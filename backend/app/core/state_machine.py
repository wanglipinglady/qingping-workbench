"""
状态机引擎基类
提供通用的有限状态机实现，可用于对话流程、任务状态管理等
"""
from typing import Dict, Any, Optional, Callable
from enum import Enum


class StateMachine:
    """
    状态机引擎基类
    支持定义状态、事件、转换和动作
    """

    def __init__(self, initial_state: str):
        """
        初始化状态机

        Args:
            initial_state: 初始状态
        """
        self.current_state = initial_state
        # 转换表: { 当前状态: { 事件: (目标状态, 动作函数) } }
        self._transitions: Dict[str, Dict[str, tuple]] = {}
        # 进入状态时的回调
        self._on_enter: Dict[str, Callable] = {}
        # 离开状态时的回调
        self._on_exit: Dict[str, Callable] = {}

    def add_transition(
        self,
        from_state: str,
        event: str,
        to_state: str,
        action: Optional[Callable] = None,
    ) -> None:
        """
        添加状态转换规则

        Args:
            from_state: 源状态
            event: 触发事件
            to_state: 目标状态
            action: 转换时执行的动作函数
        """
        if from_state not in self._transitions:
            self._transitions[from_state] = {}
        self._transitions[from_state][event] = (to_state, action)

    def on_enter(self, state: str, callback: Callable) -> None:
        """
        注册进入状态时的回调

        Args:
            state: 状态
            callback: 回调函数
        """
        self._on_enter[state] = callback

    def on_exit(self, state: str, callback: Callable) -> None:
        """
        注册离开状态时的回调

        Args:
            state: 状态
            callback: 回调函数
        """
        self._on_exit[state] = callback

    def trigger(self, event: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        触发事件，尝试状态转换

        Args:
            event: 事件名称
            context: 上下文数据

        Returns:
            是否成功转换
        """
        context = context or {}

        # 检查当前状态是否有此事件的转换
        if self.current_state not in self._transitions:
            return False
        if event not in self._transitions[self.current_state]:
            return False

        to_state, action = self._transitions[self.current_state][event]
        from_state = self.current_state

        # 执行离开状态回调
        if from_state in self._on_exit:
            self._on_exit[from_state](context)

        # 执行转换动作
        if action:
            action(context)

        # 切换状态
        self.current_state = to_state

        # 执行进入状态回调
        if to_state in self._on_enter:
            self._on_enter[to_state](context)

        return True

    def can_trigger(self, event: str) -> bool:
        """
        检查当前状态下是否可以触发指定事件

        Args:
            event: 事件名称

        Returns:
            是否可以触发
        """
        if self.current_state not in self._transitions:
            return False
        return event in self._transitions[self.current_state]

    def get_available_events(self) -> list:
        """
        获取当前状态下所有可触发的事件

        Returns:
            事件名称列表
        """
        if self.current_state not in self._transitions:
            return []
        return list(self._transitions[self.current_state].keys())
