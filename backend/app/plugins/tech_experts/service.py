"""技术专家组业务逻辑层

封装状态机流转、消息管理、MiniMax 调用等核心业务逻辑，
供 API 路由层调用。
"""

import json
from typing import List, Dict, Optional, Tuple, AsyncIterator
from sqlalchemy.orm import Session

from app.capabilities.llm.minimax_client import minimax_client, MiniMaxClient
from app.plugins.tech_experts.models import (
    ExpertSession,
    ExpertMessage,
    ExpertStateTransition,
)
from app.plugins.tech_experts.state_machine import (
    TechExpertStateMachine,
    TechExpertState,
    STATE_LABELS,
)
from app.plugins.tech_experts.experts import (
    ExpertType,
    get_expert_config,
    get_expert_name,
    get_expert_by_state,
    get_all_experts,
    EXPERT_CONFIG,
)
from app.plugins.tech_experts.schemas import SSEEvent


class TechExpertService:
    """技术专家组服务类

    封装所有业务逻辑，包括会话管理、消息管理、状态机控制、
    专家调用等。routes 层通过此类与业务逻辑交互。
    """

    def __init__(self, db: Session):
        """
        Args:
            db: 数据库会话
        """
        self.db = db
        self._minimax_client: Optional[MiniMaxClient] = None

    @property
    def minimax_client(self) -> MiniMaxClient:
        """惰性加载 MiniMax 客户端"""
        if self._minimax_client is None:
            self._minimax_client = minimax_client
        return self._minimax_client

    # ==================================================================
    # 会话管理
    # ==================================================================

    def list_sessions(self, user_id: int) -> List[ExpertSession]:
        """获取用户的会话列表（按更新时间倒序）"""
        return (
            self.db.query(ExpertSession)
            .filter(ExpertSession.user_id == user_id)
            .order_by(ExpertSession.updated_at.desc())
            .all()
        )

    def create_session(
        self,
        user_id: int,
        title: str = "新的技术协作",
        initial_message: Optional[str] = None,
    ) -> ExpertSession:
        """创建新的专家会话

        Args:
            user_id: 用户 ID
            title: 会话标题
            initial_message: 初始需求消息（可选）

        Returns:
            创建的会话对象
        """
        session = ExpertSession(
            user_id=user_id,
            title=title,
            current_state=TechExpertState.IDLE.value,
            iteration_count=0,
            max_iterations=10,
            status="active",
            total_tokens=0,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        # 如果有初始消息，保存用户消息
        if initial_message:
            self.add_message(
                session_id=session.id,
                role="user",
                content=initial_message,
                expert_type=None,
                state_label=TechExpertState.IDLE.value,
                iteration=0,
            )

        return session

    def get_session(self, session_id: int, user_id: int) -> Optional[ExpertSession]:
        """获取指定会话（验证用户权限）"""
        return (
            self.db.query(ExpertSession)
            .filter(
                ExpertSession.id == session_id,
                ExpertSession.user_id == user_id,
            )
            .first()
        )

    def delete_session(self, session_id: int, user_id: int) -> bool:
        """删除会话及其所有消息和状态转移记录"""
        session = self.get_session(session_id, user_id)
        if not session:
            return False

        # 删除关联消息
        self.db.query(ExpertMessage).filter(
            ExpertMessage.session_id == session_id
        ).delete()

        # 删除状态转移记录
        self.db.query(ExpertStateTransition).filter(
            ExpertStateTransition.session_id == session_id
        ).delete()

        # 删除会话
        self.db.delete(session)
        self.db.commit()
        return True

    def update_session_state(
        self,
        session: ExpertSession,
        new_state: str,
        iteration: Optional[int] = None,
    ):
        """更新会话的状态和迭代信息"""
        session.current_state = new_state
        if iteration is not None:
            session.iteration_count = iteration
        self.db.commit()
        self.db.refresh(session)

    def increment_tokens(self, session: ExpertSession, tokens: int):
        """增加会话的 token 消耗统计"""
        session.total_tokens += tokens
        self.db.commit()

    # ==================================================================
    # 消息管理
    # ==================================================================

    def get_messages(self, session_id: int, user_id: int) -> List[ExpertMessage]:
        """获取会话的所有消息（按时间正序）"""
        session = self.get_session(session_id, user_id)
        if not session:
            return []
        return (
            self.db.query(ExpertMessage)
            .filter(ExpertMessage.session_id == session_id)
            .order_by(ExpertMessage.created_at.asc())
            .all()
        )

    def add_message(
        self,
        session_id: int,
        role: str,
        content: str,
        expert_type: Optional[str] = None,
        state_label: Optional[str] = None,
        iteration: int = 0,
        token_usage: int = 0,
    ) -> ExpertMessage:
        """添加一条消息

        Args:
            session_id: 会话 ID
            role: 消息角色 (user/assistant/system)
            content: 消息内容
            expert_type: 专家类型 (architect/coder/reviewer/tester)
            state_label: 所属状态节点
            iteration: 迭代轮次
            token_usage: token 消耗

        Returns:
            创建的消息对象
        """
        msg = ExpertMessage(
            session_id=session_id,
            role=role,
            expert_type=expert_type,
            state_label=state_label,
            iteration=iteration,
            content=content,
            token_usage=token_usage,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def build_context_messages(
        self,
        session: ExpertSession,
        current_state: str,
    ) -> List[Dict[str, str]]:
        """构建当前状态的上下文消息列表

        从数据库中提取相关历史消息，整理为 LLM 可识别的格式。
        策略：保留最近的关键交互，避免上下文过长。

        Args:
            session: 会话对象
            current_state: 当前状态

        Returns:
            消息列表，格式 [{"role": "user", "content": "..."}]
        """
        messages_db = (
            self.db.query(ExpertMessage)
            .filter(ExpertMessage.session_id == session.id)
            .order_by(ExpertMessage.created_at.asc())
            .all()
        )

        result = []
        for msg in messages_db:
            # 跳过 system 消息（System Prompt 会在状态机中单独添加）
            if msg.role == "system":
                continue

            role = msg.role
            # 为 assistant 消息添加专家标识前缀
            if role == "assistant" and msg.expert_type:
                expert_name = get_expert_name(msg.expert_type)
                # 直接以 assistant 角色发送，内容中包含专家身份
                content = f"【{expert_name}】\n{msg.content}"
            else:
                content = msg.content

            result.append({"role": role, "content": content})

        # 限制上下文长度（最多保留最近 30 条消息）
        if len(result) > 30:
            # 保留第一条（通常是初始需求）+ 最近 29 条
            result = [result[0]] + result[-29:]

        return result

    # ==================================================================
    # 状态转移记录
    # ==================================================================

    def record_transition(
        self,
        session_id: int,
        from_state: str,
        to_state: str,
        transition_type: str,
        reason: str = "",
    ) -> ExpertStateTransition:
        """记录一次状态转移

        Args:
            session_id: 会话 ID
            from_state: 源状态
            to_state: 目标状态
            transition_type: 转移类型 (auto/human_confirm/human_rollback/human_switch)
            reason: 转移原因

        Returns:
            转移记录对象
        """
        transition = ExpertStateTransition(
            session_id=session_id,
            from_state=from_state,
            to_state=to_state,
            transition_type=transition_type,
            reason=reason,
        )
        self.db.add(transition)
        self.db.commit()
        self.db.refresh(transition)
        return transition

    def get_transitions(self, session_id: int, user_id: int) -> List[ExpertStateTransition]:
        """获取会话的状态转移历史"""
        session = self.get_session(session_id, user_id)
        if not session:
            return []
        return (
            self.db.query(ExpertStateTransition)
            .filter(ExpertStateTransition.session_id == session_id)
            .order_by(ExpertStateTransition.created_at.asc())
            .all()
        )

    # ==================================================================
    # 状态机操作
    # ==================================================================

    def create_state_machine(self, session: ExpertSession) -> TechExpertStateMachine:
        """为会话创建状态机实例

        Args:
            session: 会话对象

        Returns:
            状态机实例
        """
        return TechExpertStateMachine(
            session_id=session.id,
            minimax_client=self.minimax_client,
            initial_state=session.current_state,
            iteration=session.iteration_count,
        )

    def get_state_info(self, session: ExpertSession) -> Dict:
        """获取当前状态的详细信息

        Args:
            session: 会话对象

        Returns:
            状态信息字典
        """
        state_machine = self.create_state_machine(session)
        current_state = state_machine.get_state()
        expert_type = state_machine.get_state_expert()
        expert_config = get_expert_config(expert_type) if expert_type else None

        return {
            "current_state": current_state,
            "current_state_label": STATE_LABELS.get(current_state, current_state),
            "current_expert": expert_type,
            "current_expert_name": expert_config["name"] if expert_config else None,
            "iteration": session.iteration_count,
            "can_confirm": state_machine.can_forward(),
            "can_rollback_to": state_machine.get_rollback_targets(),
            "pause_for_human": state_machine.should_pause_for_human(),
        }

    # ==================================================================
    # 对话交互 - 同步版本
    # ==================================================================

    def chat(self, session: ExpertSession, user_message: str) -> Dict:
        """发送用户消息，触发当前专家回复（同步）

        流程：
        1. 保存用户消息
        2. 如果当前是 IDLE 状态，自动进入架构设计状态
        3. 调用当前状态对应的专家生成回复
        4. 保存专家回复
        5. 返回回复内容和状态信息

        Args:
            session: 会话对象
            user_message: 用户消息内容

        Returns:
            包含回复内容、专家信息、状态信息的字典
        """
        state_machine = self.create_state_machine(session)
        current_state = state_machine.get_state()

        # 保存用户消息
        self.add_message(
            session_id=session.id,
            role="user",
            content=user_message,
            expert_type=None,
            state_label=current_state,
            iteration=session.iteration_count,
        )

        # 如果是 IDLE 状态，自动进入架构设计
        if current_state == TechExpertState.IDLE.value:
            from_state, to_state = state_machine.next_state(user_confirmation=False)
            self.record_transition(
                session_id=session.id,
                from_state=from_state,
                to_state=to_state,
                transition_type="auto",
                reason="首次对话，自动进入架构设计阶段",
            )
            self.update_session_state(session, to_state, state_machine.iteration)
            current_state = to_state

        # 构建上下文
        context_messages = self.build_context_messages(session, current_state)

        # 调用专家生成回复
        expert_type = state_machine.get_state_expert(current_state)
        response = state_machine.generate_expert_response(
            state=current_state,
            messages=context_messages,
        )

        # 估算 token 消耗
        token_usage = self.minimax_client.count_tokens(response)

        # 保存专家回复
        self.add_message(
            session_id=session.id,
            role="assistant",
            content=response,
            expert_type=expert_type,
            state_label=current_state,
            iteration=session.iteration_count,
            token_usage=token_usage,
        )

        # 更新 token 统计
        self.increment_tokens(session, token_usage)

        # 判断是否需要暂停等待人工确认
        should_pause = state_machine.should_pause_for_human(current_state)

        return {
            "content": response,
            "expert_type": expert_type,
            "expert_name": get_expert_name(expert_type) if expert_type else "",
            "state": current_state,
            "state_label": STATE_LABELS.get(current_state, current_state),
            "iteration": session.iteration_count,
            "pause_for_human": should_pause,
            "can_forward": state_machine.can_forward(),
        }

    # ==================================================================
    # 对话交互 - 流式版本（SSE）
    # ==================================================================

    async def chat_stream(
        self,
        session: ExpertSession,
        user_message: str,
    ) -> AsyncIterator[str]:
        """流式对话（SSE 格式输出）

        以 SSE 事件流的形式输出，包含：
        - state_enter: 进入新状态
        - message_chunk: 消息内容块
        - message_end: 单条消息生成完成
        - state_pause: 状态完成，暂停等待人工确认
        - error: 错误

        Args:
            session: 会话对象
            user_message: 用户消息内容

        Yields:
            SSE 格式的事件字符串
        """
        try:
            state_machine = self.create_state_machine(session)
            current_state = state_machine.get_state()

            # 保存用户消息
            self.add_message(
                session_id=session.id,
                role="user",
                content=user_message,
                expert_type=None,
                state_label=current_state,
                iteration=session.iteration_count,
            )

            # 如果是 IDLE 状态，自动进入架构设计
            if current_state == TechExpertState.IDLE.value:
                from_state, to_state = state_machine.next_state(user_confirmation=False)
                self.record_transition(
                    session_id=session.id,
                    from_state=from_state,
                    to_state=to_state,
                    transition_type="auto",
                    reason="首次对话，自动进入架构设计阶段",
                )
                self.update_session_state(session, to_state, state_machine.iteration)
                current_state = to_state

                # 发送状态进入事件
                expert_type = state_machine.get_state_expert(current_state)
                yield self._sse_event(SSEEvent.STATE_ENTER, {
                    "state": current_state,
                    "state_label": STATE_LABELS.get(current_state, current_state),
                    "expert_type": expert_type,
                    "expert_name": get_expert_name(expert_type) if expert_type else "",
                    "iteration": session.iteration_count,
                })

            # 构建上下文
            context_messages = self.build_context_messages(session, current_state)

            # 获取专家类型
            expert_type = state_machine.get_state_expert(current_state)

            # 流式生成回复（同步生成器包装为异步）
            import asyncio
            full_response = []
            system_prompt = ""
            if expert_type:
                from app.plugins.tech_experts.experts import get_expert_system_prompt
                system_prompt = get_expert_system_prompt(expert_type)

            full_messages = [
                {"role": "system", "content": system_prompt},
            ]
            full_messages.extend(context_messages)

            # 同步流式调用 + 解析 SSE data
            loop = asyncio.get_event_loop()

            def _sync_chat() -> list:
                """同步执行流式调用并解析结果"""
                chunks = []
                for data_str in self.minimax_client.chat_stream(full_messages):
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                chunks.append(content)
                    except (json.JSONDecodeError, KeyError):
                        continue
                return chunks

            chunks = await loop.run_in_executor(None, _sync_chat)

            for chunk in chunks:
                full_response.append(chunk)
                yield self._sse_event(SSEEvent.MESSAGE_CHUNK, {
                    "content": chunk,
                    "expert_type": expert_type,
                    "state": current_state,
                })
                await asyncio.sleep(0.01)  # 模拟流式效果

            complete_text = "".join(full_response)

            # 估算 token 消耗
            token_usage = self._count_tokens(complete_text)

            # 保存专家回复
            self.add_message(
                session_id=session.id,
                role="assistant",
                content=complete_text,
                expert_type=expert_type,
                state_label=current_state,
                iteration=session.iteration_count,
                token_usage=token_usage,
            )

            # 更新 token 统计
            self.increment_tokens(session, token_usage)

            # 发送消息结束事件
            yield self._sse_event(SSEEvent.MESSAGE_END, {
                "expert_type": expert_type,
                "expert_name": get_expert_name(expert_type) if expert_type else "",
                "state": current_state,
                "state_label": STATE_LABELS.get(current_state, current_state),
                "iteration": session.iteration_count,
                "token_usage": token_usage,
                "total_tokens": session.total_tokens,
            })

            # 判断是否需要暂停等待人工确认
            should_pause = state_machine.should_pause_for_human(current_state)
            if should_pause:
                yield self._sse_event(SSEEvent.STATE_PAUSE, {
                    "state": current_state,
                    "state_label": STATE_LABELS.get(current_state, current_state),
                    "can_forward": state_machine.can_forward(),
                    "can_rollback_to": state_machine.get_rollback_targets(),
                    "message": f"{STATE_LABELS.get(current_state, current_state)}阶段完成，请确认是否进入下一阶段",
                })

        except Exception as e:
            yield self._sse_event(SSEEvent.ERROR, {
                "message": str(e),
            })

    # ==================================================================
    # 状态控制
    # ==================================================================

    def confirm_state(self, session: ExpertSession) -> Dict:
        """确认当前状态，进入下一状态

        人工确认后，状态机正向流转到下一个状态。

        Args:
            session: 会话对象

        Returns:
            状态转移结果

        Raises:
            ValueError: 当前状态无法正向流转
        """
        state_machine = self.create_state_machine(session)

        if not state_machine.can_forward():
            raise ValueError("当前状态无法继续前进，已到达最终状态或无效状态")

        from_state, to_state = state_machine.next_state(user_confirmation=True)

        # 记录状态转移
        self.record_transition(
            session_id=session.id,
            from_state=from_state,
            to_state=to_state,
            transition_type="human_confirm",
            reason="用户确认，进入下一阶段",
        )

        # 更新会话状态
        self.update_session_state(session, to_state, state_machine.iteration)

        # 如果到达 DONE 状态，标记会话为完成
        if to_state == TechExpertState.DONE.value:
            session.status = "completed"
            self.db.commit()

        return {
            "from_state": from_state,
            "from_state_label": STATE_LABELS.get(from_state, from_state),
            "to_state": to_state,
            "to_state_label": STATE_LABELS.get(to_state, to_state),
            "transition_type": "human_confirm",
            "iteration": session.iteration_count,
        }

    def rollback_state(self, session: ExpertSession, target_state: str, reason: str = "") -> Dict:
        """回退到指定状态

        Args:
            session: 会话对象
            target_state: 目标状态
            reason: 回退原因

        Returns:
            状态转移结果

        Raises:
            ValueError: 不允许回退到目标状态
        """
        state_machine = self.create_state_machine(session)

        if not state_machine.can_rollback_to(target_state):
            raise ValueError(
                f"不允许从 {session.current_state} 回退到 {target_state}"
            )

        from_state, to_state = state_machine.rollback_to(target_state, reason)

        # 记录状态转移
        self.record_transition(
            session_id=session.id,
            from_state=from_state,
            to_state=to_state,
            transition_type="human_rollback",
            reason=reason or "用户手动回退",
        )

        # 更新会话状态
        self.update_session_state(session, to_state, state_machine.iteration)

        # 恢复为活跃状态
        if session.status != "active":
            session.status = "active"
            self.db.commit()

        # 添加一条系统消息说明回退
        from app.plugins.tech_experts.prompts import ROLLBACK_CONTEXT_PROMPT
        system_msg = ROLLBACK_CONTEXT_PROMPT.format(
            from_state=STATE_LABELS.get(from_state, from_state),
            to_state=STATE_LABELS.get(to_state, to_state),
            reason=reason or "用户手动回退",
        )
        self.add_message(
            session_id=session.id,
            role="system",
            content=system_msg,
            expert_type=None,
            state_label=to_state,
            iteration=session.iteration_count,
        )

        return {
            "from_state": from_state,
            "from_state_label": STATE_LABELS.get(from_state, from_state),
            "to_state": to_state,
            "to_state_label": STATE_LABELS.get(to_state, to_state),
            "transition_type": "human_rollback",
            "reason": reason,
            "iteration": session.iteration_count,
        }

    def switch_expert(
        self,
        session: ExpertSession,
        expert_type: str,
        reason: str = "",
    ) -> Dict:
        """手动切换到指定专家

        Args:
            session: 会话对象
            expert_type: 目标专家类型
            reason: 切换原因

        Returns:
            切换结果

        Raises:
            ValueError: 无效的专家类型
        """
        state_machine = self.create_state_machine(session)

        if expert_type not in EXPERT_CONFIG:
            raise ValueError(f"无效的专家类型: {expert_type}")

        from_state = state_machine.get_state()
        target_state = EXPERT_CONFIG[expert_type]["state"]

        if from_state == target_state:
            return {
                "from_state": from_state,
                "to_state": target_state,
                "transition_type": "human_switch",
                "message": "已在当前专家状态",
                "iteration": session.iteration_count,
            }

        # 执行切换
        from_state, to_state = state_machine.switch_expert(expert_type)

        # 记录状态转移
        self.record_transition(
            session_id=session.id,
            from_state=from_state,
            to_state=to_state,
            transition_type="human_switch",
            reason=reason or "用户手动切换专家",
        )

        # 更新会话状态
        self.update_session_state(session, to_state, state_machine.iteration)

        # 添加系统消息
        from app.plugins.tech_experts.prompts import SWITCH_EXPERT_PROMPT
        system_msg = SWITCH_EXPERT_PROMPT.format(
            expert_name=get_expert_name(expert_type),
            reason=reason or "用户手动切换专家",
        )
        self.add_message(
            session_id=session.id,
            role="system",
            content=system_msg,
            expert_type=None,
            state_label=to_state,
            iteration=session.iteration_count,
        )

        return {
            "from_state": from_state,
            "from_state_label": STATE_LABELS.get(from_state, from_state),
            "to_state": to_state,
            "to_state_label": STATE_LABELS.get(to_state, to_state),
            "transition_type": "human_switch",
            "expert_type": expert_type,
            "expert_name": get_expert_name(expert_type),
            "reason": reason,
            "iteration": session.iteration_count,
        }

    # ==================================================================
    # 验收标准（预留）
    # ==================================================================

    def get_acceptance_criteria(self, session: ExpertSession) -> Dict:
        """获取验收标准（预留接口）"""
        return {
            "criteria": session.acceptance_criteria,
            "message": "Step 2功能，即将上线",
        }

    def set_acceptance_criteria(
        self,
        session: ExpertSession,
        criteria: Dict,
    ) -> Dict:
        """设置验收标准（预留接口）"""
        # 预留功能，暂不实际保存复杂逻辑
        session.acceptance_criteria = criteria
        self.db.commit()
        return {
            "criteria": criteria,
            "message": "Step 2功能，即将上线",
        }

    # ==================================================================
    # 工具方法
    # ==================================================================

    def _sse_event(self, event: str, data: Dict) -> str:
        """构造 SSE 事件字符串

        Args:
            event: 事件类型
            data: 事件数据

        Returns:
            SSE 格式的字符串
        """
        payload = {
            "event": event,
            "data": data,
        }
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    def _count_tokens(self, text: str) -> int:
        """估算 token 数量（简单估算）

        中文每个字约 1 token，英文每 4 个字符约 1 token。
        """
        cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        en_chars = len(text) - cn_chars
        return cn_chars + max(1, en_chars // 4)
