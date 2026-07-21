"""
状态机核心逻辑单元测试
覆盖：状态流转、回退、专家切换、边界条件
注意：不依赖真实 MiniMax API，所有外部调用都 mock
"""
import pytest
from unittest.mock import MagicMock

from app.plugins.wechat_writer.state_machine import (
    WeChatWriterStateMachine,
    WriterState,
    FORWARD_TRANSITIONS,
    get_all_previous_states,
    STATE_LABELS,
)


@pytest.fixture
def mock_minimax():
    """创建一个 mock 的 MiniMax 客户端"""
    mock = MagicMock()
    mock.chat.return_value = {
        "choices": [{"message": {"content": "mock response"}}]
    }
    return mock


@pytest.fixture
def sm(mock_minimax):
    """创建一个初始状态为 idle 的状态机"""
    return WeChatWriterStateMachine(session_id=1, minimax_client=mock_minimax)


# =====================================================================
# 基础状态查询测试
# =====================================================================

class TestStateBasics:
    """基础状态查询"""

    def test_initial_state_is_idle(self, sm):
        assert sm.get_state() == WriterState.IDLE.value

    def test_state_label_mapping(self):
        assert STATE_LABELS["idle"] == "初始化"
        assert STATE_LABELS["topic_confirm"] == "选题确认"
        assert STATE_LABELS["done"] == "已完成"

    def test_get_next_state(self, sm):
        """idle 的下一个状态应该是 topic_confirm"""
        assert sm.get_next_state() == WriterState.TOPIC_CONFIRM.value

    def test_get_next_state_when_done(self, sm):
        """done 状态没有下一个状态"""
        sm.current_state = WriterState.DONE.value
        assert sm.get_next_state() is None

    def test_can_forward(self, sm):
        assert sm.can_forward() is True

    def test_can_forward_when_done(self, sm):
        sm.current_state = WriterState.DONE.value
        assert sm.can_forward() is False


# =====================================================================
# 正向流转测试
# =====================================================================

class TestForwardTransitions:
    """正向状态流转"""

    def test_full_forward_path(self, sm):
        """测试完整的正向流转路径：idle → topic_confirm → research → outline → draft → polish → done"""
        expected_path = [
            ("idle", "topic_confirm"),
            ("topic_confirm", "research"),
            ("research", "outline"),
            ("outline", "draft"),
            ("draft", "polish"),
            ("polish", "done"),
        ]
        for from_state, to_state in expected_path:
            assert sm.current_state == from_state
            result = sm.next_state()
            assert result == (from_state, to_state)
            assert sm.current_state == to_state

    def test_next_state_raises_when_done(self, sm):
        """done 状态调用 next_state 应该报错"""
        sm.current_state = WriterState.DONE.value
        with pytest.raises(ValueError, match="无法正向流转"):
            sm.next_state()

    def test_iteration_increments_on_work_states(self, sm):
        """进入工作状态时，迭代轮次应该 +1"""
        assert sm.iteration == 0
        sm.next_state()  # idle → topic_confirm（工作状态）
        assert sm.iteration == 1
        sm.next_state()  # topic_confirm → research（工作状态）
        assert sm.iteration == 2


# =====================================================================
# 回退测试
# =====================================================================

class TestRollback:
    """状态回退"""

    def test_get_rollback_targets_from_research(self, sm):
        sm.current_state = WriterState.RESEARCH.value
        targets = sm.get_rollback_targets()
        assert "idle" in targets
        assert "topic_confirm" in targets
        assert "research" not in targets  # 不能回退到自己

    def test_get_rollback_targets_from_idle(self, sm):
        """idle 状态没有可回退的目标"""
        sm.current_state = WriterState.IDLE.value
        assert sm.get_rollback_targets() == []

    def test_rollback_from_research_to_topic_confirm(self, sm):
        sm.current_state = WriterState.RESEARCH.value
        initial_iter = sm.iteration
        result = sm.rollback_to(WriterState.TOPIC_CONFIRM.value)
        assert result == ("research", "topic_confirm")
        assert sm.current_state == "topic_confirm"
        assert sm.iteration == initial_iter + 1  # 回退后迭代 +1

    def test_rollback_to_invalid_target_raises(self, sm):
        """回退到不合法的目标状态应该报错"""
        sm.current_state = WriterState.TOPIC_CONFIRM.value
        with pytest.raises(ValueError, match="不允许从"):
            sm.rollback_to(WriterState.RESEARCH.value)  # 不能回退到后面的状态

    def test_rollback_from_polish_to_any_earlier(self, sm):
        """从 polish 可以回退到任意之前的状态"""
        sm.current_state = WriterState.POLISH.value
        for target in ["idle", "topic_confirm", "research", "outline", "draft"]:
            sm_copy = WeChatWriterStateMachine(
                session_id=1, minimax_client=MagicMock(),
                initial_state=WriterState.POLISH.value
            )
            result = sm_copy.rollback_to(target)
            assert result[1] == target


# =====================================================================
# 辅助函数测试
# =====================================================================

class TestHelperFunctions:
    """get_all_previous_states 等辅助函数"""

    def test_get_all_previous_states_idle(self):
        assert get_all_previous_states("idle") == []

    def test_get_all_previous_states_done(self):
        prev = get_all_previous_states("done")
        assert "polish" in prev
        assert "idle" in prev
        assert "done" not in prev

    def test_get_all_previous_states_order(self):
        """返回的状态顺序应该与正向流转顺序一致"""
        prev = get_all_previous_states("outline")
        assert prev == ["idle", "topic_confirm", "research"]


# =====================================================================
# 人工介入测试
# =====================================================================

class TestHumanIntervention:
    """人工确认机制"""

    def test_pause_states(self, sm):
        """所有工作状态完成后都需要暂停确认"""
        work_states = ["topic_confirm", "research", "outline", "draft", "polish"]
        for state in work_states:
            sm.current_state = state
            assert sm.should_pause_for_human() is True, f"{state} 应该暂停等待确认"

    def test_no_pause_for_idle_and_done(self, sm):
        """idle 和 done 不需要暂停确认"""
        sm.current_state = "idle"
        assert sm.should_pause_for_human() is False
        sm.current_state = "done"
        assert sm.should_pause_for_human() is False
