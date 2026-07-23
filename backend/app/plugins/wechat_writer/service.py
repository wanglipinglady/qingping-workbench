"""
微信公众号写作助手 - 服务层
提供会话、状态机、资料卡片、写作模板的业务逻辑
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
    WeChatWriterTemplate,
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

    # 状态顺序定义（用于消息过滤）
    _STATE_ORDER = [
        "idle", "topic_confirm", "research", "outline", "draft", "polish", "done"
    ]

    def _get_state_order_index(self, state: str) -> int:
        """获取状态在流程中的顺序索引"""
        try:
            return self._STATE_ORDER.index(state)
        except ValueError:
            return 0

    def _get_session_messages(
        self, db: Session, session_id: int,
        current_state: Optional[str] = None,
    ) -> List[dict]:
        """获取会话的历史消息（用于构建 LLM 上下文）

        关键设计：只保留当前阶段的消息 + 之前阶段的 user 反馈消息。
        之前阶段的 assistant 长输出（选题分析、资料卡片、大纲、初稿等）
        已通过 `_build_stage_context` 注入为结构化 system 消息，不需要
        在历史消息中重复，否则会导致：
        1. 上下文冗余，token 浪费
        2. AI 注意力被之前阶段的长输出淹没，忘记当前角色
        3. 每个阶段输出趋同（看起来像上一阶段的延续）

        Args:
            session_id: 会话 ID
            current_state: 当前状态，用于过滤消息
                          如果为 None，则返回所有 user/assistant 消息（向后兼容）
        """
        messages = (
            db.query(WeChatWriterMessage)
            .filter(WeChatWriterMessage.session_id == session_id)
            .order_by(WeChatWriterMessage.created_at.asc())
            .all()
        )

        # 计算当前状态在流程中的位置
        current_idx = self._get_state_order_index(current_state) if current_state else len(self._STATE_ORDER) - 1

        llm_messages = []
        for msg in messages:
            if msg.role not in ("user", "assistant"):
                continue

            # 无状态标签的消息（兼容性处理）
            if msg.state_label is None:
                llm_messages.append({"role": msg.role, "content": msg.content})
                continue

            msg_state_idx = self._get_state_order_index(msg.state_label)

            # 跳过未来状态的消息（防止回退后旧消息污染）
            if msg_state_idx > current_idx:
                continue

            if msg_state_idx < current_idx:
                # 之前阶段的消息：只保留 user 消息（用户的反馈/修改建议）
                # 之前阶段的 assistant 长输出已通过 _build_stage_context 注入，不再重复
                if msg.role == "user":
                    llm_messages.append({
                        "role": "user",
                        "content": f"[阶段：{msg.state_label}] {msg.content}",
                    })
            else:
                # 当前阶段的消息：user 和 assistant 都保留
                # 添加阶段标签帮助 AI 理解上下文
                label_prefix = f"[阶段：{msg.state_label}] " if msg.state_label else ""
                llm_messages.append({
                    "role": msg.role,
                    "content": f"{label_prefix}{msg.content}",
                })

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
            rag_context = self._build_rag_context(
                user_id, session.topic, session.confirmed_topic
            )

        # 构建上下文
        context = {}
        if sm.iteration > 1:
            context["is_rollback"] = True
            context["from_state"] = current_state
            context["reason"] = "用户回退后重新生成"
        if rag_context:
            context["rag_context"] = rag_context
        if feedback:
            context["is_regenerate"] = True
            context["feedback"] = feedback

        # 注入前置阶段内容（选题确认单/资料卡片/大纲/初稿）
        stage_context = self._build_stage_context(db, session_id, current_state)
        context.update(stage_context)
        if stage_context:
            print(f"[WeChatWriter] 注入阶段上下文: {list(stage_context.keys())}")

        # 记录用户消息（如果有反馈）
        if feedback:
            self._add_message(
                db, session_id, "user", feedback,
                expert_type=None, state_label=current_state, iteration=sm.iteration,
            )

        # 获取历史消息（只包含当前状态及之前状态的消息，防止回退后旧消息污染）
        llm_messages = self._get_session_messages(db, session_id, current_state=current_state)

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

    async def generate_current_state_stream(
        self, db: Session, user_id: int, session_id: int,
        feedback: Optional[str] = None,
    ):
        """
        在当前状态触发 AI 生成（流式版本，SSE 推送）

        Returns:
            AsyncGenerator[str, None]: 逐块推送的 JSON 字符串
            格式: {"type": "chunk", "content": "..."} / {"type": "done", "full_content": "..."}
        """
        import json

        session = self.get_session(db, user_id, session_id)
        sm = self._get_state_machine(session)

        current_state = sm.current_state
        expert_type = get_expert_by_state(current_state)

        if not expert_type:
            yield json.dumps({"type": "error", "message": f"当前状态「{current_state}」没有对应的专家"})
            return

        print(f"[WeChatWriter] 流式 AI 生成, state={current_state}, expert={expert_type}")

        # 构建 RAG 上下文
        rag_context = ""
        if current_state in ("research", "outline", "draft"):
            rag_context = self._build_rag_context(
                user_id, session.topic, session.confirmed_topic
            )

        context = {}
        if sm.iteration > 1:
            context["is_rollback"] = True
            context["from_state"] = current_state
            context["reason"] = "用户回退后重新生成"
        if rag_context:
            context["rag_context"] = rag_context
        if feedback:
            context["is_regenerate"] = True
            context["feedback"] = feedback

        # 注入前置阶段内容（选题确认单/资料卡片/大纲/初稿）
        stage_context = self._build_stage_context(db, session_id, current_state)
        context.update(stage_context)
        if stage_context:
            print(f"[WeChatWriter] 注入阶段上下文: {list(stage_context.keys())}")

        # 记录用户消息
        if feedback:
            self._add_message(
                db, session_id, "user", feedback,
                expert_type=None, state_label=current_state, iteration=sm.iteration,
            )

        # 获取历史消息（只包含当前状态及之前状态的消息，防止回退后旧消息污染）
        llm_messages = self._get_session_messages(db, session_id, current_state=current_state)

        # 流式调用专家
        full_content_parts = []
        async for chunk in sm.generate_expert_response_stream(current_state, llm_messages, context):
            if chunk and len(chunk.strip()) > 0:
                full_content_parts.append(chunk)
                yield json.dumps({"type": "chunk", "content": chunk}, ensure_ascii=False)

        # 合并完整内容
        full_response = "".join(full_content_parts)

        # 记录 assistant 消息
        self._add_message(
            db, session_id, "assistant", full_response,
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
            content=full_response, version=new_version, feedback=feedback,
        )

        # 保存状态机状态
        self._save_state_machine(db, session, sm)

        # 推送完成事件
        yield json.dumps({
            "type": "done",
            "full_content": full_response,
            "state": current_state,
            "expert": get_expert_name(expert_type),
        }, ensure_ascii=False)

    def confirm_state(self, db: Session, user_id: int, session_id: int) -> dict:
        """确认当前状态，进入下一步

        如果当前是 topic_confirm，保存 confirmed_topic 并进入 research。
        状态切换后自动触发下一状态的 AI 生成（与 start_topic_confirm 行为一致）。
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

            # 切换状态后自动触发下一状态的 AI 生成
            expert_type = get_expert_by_state(to_state)
            response = ""

            if expert_type:
                print(f"[WeChatWriter] confirm 后自动触发 AI 生成, state={to_state}, expert={expert_type}")

                # 构建 RAG 上下文（research/outline/draft 状态需要知识库资料）
                rag_context = ""
                if to_state in ("research", "outline", "draft"):
                    rag_context = self._build_rag_context(
                        user_id, session.topic, session.confirmed_topic
                    )

                # 构建上下文
                context = {}

                # 检测是否是回退后的重新生成（iteration > 1 说明之前有过回退）
                if sm.iteration > 1:
                    context["is_rollback"] = True
                    context["from_state"] = from_state
                    context["reason"] = "用户回退后重新进入此状态"
                    print(f"[WeChatWriter] 检测到回退后的重新生成, iteration={sm.iteration}")

                if rag_context:
                    context["rag_context"] = rag_context

                # 注入前置阶段内容（选题确认单/资料卡片/大纲/初稿）
                stage_context = self._build_stage_context(db, session_id, to_state)
                context.update(stage_context)
                if stage_context:
                    print(f"[WeChatWriter] 注入阶段上下文: {list(stage_context.keys())}")

                # 获取历史消息（只包含目标状态及之前状态的消息，防止回退后旧消息污染）
                llm_messages = self._get_session_messages(db, session_id, current_state=to_state)

                # 调用专家生成回复
                try:
                    response = sm.generate_expert_response(to_state, llm_messages, context)
                except Exception as e:
                    print(f"[WeChatWriter] AI 生成失败: {e}")
                    response = f"（AI 生成失败：{e}）"

                # 记录 assistant 消息
                self._add_message(
                    db, session_id, "assistant", response,
                    expert_type=expert_type, state_label=to_state, iteration=sm.iteration,
                )

                # 保存输出版本
                step = self._state_to_step(to_state)
                content_type = self._state_to_content_type(to_state)
                self._add_output(
                    db, session_id, step=step, content_type=content_type,
                    content=response, version=1,
                )

                # 保存状态机状态
                self._save_state_machine(db, session, sm)

                return {
                    "from_state": from_state,
                    "to_state": to_state,
                    "expert": get_expert_name(expert_type),
                    "response": response,
                    "message": f"已从「{STATE_LABELS.get(from_state, from_state)}」进入「{STATE_LABELS.get(to_state, to_state)}」，{get_expert_name(expert_type)}已开始工作",
                }
            else:
                # done 状态没有专家
                return {
                    "from_state": from_state,
                    "to_state": to_state,
                    "response": "",
                    "message": f"已从「{STATE_LABELS.get(from_state, from_state)}」进入「{STATE_LABELS.get(to_state, to_state)}」",
                }
        else:
            return {
                "from_state": current_state,
                "to_state": current_state,
                "response": "",
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

        # 获取历史消息（只包含当前状态及之前状态的消息，防止回退后旧消息污染）
        llm_messages = self._get_session_messages(db, session_id, current_state=current_state)

        # 调用专家（带重新生成上下文）
        context = {"is_regenerate": True, "feedback": feedback}

        # 注入前置阶段内容（选题确认单/资料卡片/大纲/初稿）
        stage_context = self._build_stage_context(db, session_id, current_state)
        context.update(stage_context)

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
        """回退到指定状态

        回退后：
        1. 状态机状态更新为 target_state，iteration +1
        2. 添加一条系统消息记录回退事件
        3. 后续 confirm/generate 时只使用 target_state 及之前状态的消息
        """
        session = self.get_session(db, user_id, session_id)
        sm = self._get_state_machine(session)

        from_state, to_state = sm.rollback_to(target_state, reason)
        self._save_state_machine(db, session, sm)

        # 记录回退事件为系统消息（state_label 设为目标状态，便于消息过滤）
        rollback_msg = f"[系统] 用户从「{STATE_LABELS.get(from_state, from_state)}」回退到「{STATE_LABELS.get(to_state, to_state)}」"
        if reason:
            rollback_msg += f"，原因：{reason}"
        self._add_message(
            db, session_id, "user", rollback_msg,
            expert_type=None, state_label=to_state, iteration=sm.iteration,
        )

        return {
            "from_state": from_state,
            "to_state": to_state,
            "reason": reason,
            "message": f"已从「{STATE_LABELS.get(from_state, from_state)}」回退到「{STATE_LABELS.get(to_state, to_state)}」",
        }

    # ========== 辅助方法 ==========

    def _build_rag_context(self, user_id: int, topic: str,
                            confirmed_topic: Optional[str] = None) -> str:
        """构建 RAG 上下文（共用方法）

        1. 先从本地 Obsidian 知识库搜索资料
        2. 如果本地知识库找不到资料，使用 fallback 上下文，
           告诉 AI 基于通用知识和网络公开信息输出资料卡片

        Returns:
            格式化后的 RAG 上下文字符串，空字符串表示无需注入
        """
        queries = build_search_queries(topic, confirmed_topic)
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
            print(f"[RAG] 检索到 {len(all_results)} 条本地资料，已格式化注入上下文")
            return rag_context

        # 本地知识库无资料时，使用 fallback 上下文，告诉 AI 用通用知识和网络资料
        print(f"[RAG] 本地知识库未找到相关资料，使用通用知识/网络资料 fallback")
        fallback_context = f"""
============================================================
【本地知识库检索结果】
未在用户的 Obsidian 知识库中找到与主题相关的笔记。

【资料来源说明】
由于本地知识库无相关资料，请基于你的通用知识和对互联网公开信息的了解，
输出 3-5 条结构化的资料卡片。这些资料卡片可以：
1. 引用该领域公认的常识、数据和最佳实践
2. 引用公开可查的行业报告、统计数据（标注大致来源）
3. 基于该主题的常见论点和案例进行合理推演
4. 标注可信度时适当降低（本地未验证的资料不超过 3 星）

【注意】
- 不要因为本地无资料就向用户提问或要求补充信息
- 直接基于你的知识输出资料卡片，确保内容有价值
- 如果某些数据不确定，可以用"据公开报道"、"行业普遍认为"等措辞
============================================================
"""
        return fallback_context

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
        """状态到输出内容类型的映射"""
        mapping = {
            "topic_confirm": "analysis",
            "research": "materials",
            "outline": "outline",
            "draft": "draft",
            "polish": "final",
        }
        return mapping.get(state, state)

    def _get_latest_output(self, db: Session, session_id: int, step: str) -> Optional[str]:
        """获取指定步骤最新的输出内容"""
        output = (
            db.query(WeChatWriterOutput)
            .filter(
                WeChatWriterOutput.session_id == session_id,
                WeChatWriterOutput.step == step,
            )
            .order_by(WeChatWriterOutput.version.desc())
            .first()
        )
        return output.content if output else None

    def _get_session_materials_text(self, db: Session, session_id: int) -> str:
        """获取会话的资料卡片文本（用于上下文注入）"""
        materials = (
            db.query(WeChatWriterMaterial)
            .filter(WeChatWriterMaterial.session_id == session_id)
            .order_by(WeChatWriterMaterial.created_at.asc())
            .all()
        )
        if not materials:
            return ""
        lines = []
        for i, m in enumerate(materials, 1):
            credibility = "⭐" * (m.credibility_score or 3)
            lines.append(f"【资料卡片 #{i}】")
            if m.title:
                lines.append(f"标题：{m.title}")
            if m.source_type:
                lines.append(f"来源：{m.source_type}")
            lines.append(f"可信度：{credibility}")
            if m.core_idea:
                lines.append(f"核心观点：{m.core_idea}")
            if m.useful_snippets:
                lines.append(f"可用片段：{m.useful_snippets}")
            if m.suggested_usage:
                lines.append(f"推荐使用：{m.suggested_usage}")
            if m.tags:
                lines.append(f"标签：{m.tags}")
            lines.append("")
        return "\n".join(lines)

    def _build_stage_context(self, db: Session, session_id: int, state: str) -> dict:
        """构建指定阶段的前置内容上下文

        每个阶段需要的前置内容：
        - research: 选题确认单
        - outline:  选题确认单 + 资料卡片
        - draft:    选题确认单 + 资料卡片 + 大纲
        - polish:   选题确认单 + 资料卡片 + 大纲 + 初稿
        """
        context = {}

        # 选题确认单（所有阶段都需要）
        confirmed_topic = self._get_latest_output(db, session_id, "topic")
        if confirmed_topic:
            context["topic_analysis"] = confirmed_topic

        if state in ("outline", "draft", "polish"):
            # 资料卡片
            materials_text = self._get_session_materials_text(db, session_id)
            if materials_text:
                context["materials"] = materials_text

        if state in ("draft", "polish"):
            # 大纲
            outline = self._get_latest_output(db, session_id, "outline")
            if outline:
                context["outline"] = outline

        if state == "polish":
            # 初稿
            draft = self._get_latest_output(db, session_id, "draft")
            if draft:
                context["draft_content"] = draft

        return context

    def export_article(self, db: Session, user_id: int, session_id: int) -> tuple:
        """导出文章内容

        优先使用润色稿（polish），没有则使用初稿（draft）

        Returns:
            (content, title): 文章内容和标题
        """
        session = self.get_session(db, user_id, session_id)

        # 优先获取润色稿
        polish_output = self._get_latest_output(db, session_id, "polish")
        if polish_output:
            content = polish_output
        else:
            # 没有润色稿则使用初稿
            draft_output = self._get_latest_output(db, session_id, "draft")
            content = draft_output or ""

        if not content:
            return ("", "")

        # 提取标题（第一个 # 开头的行）
        import re
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else session.title or "article"
        # 清理文件名中的非法字符
        title = re.sub(r'[\\/:*?"<>|]', '_', title)

        return (content, title)

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

    def create_material(
        self, db: Session, user_id: int, session_id: int,
        source_type: str, title: str,
        url: Optional[str] = None, core_idea: Optional[str] = None,
        useful_snippets: Optional[str] = None, credibility_score: int = 3,
        suggested_usage: Optional[str] = None, tags: Optional[str] = None,
    ) -> WeChatWriterMaterial:
        """创建资料卡片"""
        session = self.get_session(db, user_id, session_id)
        material = WeChatWriterMaterial(
            session_id=session.id,
            source_type=source_type,
            title=title,
            url=url,
            core_idea=core_idea,
            useful_snippets=useful_snippets,
            credibility_score=credibility_score,
            suggested_usage=suggested_usage,
            is_useful=1,
            tags=tags,
        )
        db.add(material)
        db.commit()
        db.refresh(material)
        print(f"[Material] 创建资料卡片: id={material.id}, title={title}")
        return material

    def update_material(
        self, db: Session, user_id: int, material_id: int,
        is_useful: Optional[bool] = None, tags: Optional[str] = None,
        credibility_score: Optional[int] = None,
    ) -> WeChatWriterMaterial:
        """更新资料卡片"""
        material = (
            db.query(WeChatWriterMaterial)
            .join(WeChatWriterSession, WeChatWriterMaterial.session_id == WeChatWriterSession.id)
            .filter(
                WeChatWriterMaterial.id == material_id,
                WeChatWriterSession.user_id == user_id,
            )
            .first()
        )
        if not material:
            raise BusinessException("资料卡片不存在")

        if is_useful is not None:
            material.is_useful = 1 if is_useful else 0
        if tags is not None:
            material.tags = tags
        if credibility_score is not None:
            material.credibility_score = max(1, min(5, credibility_score))

        db.commit()
        db.refresh(material)
        return material

    def delete_material(self, db: Session, user_id: int, material_id: int) -> None:
        """删除资料卡片"""
        material = (
            db.query(WeChatWriterMaterial)
            .join(WeChatWriterSession, WeChatWriterMaterial.session_id == WeChatWriterSession.id)
            .filter(
                WeChatWriterMaterial.id == material_id,
                WeChatWriterSession.user_id == user_id,
            )
            .first()
        )
        if not material:
            raise BusinessException("资料卡片不存在")
        db.delete(material)
        db.commit()
        print(f"[Material] 删除资料卡片: id={material_id}")

    def parse_and_save_materials(
        self, db: Session, user_id: int, session_id: int, ai_output: str,
    ) -> List[WeChatWriterMaterial]:
        """
        从研究员的 AI 输出中解析资料卡片并批量保存

        研究员的输出格式包含多个资料卡片，每个卡片有：
        标题、来源、可信度、核心观点、可用片段、推荐使用位置
        """
        import re

        if not ai_output or len(ai_output.strip()) == 0:
            return []

        saved_materials = []

        # 尝试从 Markdown 中解析资料卡片
        # 匹配模式：以 "##" 或 "###" 或 "---" 分隔的卡片，或 "资料" 开头的块
        card_blocks = re.split(r"\n---+\n|\n#{2,3}\s*资料", ai_output, flags=re.IGNORECASE)

        for block in card_blocks:
            block = block.strip()
            if len(block) < 20:
                continue

            # 提取字段
            title_match = re.search(r"(?:标题|资料标题|📄)\s*[：:]\s*(.+?)(?:\n|$)", block)
            source_match = re.search(r"(?:来源|出处|📁|url|路径)\s*[：:]\s*(.+?)(?:\n|$)", block, re.IGNORECASE)
            credibility_match = re.search(r"(?:可信度|评分|🔍)\s*[：:]\s*(\d+)", block)
            core_match = re.search(r"(?:核心观点|内容摘要|📝|摘要)\s*[：:]\s*(.+?)(?:\n\s*\n|$)", block, re.DOTALL)
            snippet_match = re.search(r"(?:可用片段|关键内容|内容)\s*[：:]\s*(.+?)(?:\n\s*\n|$)", block, re.DOTALL)
            usage_match = re.search(r"(?:推荐使用|使用场景|建议)\s*[：:]\s*(.+?)(?:\n|$)", block)

            title = (title_match.group(1).strip() if title_match else None)
            if not title:
                # 尝试用第一行作为标题
                first_line = block.split("\n")[0].strip()
                if first_line and len(first_line) < 200:
                    title = re.sub(r"^[#\-\s]+", "", first_line)[:100]

            if not title or len(title) < 2:
                continue

            source_type = "web"
            url = source_match.group(1).strip() if source_match else None
            if url and ("obsidian" in url.lower() or ".md" in url.lower() or "/" in url):
                source_type = "obsidian"

            credibility = 3
            if credibility_match:
                try:
                    credibility = max(1, min(5, int(credibility_match.group(1))))
                except ValueError:
                    pass

            core_idea = core_match.group(1).strip() if core_match else None
            useful_snippets = snippet_match.group(1).strip() if snippet_match else None
            suggested_usage = usage_match.group(1).strip() if usage_match else None

            try:
                material = self.create_material(
                    db, user_id, session_id,
                    source_type=source_type,
                    title=title,
                    url=url,
                    core_idea=core_idea,
                    useful_snippets=useful_snippets,
                    credibility_score=credibility,
                    suggested_usage=suggested_usage,
                )
                saved_materials.append(material)
            except Exception as e:
                print(f"[Material] 解析保存失败: {e}, title={title}")

        print(f"[Material] 从 AI 输出解析并保存了 {len(saved_materials)} 条资料卡片")
        return saved_materials

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

    # ========== 写作模板 ==========

    def list_templates(
        self, db: Session, user_id: int,
        category: Optional[str] = None,
        include_system: bool = True,
    ) -> List[WeChatWriterTemplate]:
        """获取模板列表（系统预设 + 当前用户的私有模板）"""
        query = db.query(WeChatWriterTemplate).filter(
            (WeChatWriterTemplate.user_id == user_id) |
            (WeChatWriterTemplate.is_system == 1) |
            (WeChatWriterTemplate.is_public == 1)
        )
        if category:
            query = query.filter(WeChatWriterTemplate.category == category)
        return query.order_by(
            WeChatWriterTemplate.sort_order,
            WeChatWriterTemplate.use_count.desc(),
            WeChatWriterTemplate.created_at.desc(),
        ).all()

    def get_template(self, db: Session, user_id: int, template_id: int) -> Optional[WeChatWriterTemplate]:
        """获取单个模板（带权限校验）"""
        template = db.query(WeChatWriterTemplate).filter(
            WeChatWriterTemplate.id == template_id
        ).first()
        if not template:
            return None
        # 权限校验：系统模板、公开模板、自己的模板 可以访问
        if template.is_system or template.is_public or template.user_id == user_id:
            return template
        return None

    def create_template(
        self, db: Session, user_id: int,
        name: str, description: Optional[str] = None,
        category: str = "custom", icon: Optional[str] = "📝",
        topic_prompt: Optional[str] = None,
        research_prompt: Optional[str] = None,
        outline_prompt: Optional[str] = None,
        writer_prompt: Optional[str] = None,
        suggested_topics: Optional[str] = None,
        default_style: Optional[str] = None,
        default_audience: Optional[str] = None,
        is_public: bool = False,
    ) -> WeChatWriterTemplate:
        """创建自定义模板"""
        template = WeChatWriterTemplate(
            name=name,
            description=description,
            category=category,
            icon=icon or "📝",
            topic_prompt=topic_prompt,
            research_prompt=research_prompt,
            outline_prompt=outline_prompt,
            writer_prompt=writer_prompt,
            suggested_topics=suggested_topics,
            default_style=default_style,
            default_audience=default_audience,
            user_id=user_id,
            is_public=1 if is_public else 0,
            is_system=0,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        print(f"[Template] 创建模板: id={template.id}, name={name}")
        return template

    def update_template(
        self, db: Session, user_id: int, template_id: int,
        **kwargs,
    ) -> WeChatWriterTemplate:
        """更新模板（只能更新自己的模板）"""
        template = db.query(WeChatWriterTemplate).filter(
            WeChatWriterTemplate.id == template_id,
            WeChatWriterTemplate.user_id == user_id,
        ).first()
        if not template:
            raise BusinessException("模板不存在或无权限修改")

        for key, value in kwargs.items():
            if value is not None and hasattr(template, key):
                if key == "is_public":
                    setattr(template, key, 1 if value else 0)
                else:
                    setattr(template, key, value)

        db.commit()
        db.refresh(template)
        return template

    def delete_template(self, db: Session, user_id: int, template_id: int) -> None:
        """删除模板（只能删除自己的模板）"""
        template = db.query(WeChatWriterTemplate).filter(
            WeChatWriterTemplate.id == template_id,
            WeChatWriterTemplate.user_id == user_id,
        ).first()
        if not template:
            raise BusinessException("模板不存在或无权限删除")
        db.delete(template)
        db.commit()
        print(f"[Template] 删除模板: id={template_id}")

    def apply_template(
        self, db: Session, user_id: int,
        template_id: int, topic: Optional[str] = None,
    ) -> WeChatWriterSession:
        """
        从模板创建会话

        - 自动增加模板使用次数
        - 如果模板有推荐主题且用户未指定，使用推荐主题
        - 后续 Prompt 注入逻辑在状态机中处理
        """
        template = self.get_template(db, user_id, template_id)
        if not template:
            raise BusinessException("模板不存在或无权限使用")

        # 确定主题
        final_topic = topic
        if not final_topic and template.suggested_topics:
            import json
            try:
                topics = json.loads(template.suggested_topics)
                if topics and isinstance(topics, list) and len(topics) > 0:
                    final_topic = topics[0]
            except (json.JSONDecodeError, TypeError):
                pass

        if not final_topic:
            final_topic = f"使用「{template.name}」模板写作"

        # 创建会话（带模板标记）
        from app.plugins.wechat_writer.schemas import SessionCreateRequest
        session = self.create_session(db, user_id, SessionCreateRequest(topic=final_topic))

        # 增加模板使用次数
        template.use_count = (template.use_count or 0) + 1
        db.commit()

        print(f"[Template] 从模板创建会话: template_id={template_id}, session_id={session.id}")
        return session


# 全局服务实例
wechat_writer_service = WeChatWriterService()
