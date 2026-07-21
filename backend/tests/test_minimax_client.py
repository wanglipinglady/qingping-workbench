"""
AI 输出清洗与 MiniMax 客户端单元测试
覆盖：推理标签过滤、响应解析、超时配置
"""
import pytest

from app.capabilities.llm.minimax_client import MiniMaxClient


# =====================================================================
# _strip_think_tags 测试
# =====================================================================

class TestStripThinkTags:
    """AI 输出清洗：移除推理过程标签"""

    def test_clean_text_unchanged(self):
        """干净的文本应该保持不变"""
        text = "这是一段正常的输出内容，不包含任何推理标签。"
        result = MiniMaxClient._strip_think_tags(text)
        assert result == text

    def test_standard_think_tags(self):
        """标准 <think>...</think> 标签应该被移除"""
        text = "<think>我需要先分析这个问题的背景</think>这是最终的回答内容。"
        result = MiniMaxClient._strip_think_tags(text)
        assert "<think>" not in result
        assert "我需要先分析" not in result
        assert "这是最终的回答内容" in result

    def test_multiline_think_tags(self):
        """跨行的 <think> 标签也应该被移除"""
        text = """<think>
让我分析一下这个问题：
1. 首先考虑背景
2. 然后拆解需求
</think>
好的，根据分析，我给出以下建议："""
        result = MiniMaxClient._strip_think_tags(text)
        assert "<think>" not in result
        assert "让我分析一下" not in result
        assert "好的，根据分析" in result

    def test_special_format_tags(self):
        """特殊字符格式的推理标签 <RichMediaReference>...superscript: 应该被移除"""
        text = "<RichMediaReference>用户问了一个关于AI的问题，我需要从多个角度分析superscript:这是最终的回答。"
        result = MiniMaxClient._strip_think_tags(text)
        assert "<RichMediaReference>" not in result
        assert "用户问了一个关于AI的问题" not in result
        assert "这是最终的回答" in result

    def test_both_formats_mixed(self):
        """两种格式混合出现时都应该被移除"""
        text = "<think>内部思考</think>开头内容<RichMediaReference>更多推理superscript:结尾内容"
        result = MiniMaxClient._strip_think_tags(text)
        assert "<think>" not in result
        assert "内部思考" not in result
        assert "更多推理" not in result
        assert "开头内容" in result
        assert "结尾内容" in result

    def test_empty_string(self):
        """空字符串应该返回空"""
        assert MiniMaxClient._strip_think_tags("") == ""
        assert MiniMaxClient._strip_think_tags(None) is None

    def test_only_tags(self):
        """只有标签没有实际内容时返回空"""
        text = "<think>全是推理内容</think>"
        result = MiniMaxClient._strip_think_tags(text)
        assert result.strip() == ""


# =====================================================================
# 超时配置测试
# =====================================================================

class TestTimeoutConfig:
    """超时配置验证"""

    def test_default_timeouts(self):
        """默认超时配置应该正确"""
        client = MiniMaxClient()
        assert client.chat_timeout == 180, "对话生成超时应该是 180 秒"
        assert client.generic_timeout == 60, "普通请求超时应该是 60 秒"

    def test_chat_timeout_longer_than_generic(self):
        """对话超时应该长于普通请求超时"""
        client = MiniMaxClient()
        assert client.chat_timeout > client.generic_timeout


# =====================================================================
# 响应解析测试
# =====================================================================

class TestResponseParsing:
    """MiniMax API 响应解析（通过 get_chat_reply 间接测试）"""

    @pytest.fixture
    def client(self):
        return MiniMaxClient()

    def test_get_chat_reply_standard_format(self, client):
        """标准格式响应应该正确提取内容"""
        original_chat = client.chat
        client.chat = lambda msgs, **kw: {
            "choices": [{"message": {"content": "你好，这是 AI 的回答。"}}]
        }
        try:
            reply = client.get_chat_reply([{"role": "user", "content": "test"}])
            assert reply == "你好，这是 AI 的回答。"
        finally:
            client.chat = original_chat

    def test_get_chat_reply_text_format(self, client):
        """text 格式响应也应该支持"""
        original_chat = client.chat
        client.chat = lambda msgs, **kw: {
            "choices": [{"text": "这是 text 格式的回答。"}]
        }
        try:
            reply = client.get_chat_reply([{"role": "user", "content": "test"}])
            assert reply == "这是 text 格式的回答。"
        finally:
            client.chat = original_chat

    def test_get_chat_reply_empty_choices(self, client):
        """空 choices 应该返回空字符串"""
        original_chat = client.chat
        client.chat = lambda msgs, **kw: {"choices": []}
        try:
            reply = client.get_chat_reply([{"role": "user", "content": "test"}])
            assert reply == ""
        finally:
            client.chat = original_chat

    def test_get_chat_reply_strips_think_tags(self, client):
        """get_chat_reply 应该自动移除 think 标签"""
        # 我们需要 mock chat 方法
        original_chat = client.chat
        client.chat = lambda msgs, **kw: {
            "choices": [{"message": {"content": "<think>推理</think>最终答案"}}]
        }
        try:
            reply = client.get_chat_reply([{"role": "user", "content": "test"}])
            assert "推理" not in reply
            assert "最终答案" in reply
        finally:
            client.chat = original_chat
