"""写作助手状态机（核心模块）

实现「状态图式协作 + 人工介入机制」的核心逻辑。

状态流转图（正向）：
    idle → topic_confirm → research → outline → draft → polish → done

回退路径（任意状态可回退到任意前置状态）：
    research → topic_confirm
    outline → topic_confirm / research
    draft → topic_confirm / research / outline
    polish → topic_confirm / research / outline / draft
    done → 任意前置状态

人工介入机制：
    - 每个工作状态（topic_confirm/research/outline/draft/polish）完成后默认暂停
    - 用户可以：确认前进 / 重新生成（填建议）/ 回退 / 切换专家
"""

from enum import Enum
from typing import List, Dict, Optional, Tuple
import json
import asyncio

from app.capabilities.llm.minimax_client import MiniMaxClient
from app.plugins.wechat_writer.experts import (
    ExpertType,
    EXPERT_CONFIG,
    get_expert_system_prompt,
    get_expert_name,
    get_expert_by_state,
    get_expert_config,
)
from app.plugins.wechat_writer.prompts import (
    STATE_ENTER_PROMPT,
    ROLLBACK_CONTEXT_PROMPT,
    SWITCH_EXPERT_PROMPT,
    REGENERATE_PROMPT,
)


# =============================================================================
# 状态枚举
# =============================================================================

class WriterState(str, Enum):
    """写作助手状态枚举"""

    IDLE = "idle"                # 初始状态
    TOPIC_CONFIRM = "topic_confirm"  # 选题确认
    RESEARCH = "research"          # 资料搜集
    OUTLINE = "outline"            # 大纲设计
    DRAFT = "draft"                # 初稿写作
    POLISH = "polish"              # 润色优化
    DONE = "done"                  # 已完成


# =============================================================================
# 状态中文名映射
# =============================================================================

STATE_LABELS: Dict[str, str] = {
    WriterState.IDLE.value: "初始化",
    WriterState.TOPIC_CONFIRM.value: "选题确认",
    WriterState.RESEARCH.value: "资料搜集",
    WriterState.OUTLINE.value: "大纲设计",
    WriterState.DRAFT.value: "初稿写作",
    WriterState.POLISH.value: "润色优化",
    WriterState.DONE.value: "已完成",
}


# =============================================================================
# 状态转移图定义
# =============================================================================

# 正向流转路径
FORWARD_TRANSITIONS: Dict[str, str] = {
    WriterState.IDLE.value: WriterState.TOPIC_CONFIRM.value,
    WriterState.TOPIC_CONFIRM.value: WriterState.RESEARCH.value,
    WriterState.RESEARCH.value: WriterState.OUTLINE.value,
    WriterState.OUTLINE.value: WriterState.DRAFT.value,
    WriterState.DRAFT.value: WriterState.POLISH.value,
    WriterState.POLISH.value: WriterState.DONE.value,
}


def get_all_previous_states(state: str) -> List[str]:
    """获取某个状态的所有前置状态（用于回退）"""
    all_states = [
        WriterState.IDLE.value,
        WriterState.TOPIC_CONFIRM.value,
        WriterState.RESEARCH.value,
        WriterState.OUTLINE.value,
        WriterState.DRAFT.value,
        WriterState.POLISH.value,
        WriterState.DONE.value,
    ]
    idx = all_states.index(state) if state in all_states else -1
    if idx <= 0:
        return []
    return all_states[:idx]


# 需要人工确认后才能继续的状态（所有工作状态都需要暂停确认）
PAUSE_AFTER_STATES: set = {
    WriterState.TOPIC_CONFIRM.value,
    WriterState.RESEARCH.value,
    WriterState.OUTLINE.value,
    WriterState.DRAFT.value,
    WriterState.POLISH.value,
}


# =============================================================================
# 状态机类
# =============================================================================

