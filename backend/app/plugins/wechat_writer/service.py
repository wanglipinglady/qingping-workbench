"""
微信公众号写作助手 - 服务层
提供会话、状态机、资料卡片的业务逻辑
"""
from typing import Optional, List, Tuple
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.capabilities.llm.minimax_client import minimax_client
from app.plugins.wechat_writer.models import (
    WeChatWriterSession,
    WeChatWriterMaterial,
    WeChatWriterMessage,
    WeChatWriterOutput,
)
from app.plugins.wechat_writer.schemas import (
    SessionCreateRequest,
    SessionUpdateRequest,
    WriterState,
    SessionStatus,
)
from app.plugins.wechat_writer.state_machine import (
    WeChatWriterStateMachine,
    STATE_LABELS,
)
from app.plugins.wechat_writer.experts import (
    get_expert_by_state,
    get_expert_name,
)
from app.plugins.wechat_writer.obsidian_reader import obsidian_reader
from app.plugins.wechat_writer.rag_helper import format_rag_context, build_search_queries


class WeChatWriterService:
    """微信公众号写作助手服务类"""

    # ========== 会话管理 ==========

    def create_session(self, db: Session, user_id: int, req: SessionCreateRequest) -> WeChatWriterSession:
        """创建写作会话"""
        title = req.title or req.topic[:50]
        session = WeChatWriterSession(
            user_id=user_id,
            title=title,
            topic=req.topic,
            current_state=WriterState.IDLE.value,
            status=SessionStatus.ACTIVE.value,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_session_list(
        self, db: Session, user_id: int, page: int = 1, page_size: int = 20,
        status: Optional[str] = None, keyword: Optional[str] = None,
    ) -> Tuple[List[WeChatWriterSession], int]:
        """获取会话列表"""
        query = db.query(WeChatWriterSession).filter(WeChatWriterSession.user_id == user_id)

        if status:
            query = query.filter(WeChatWriterSession.status == status)
        if keyword:
            query = query.filter(
                (WeChatWriterSession.title.like(f"%{keyword}%")) |
                (WeChatWriterSession.topic.like(f"%{keyword}%"))
            )

        total = query.count()
        items = (
            query.order_by(WeChatWriterSession.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def get_session(self, db: Session, user_id: int, session_id: int) -> WeChatWriterSession:
        """获取会话详情"""
        session = (
            db.query(WeChatWriterSession)
            .filter(
                WeChatWriterSession.id == session_id,
                WeChatWriterSession.user_id == user_id,
            )
            .first()
        )
        if not session:
            raise BusinessException("会话不存在或无权限访问")
        return session

    def update_session(
        self, db: Session, user_id: int, session_id: int, req: SessionUpdateRequest
    ) -> WeChatWriterSession:
        """更新会话"""
        session = self.get_session(db, user_id, session_id)
        update_data = req.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(session, key, value)
        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    def delete_session(self, db: Session, user_id: int, session_id: int) -> None:
        """删除会话"""
        session = self.get_session(db, user_id, session_id)
        db.delete(session)
        db.commit()

    # ========== 状态机操作 ==========

    def _get_state_machine(self, session: WeChatWriterSession) -> WeChatWriterStateMachine:
        """从会话创建状态机实例"""
        return WeChatWriterStateMachine(
            session_id=session.id,
            minimax_client=minimax_client,
            initial_state=session.current_state,
            iteration=session.iteration_count,
        )

    def _save_state_machine(
        self, db: Session, session: WeChatWriterSession, sm: WeChatWriterStateMachine
    ) -> None:
        """将状态机状态保存回数据库"""
        session.current_state = sm.current_state
        session.iteration_count = sm.iteration
        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)

    def _add_message(
        self, db: Session, session_id: int, role: str, content: str,
        expert_type: Optional[str] = None, state_label: Optional[str] = None,
        iteration: int = 1, token_usage: int = 0,
    ) -> WeChatWriterMessage:
        """添加消息记录"""
        msg = WeChatWriterMessage(
            session_id=session_id,
            role=role,
            expert_type=expert_type,
            state_label=state_label,
            iteration=iteration,
            content=content,
            token_usage=token_usage,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    def _add_output(
        self, db: Session, session_id: int, step: str, content_type: str,
        content: str, version: int = 1, feedback: Optional[str] = None,
    ) -> WeChatWriterOutput:
        """添加输出版本记录"""
        output = WeChatWriterOutput(
            session_id=session_id,
            step=step,
            content_type=content_type,
            content=content,
            version=version,
            feedback=feedback,
        )
        db.add(output)
        db.commit()
        db.refresh(output)
        return output

    def _get_session_messages(self, db: Session, session_id: int) -> List[dict]:
        """获取会话的历史消息（用于构建 LLM 上下文）"""
        messages = (
            db.query(WeChatWriterMessage)
            .filter(WeChatWriterMessage.session_id == session_id)
            .order_by(WeChatWriterMessage.created_at.asc())
            .all()
        )
        # 只返回 user/assistant 消息给 LLM
        llm_messages = []
        for msg in messages:
            if msg.role in ("user", "assistant"):
                llm_messages.append({"role": msg.role, "content": msg.content})
        return llm_messages

    def start_topic_confirm(self, db: Session, user_id: int, session_id: int) -> dict:
        """开始选题确认阶段（调用选题编辑专家）

        Returns:
            dict: {
                "from_state": 原状态,
                "to_state": 新状态,
                "expert": 专家名称,
                "response": 专家生成的回复文本,
            }
        """
        session = self.get_session(db, user_id, session_id)
        sm = self._get_state_machine(session)

        # 正向流转到 topic_confirm
        from_state, to_state = sm.next_state()

        # 记录用户的主题（作为 user 消息）
        self._add_message(
            db, session_id, "user", session.topic,
            expert_type=None, state_label=from_state, iteration=sm.iteration,
        )

        # 构建 LLM 消息（只有用户的主题）
        llm_messages = [{"role": "user", "content": session.topic}]

        # 调用选题编辑专家
        expert_type = get_expert_by_state(to_state)
        response = sm.generate_expert_response(to_state, llm_messages)

        # 记录 assistant 消息
        self._add_message(
            db, session_id, "assistant", response,
            expert_type=expert_type, state_label=to_state, iteration=sm.iteration,
        )

        # 保存输出版本
        self._add_output(
            db, session_id, step="topic", content_type="analysis",
            content=response, version=1,
        )

        # 保存状态机状态
        self._save_state_machine(db, session, sm)

        return {
            "from_state": from_state,
            "to_state": to_state,
            "expert": get_expert_name(expert_type),
            "response": response,
        }

    def generate_current_state(
        self, db: Session, user_id: int, session_id: int,
        feedback: Optional[str] = None,
    ) -> dict:
        """在当前状态触发 AI 生成（通用方法，适用于所有工作状态）

        当用户确认进入新状态后，调用此方法让对应专家开始工作。
        会自动进行 RAG 检索（research/outline/draft 状态）并注入上下文。

        Args:
            feedback: 用户的修改建议（仅在重新生成时使用）

        Returns:
            dict: {
                "from_state": 原状态,
                "to_state": 新状态,
                "expert": 专家名称,
                "response": 专家生成的回复文本,
            }
        """
        session = self.get_session(db, user_id, session_id)
        sm = self._get_state_machine(session)

        current_state = sm.current_state
        expert_type = get_expert_by_state(current_state)

        if not expert_type:
            raise BusinessException(
                f"当前状态「{STATE_LABELS.get(current_state, current_state)}」没有对应的专家，无法生成"
            )

        print(f"[WeChatWriter] 触发 AI 生成, state={current_state}, expert={expert_type}")

        # 构建 RAG 上下文（research/outline/draft 状态需要知识库资料）
        rag_context = ""
        if current_state in ("research", "outline", "draft"):
            queries = build_search_queries(session.topic, session.confirmed_topic)
            print(f"[RAG] 搜索关键词: {queries}")
            all_results = []
            for q in queries:
                try:
                    results = obsidian_reader.search(user_id, q, top_k=5)
                    all_results.extend(results)
                except Exception as e:
                    print(f"[RAG] 搜索失败 query='{q}': {e}")
            if all_results:
                rag_context = format_rag_context(all_results, max_snippets=8)
                print(f"[RAG] 检索到 {len(all_results)} 条资料，已格式化注入上下文")

        # 构建上下文
        context = {}
        if rag_context:
            context["rag_context"] = rag_context
        if feedback:
            context["is_regenerate"] = True
            context["feedback"] = feedback

        # 记录用户消息（如果有反馈）
        if feedback:
            self._add_message(
                db, session_id, "user", feedback,
                expert_type=None, state_label=current_state, iteration=sm.iteration,
            )

        # 获取历史消息
        llm_messages = self._get_session_messages(db, session_id)

        # 调用专家生成回复
        response = sm.generate_expert_response(current_state, llm_messages, context)

        # 记录 assistant 消息
        self._add_message(
            db, session_id, "assistant", response,
            expert_type=expert_type, state_label=current_state, iteration=sm.iteration,
        )

        # 保存输出版本
        step = self._state_to_step(current_state)
        content_type = self._state_to_content_type(current_state)
        latest = (
            db.query(WeChatWriterOutput)
            .filter(
                WeChatWriterOutput.session_id == session_id,
                WeChatWriterOutput.step == step,
            )
            .order_by(WeChatWriterOutput.version.desc())
            .first()
        )
        new_version = (latest.version + 1) if latest else 1
        self._add_output(
            db, session_id, step=step, content_type=content_type,
            content=response, version=new_version, feedback=feedback,
        )

        # 保存状态机状态
        self._save_state_machine(db, session, sm)

        return {
            "from_state": current_state,
            "to_state": current_state,
            "expert": get_expert_name(expert_type),
            "response": response,
        }

    def confirm_state(self, db: Session, user_id: int, session_id: int) -> dict:
        """确认当前状态，进入下一步

        如果当前是 topic_confirm，保存 confirmed_topic 并进入 research
        """
        session = self.get_session(db, user_id, session_id)
        sm = self._get_state_machine(session)

        current_state = sm.current_state

        # 如果是 topic_confirm，把上一轮输出保存为 confirmed_topic
        if current_state == "topic_confirm":
            # 找到最新的 topic 输出
            latest_output = (
                db.query(WeChatWriterOutput)
                .filter(
                    WeChatWriterOutput.session_id == session_id,
                    WeChatWriterOutput.step == "topic",
                )
                .order_by(WeChatWriterOutput.version.desc())
                .first()
            )
            if latest_output:
                session.confirmed_topic = latest_output.content
                # 标记为已确认
                latest_output.is_confirmed = 1
                db.commit()

        # 正向流转
        if sm.can_forward():
            from_state, to_state = sm.next_state()
            self._save_state_machine(db, session, sm)
            return {
                "from_state": from_state,
                "to_state": to_state,
                "message": f"已从「{STATE_LABELS.get(from_state, from_state)}」进入「{STATE_LABELS.get(to_state, to_state)}」",
            }
        else:
            return {
                "from_state": current_state,
                "to_state": current_state,
                "message": "已到达最终状态",
            }

    def regenerate(
        self, db: Session, user_id: int, session_id: int, feedback: Optional[str] = None
    ) -> dict:
        """重新生成当前步骤的输出

        Args:
            feedback: 用户填写的修改建议

        Returns:
            dict: 包含新的响应内容
        """
        session = self.get_session(db, user_id, session_id)
        sm = self._get_state_machine(session)

        current_state = sm.current_state
        expert_type = get_expert_by_state(current_state)

        if not expert_type:
            raise BusinessException(f"当前状态「{current_state}」没有对应的专家，无法重新生成")

        # 记录用户的反馈（作为 user 消息）
        user_msg = feedback or "请换一个角度重新生成"
        self._add_message(
            db, session_id, "user", user_msg,
            expert_type=None, state_label=current_state, iteration=sm.iteration,
        )

        # 获取历史消息
        llm_messages = self._get_session_messages(db, session_id)

        # 调用专家（带重新生成上下文）
        context = {"is_regenerate": True, "feedback": feedback}
        response = sm.generate_expert_response(current_state, llm_messages, context)

        # 记录 assistant 消息
        self._add_message(
            db, session_id, "assistant", response,
            expert_type=expert_type, state_label=current_state, iteration=sm.iteration,
        )

        # 计算新版本号
        step = self._state_to_step(current_state)
        latest = (
            db.query(WeChatWriterOutput)
            .filter(
                WeChatWriterOutput.session_id == session_id,
                WeChatWriterOutput.step == step,
            )
            .order_by(WeChatWriterOutput.version.desc())
            .first()
        )
        new_version = (latest.version + 1) if latest else 1

        # 保存新输出版本
        content_type = self._state_to_content_type(current_state)
        self._add_output(
            db, session_id, step=step, content_type=content_type,
            content=response, version=new_version, feedback=feedback,
        )

        return {
            "state": current_state,
            "expert": get_expert_name(expert_type),
            "version": new_version,
            "feedback": feedback,
            "response": response,
        }

    def rollback(self, db: Session, user_id: int, session_id: int, target_state: str, reason: str = "") -> dict:
        """回退到指定状态"""
        session = self.get_session(db, user_id, session_id)
        sm = self._get_state_machine(session)

        from_state, to_state = sm.rollback_to(target_state, reason)
        self._save_state_machine(db, session, sm)

        return {
            "from_state": from_state,
            "to_state": to_state,
            "reason": reason,
            "message": f"已从「{STATE_LABELS.get(from_state, from_state)}」回退到「{STATE_LABELS.get(to_state, to_state)}」",
        }

    # ========== 辅助方法 ==========

    @staticmethod
    def _state_to_step(state: str) -> str:
        """状态到输出 step 的映射"""
        mapping = {
            "topic_confirm": "topic",
            "research": "research",
            "outline": "outline",
            "draft": "draft",
            "polish": "polish",
        }
        return mapping.get(state, state)

    @staticmethod
    def _state_to_content_type(state: str) -> str:
        """状态到输出 content_type 的映射"""
        mapping = {
            "topic_confirm": "analysis",
            "research": "materials",
            "outline": "outline",
            "draft": "draft",
            "polish": "final",
        }
        return mapping.get(state, state)

    # ========== 资料卡片（占位，T7 完善） ==========

    def get_materials(
        self, db: Session, user_id: int, session_id: int,
        source_type: Optional[str] = None, is_useful: Optional[bool] = None,
    ) -> List[WeChatWriterMaterial]:
        """获取资料卡片列表"""
        session = self.get_session(db, user_id, session_id)
        query = db.query(WeChatWriterMaterial).filter(WeChatWriterMaterial.session_id == session.id)
        if source_type:
            query = query.filter(WeChatWriterMaterial.source_type == source_type)
        if is_useful is not None:
            query = query.filter(WeChatWriterMaterial.is_useful == (1 if is_useful else 0))
        return query.order_by(WeChatWriterMaterial.created_at.desc()).all()

    # ========== 输出版本（占位，T10 完善） ==========

    def get_outputs(
        self, db: Session, user_id: int, session_id: int, step: Optional[str] = None
    ) -> List[WeChatWriterOutput]:
        """获取输出版本列表"""
        session = self.get_session(db, user_id, session_id)
        query = db.query(WeChatWriterOutput).filter(WeChatWriterOutput.session_id == session.id)
        if step:
            query = query.filter(WeChatWriterOutput.step == step)
        return query.order_by(WeChatWriterOutput.step, WeChatWriterOutput.version).all()


# 全局服务实例
wechat_writer_service = WeChatWriterService()
