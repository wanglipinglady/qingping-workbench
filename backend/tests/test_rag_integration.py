"""
RAG 集成单元测试
覆盖：rag_helper 工具函数、state_machine RAG 上下文注入
注意：不依赖真实 MiniMax API，所有外部调用都 mock
"""
import pytest
from unittest.mock import MagicMock, patch

from app.plugins.wechat_writer.rag_helper import (
    format_rag_context,
    build_search_queries,
)
from app.plugins.wechat_writer.state_machine import (
    WeChatWriterStateMachine,
    WriterState,
)


# =====================================================================
# rag_helper 工具函数测试
# =====================================================================

class TestFormatRagContext:
    """format_rag_context 格式化 RAG 上下文"""

    def test_empty_results(self):
        """空结果应返回空字符串"""
        assert format_rag_context([]) == ""

    def test_none_results(self):
        """None 应返回空字符串"""
        assert format_rag_context(None) == ""

    def test_single_result(self):
        """单条结果应正确格式化"""
        results = [
            {
                "path": "notes/ai.md",
                "title": "AI 入门",
                "content": "人工智能是计算机科学的一个分支",
                "score": 0.95,
                "date": "2026-01-15",
            }
        ]
        ctx = format_rag_context(results)
        assert "AI 入门" in ctx
        assert "notes/ai.md" in ctx
        assert "人工智能" in ctx
        assert "0.95" in ctx
        assert "2026-01-15" in ctx

    def test_multiple_results_dedup(self):
        """同一篇文档的多条结果应去重，只保留最相关的一条"""
        results = [
            {"path": "docA.md", "title": "文档A-1", "content": "内容1", "score": 0.9},
            {"path": "docA.md", "title": "文档A-2", "content": "内容2", "score": 0.85},
            {"path": "docB.md", "title": "文档B", "content": "内容3", "score": 0.8},
        ]
        ctx = format_rag_context(results)
        # 只应该出现 2 篇文档（docA 去重）
        assert ctx.count("资料 #") == 2
        assert "文档A-1" in ctx  # 保留分数最高的
        assert "文档B" in ctx

    def test_max_snippets_limit(self):
        """超过 max_snippets 的结果应被截断"""
        results = [
            {"path": f"doc{i}.md", "title": f"文档{i}", "content": f"内容{i}", "score": 0.9 - i*0.01}
            for i in range(15)
        ]
        ctx = format_rag_context(results, max_snippets=5)
        assert ctx.count("资料 #") == 5

    def test_contains_usage_instructions(self):
        """结果应包含使用说明"""
        results = [
            {"path": "test.md", "title": "测试", "content": "测试内容", "score": 0.9}
        ]
        ctx = format_rag_context(results)
        assert "使用说明" in ctx
        assert "Obsidian" in ctx


class TestBuildSearchQueries:
    """build_search_queries 构建搜索关键词"""

    def test_only_topic(self):
        """只有主题时返回主题"""
        queries = build_search_queries("工业 AI 落地")
        assert len(queries) >= 1
        assert "工业 AI 落地" in queries

    def test_topic_and_confirmed(self):
        """有确认主题时返回多个关键词"""
        queries = build_search_queries(
            "工业 AI",
            "工业 AI 在离散制造中的落地实践，从数据采集到智能决策"
        )
        assert len(queries) >= 2
        assert "工业 AI" in queries

    def test_empty_topic(self):
        """空主题返回空列表"""
        queries = build_search_queries("")
        assert queries == []

    def test_same_topic_and_confirmed(self):
        """主题和确认主题相同时不重复"""
        queries = build_search_queries("AI", "AI")
        assert len(queries) == 1


# =====================================================================
# state_machine RAG 上下文注入测试
# =====================================================================

@pytest.fixture
def mock_minimax():
    """创建一个 mock 的 MiniMax 客户端"""
    mock = MagicMock()
    mock.chat.return_value = {
        "choices": [{"message": {"content": "mock expert response"}}]
    }
    return mock


@pytest.fixture
def sm(mock_minimax):
    """创建一个状态机"""
    return WeChatWriterStateMachine(session_id=1, minimax_client=mock_minimax)


class TestRAGContextInjection:
    """RAG 上下文注入到 state_machine"""

    def test_rag_context_injected_into_messages(self, sm, mock_minimax):
        """rag_context 应该被注入到 full_messages 中"""
        sm.current_state = "research"
        rag_text = "=== RAG 资料 ===\n资料1: ..."

        sm.generate_expert_response(
            state="research",
            messages=[{"role": "user", "content": "请搜集资料"}],
            context={"rag_context": rag_text},
        )

        # 验证 chat 被调用，且消息中包含 RAG 上下文
        mock_minimax.chat.assert_called_once()
        call_args = mock_minimax.chat.call_args
        messages = call_args[0][0]
        all_content = " ".join(m["content"] for m in messages)
        assert "RAG 资料" in all_content

    def test_empty_rag_context_not_injected(self, sm, mock_minimax):
        """空的 rag_context 不应该被注入"""
        sm.current_state = "research"

        sm.generate_expert_response(
            state="research",
            messages=[{"role": "user", "content": "请搜集资料"}],
            context={"rag_context": ""},
        )

        call_args = mock_minimax.chat.call_args
        messages = call_args[0][0]
        # 不应该有额外的 system 消息（只有 system prompt + 历史消息）
        assert len(messages) == 2  # 1 system prompt + 1 user message

    def test_rag_context_works_with_other_context(self, sm, mock_minimax):
        """rag_context 应该和 rollback/regenerate 等其他上下文共存"""
        sm.current_state = "research"
        rag_text = "=== RAG 资料 ==="

        sm.generate_expert_response(
            state="research",
            messages=[{"role": "user", "content": "请重新搜集"}],
            context={
                "is_regenerate": True,
                "feedback": "请增加更多案例",
                "rag_context": rag_text,
            },
        )

        call_args = mock_minimax.chat.call_args
        messages = call_args[0][0]
        all_content = " ".join(m["content"] for m in messages)
        # 两种上下文都应该存在
        assert "RAG 资料" in all_content
        assert "重新生成" in all_content
        assert "更多案例" in all_content

    def test_no_context_no_rag(self, sm, mock_minimax):
        """不传 context 时正常工作（向后兼容）"""
        sm.current_state = "topic_confirm"

        response = sm.generate_expert_response(
            state="topic_confirm",
            messages=[{"role": "user", "content": "工业 AI"}],
            context=None,
        )

        assert response == "mock expert response"
        mock_minimax.chat.assert_called_once()