class WeChatWriterStateMachine:
    """微信公众号写作助手状态机

    管理单个会话的状态流转、专家调用和人工介入逻辑。

    Attributes:
        session_id: 会话 ID
        minimax_client: MiniMax 客户端实例
        current_state: 当前状态
        iteration: 当前迭代轮次
        _state_output_cache: 每个状态的最新输出缓存
    """

    def __init__(self, session_id: int, minimax_client: MiniMaxClient,
                 initial_state: str = WriterState.IDLE.value,
                 iteration: int = 0):
        """初始化状态机

        Args:
            session_id: 会话 ID
            minimax_client: MiniMax 客户端
            initial_state: 初始状态
            iteration: 初始迭代轮次
        """
        self.session_id = session_id
        self.minimax_client = minimax_client
        self.current_state = initial_state
        self.iteration = iteration
        # 状态输出缓存：{state: content} 存储每个状态的最新输出
        self._state_output_cache: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # 基础状态查询
    # ------------------------------------------------------------------

    def get_state(self) -> str:
        """获取当前状态"""
        return self.current_state

    def get_state_label(self) -> str:
        """获取当前状态的中文名"""
        return STATE_LABELS.get(self.current_state, self.current_state)

    def get_next_state(self) -> Optional[str]:
        """获取正向流转的下一个状态

        Returns:
            下一个状态，如果已经是最终状态则返回 None
        """
        return FORWARD_TRANSITIONS.get(self.current_state)

    def can_forward(self) -> bool:
        """判断是否可以正向流转"""
        return self.current_state in FORWARD_TRANSITIONS

    def get_rollback_targets(self) -> List[str]:
        """获取当前状态可回退的目标状态列表"""
        return get_all_previous_states(self.current_state)

    def can_rollback_to(self, target_state: str) -> bool:
        """判断是否可以回退到指定状态"""
        return target_state in self.get_rollback_targets()

    # ------------------------------------------------------------------
    # 状态流转操作
    # ------------------------------------------------------------------

    def next_state(self, user_confirmation: bool = True) -> Tuple[str, str]:
        """进入下一状态（正向流转）

        Args:
            user_confirmation: 是否经过用户确认

        Returns:
            (from_state, to_state) 状态转移元组

        Raises:
            ValueError: 当前状态无法正向流转
        """
        if not self.can_forward():
            raise ValueError(f"当前状态 {self.current_state} 无法正向流转")

        from_state = self.current_state
        to_state = FORWARD_TRANSITIONS[self.current_state]

        self.current_state = to_state

        # 进入新状态时，如果是工作状态，迭代轮次 +1
        if to_state in PAUSE_AFTER_STATES:
            self.iteration += 1

        return from_state, to_state

    def rollback_to(self, target_state: str, reason: str = "") -> Tuple[str, str]:
        """回退到指定状态

        Args:
            target_state: 目标状态
            reason: 回退原因

        Returns:
            (from_state, to_state) 状态转移元组

        Raises:
            ValueError: 不允许回退到目标状态
        """
        if not self.can_rollback_to(target_state):
            raise ValueError(
                f"不允许从 {self.current_state} 回退到 {target_state}，"
                f"允许的回退目标: {self.get_rollback_targets()}"
            )

        from_state = self.current_state
        self.current_state = target_state

        # 回退后迭代轮次 +1（视为新一轮迭代的开始）
        self.iteration += 1

        return from_state, target_state

    def switch_expert(self, expert_type: str) -> Tuple[str, str]:
        """手动切换到指定专家对应的状态

        Args:
            expert_type: 专家类型

        Returns:
            (from_state, to_state) 状态转移元组

        Raises:
            ValueError: 无效的专家类型
        """
        if expert_type not in EXPERT_CONFIG:
            raise ValueError(f"无效的专家类型: {expert_type}")

        target_state = EXPERT_CONFIG[expert_type]["state"]
        from_state = self.current_state

        if from_state == target_state:
            return from_state, target_state

        self.current_state = target_state
        self.iteration += 1

        return from_state, target_state

    # ------------------------------------------------------------------
    # 专家调用
    # ------------------------------------------------------------------

    def get_state_expert(self, state: Optional[str] = None) -> Optional[str]:
        """获取指定状态对应的专家类型

        Args:
            state: 状态，默认使用当前状态

        Returns:
            专家类型，如果状态没有对应专家则返回 None
        """
        if state is None:
            state = self.current_state
        return get_expert_by_state(state)

    def should_pause_for_human(self, state: Optional[str] = None) -> bool:
        """判断指定状态完成后是否需要人工确认

        Args:
            state: 状态，默认使用当前状态

        Returns:
            是否需要暂停等待人工确认
        """
        if state is None:
            state = self.current_state
        return state in PAUSE_AFTER_STATES

    def generate_expert_response(
        self,
        state: str,
        messages: List[Dict[str, str]],
        context: Optional[Dict] = None,
    ) -> str:
        """调用对应专家生成回复（同步）

        Args:
            state: 当前状态（决定使用哪个专家）
            messages: 历史消息列表
            context: 附加上下文信息（is_rollback, is_switch, is_regenerate 等）

        Returns:
            专家生成的回复文本
        """
        expert_type = self.get_state_expert(state)
        if not expert_type:
            raise ValueError(f"状态 {state} 没有对应的专家角色")

        # 获取专家的 System Prompt
        system_prompt = get_expert_system_prompt(expert_type)

        # 构建完整的消息列表
        full_messages = [
            {"role": "system", "content": system_prompt},
        ]

        # 如果有上下文信息，添加上下文说明
        if context and context.get("is_rollback"):
            rollback_msg = ROLLBACK_CONTEXT_PROMPT.format(
                from_state=STATE_LABELS.get(context.get("from_state", ""), ""),
                to_state=STATE_LABELS.get(state, ""),
                reason=context.get("reason", ""),
            )
            full_messages.append({"role": "system", "content": rollback_msg})

        if context and context.get("is_switch"):
            switch_msg = SWITCH_EXPERT_PROMPT.format(
                expert_name=get_expert_name(expert_type),
                reason=context.get("reason", "用户手动切换专家"),
            )
            full_messages.append({"role": "system", "content": switch_msg})

        if context and context.get("is_regenerate"):
            regen_msg = REGENERATE_PROMPT.format(
                feedback=context.get("feedback", "用户未给出具体建议，请换角度重新生成"),
            )
            full_messages.append({"role": "system", "content": regen_msg})

        # 如果有 RAG 检索到的资料，注入到上下文中
        if context and context.get("rag_context"):
            rag_text = context["rag_context"]
            if rag_text and len(rag_text.strip()) > 0:
                full_messages.append({"role": "system", "content": rag_text})

        # 注入前置阶段内容（选题确认单/资料卡片/大纲/初稿）
        if context:
            if context.get("topic_analysis"):
                full_messages.append({
                    "role": "system",
                    "content": f"【选题确认单】\n{context['topic_analysis']}"
                })
            if context.get("materials"):
                full_messages.append({
                    "role": "system",
                    "content": f"【资料卡片】\n{context['materials']}"
                })
            if context.get("outline"):
                full_messages.append({
                    "role": "system",
                    "content": f"【文章大纲】\n{context['outline']}"
                })
            if context.get("draft_content"):
                full_messages.append({
                    "role": "system",
                    "content": f"【初稿全文】\n{context['draft_content']}"
                })

        # 添加历史消息
        full_messages.extend(messages)

        # 调用 MiniMax
        result = self.minimax_client.chat(full_messages)
        response = self._extract_content(result)

        # 缓存当前状态的输出
        self._state_output_cache[state] = response

        return response

    async def generate_expert_response_stream(
        self,
        state: str,
        messages: List[Dict[str, str]],
        context: Optional[Dict] = None,
    ):
        """调用对应专家生成回复（流式，异步生成器）

        Args:
            state: 当前状态
            messages: 历史消息列表
            context: 附加上下文

        Yields:
            逐块生成的文本内容
        """
        expert_type = self.get_state_expert(state)
        if not expert_type:
            raise ValueError(f"状态 {state} 没有对应的专家角色")

        system_prompt = get_expert_system_prompt(expert_type)

        full_messages = [
            {"role": "system", "content": system_prompt},
        ]

        if context and context.get("is_rollback"):
            rollback_msg = ROLLBACK_CONTEXT_PROMPT.format(
                from_state=STATE_LABELS.get(context.get("from_state", ""), ""),
                to_state=STATE_LABELS.get(state, ""),
                reason=context.get("reason", ""),
            )
            full_messages.append({"role": "system", "content": rollback_msg})

        if context and context.get("is_switch"):
            switch_msg = SWITCH_EXPERT_PROMPT.format(
                expert_name=get_expert_name(expert_type),
                reason=context.get("reason", "用户手动切换专家"),
            )
            full_messages.append({"role": "system", "content": switch_msg})

        if context and context.get("is_regenerate"):
            regen_msg = REGENERATE_PROMPT.format(
                feedback=context.get("feedback", "用户未给出具体建议，请换角度重新生成"),
            )
            full_messages.append({"role": "system", "content": regen_msg})

        # 如果有 RAG 检索到的资料，注入到上下文中
        if context and context.get("rag_context"):
            rag_text = context["rag_context"]
            if rag_text and len(rag_text.strip()) > 0:
                full_messages.append({"role": "system", "content": rag_text})

        # 注入前置阶段内容（选题确认单/资料卡片/大纲/初稿）
        if context:
            if context.get("topic_analysis"):
                full_messages.append({
                    "role": "system",
                    "content": f"【选题确认单】\n{context['topic_analysis']}"
                })
            if context.get("materials"):
                full_messages.append({
                    "role": "system",
                    "content": f"【资料卡片】\n{context['materials']}"
                })
            if context.get("outline"):
                full_messages.append({
                    "role": "system",
                    "content": f"【文章大纲】\n{context['outline']}"
                })
            if context.get("draft_content"):
                full_messages.append({
                    "role": "system",
                    "content": f"【初稿全文】\n{context['draft_content']}"
                })

        full_messages.extend(messages)

        # 用线程执行同步生成器，再异步 yield 结果
        full_response = []
        loop = asyncio.get_event_loop()

        def _collect_and_parse() -> list:
            """同步收集并解析所有流式数据"""
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

        chunks = await loop.run_in_executor(None, _collect_and_parse)

        for chunk in chunks:
            full_response.append(chunk)
            yield chunk
            await asyncio.sleep(0.01)  # 模拟流式效果

        complete_text = "".join(full_response)
        self._state_output_cache[state] = complete_text

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    def _extract_content(self, result: dict) -> str:
        """从 MiniMax API 响应中提取文本内容

        Args:
            result: API 响应字典

        Returns:
            提取的文本内容
        """
        try:
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice:
                    return choice["message"].get("content", "")
                elif "text" in choice:
                    return choice["text"]
            return ""
        except Exception:
            return str(result)

    def build_state_enter_message(self, state: str) -> str:
        """构建进入新状态的提示消息"""
        expert_type = self.get_state_expert(state)
        expert_name = get_expert_name(expert_type) if expert_type else "系统"
        return STATE_ENTER_PROMPT.format(
            state_name=STATE_LABELS.get(state, state),
            iteration=self.iteration,
            expert_name=expert_name,
        )

    def get_state_output(self, state: str) -> Optional[str]:
        """获取指定状态的最新输出缓存"""
        return self._state_output_cache.get(state)

    def set_state_output(self, state: str, content: str):
        """设置指定状态的输出缓存"""
        self._state_output_cache[state] = content
