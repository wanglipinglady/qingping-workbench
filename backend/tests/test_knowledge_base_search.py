"""
知识库语义搜索单元测试
覆盖：distance 字段 Bug 修复（service.search 从 score 反推 distance）
注意：mock 向量库与数据库，不依赖真实 ChromaDB / MiniMax API
"""
import pytest
from unittest.mock import MagicMock, patch

from app.plugins.knowledge_base.schemas import SearchRequest
from app.plugins.knowledge_base.service import KnowledgeBaseService


@pytest.fixture
def mock_kb():
    """模拟一个属于 user_id=1 的知识库对象"""
    kb = MagicMock()
    kb.id = 7
    kb.user_id = 1
    return kb


@pytest.fixture
def mock_db(mock_kb):
    """模拟数据库会话：query().filter().first() 返回知识库"""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_kb
    return db


class TestKnowledgeBaseSearchDistance:
    """知识库搜索：distance 必填字段的兼容性"""

    def test_search_with_score_only_no_keyerror(self, mock_db):
        """vector_store 只返回 score 时，search 不应抛 KeyError，且 distance 由 score 反推"""
        # search_with_score 实际返回结构：{id, content, metadata, score}，无 distance
        raw_results = [
            {
                "id": "doc_1_chunk_0",
                "content": "MOM 系统的核心模块",
                "metadata": {
                    "document_id": 3,
                    "document_name": "MOM设计.md",
                    "chunk_index": 0,
                },
                "score": 0.8,
            }
        ]
        request = SearchRequest(query="MOM", top_k=5)

        with patch(
            "app.plugins.knowledge_base.service.vector_store.search_with_score",
            return_value=raw_results,
        ):
            resp = KnowledgeBaseService.search(mock_db, 1, 7, request)

        assert resp.total == 1
        item = resp.results[0]
        assert item.score == 0.8
        # score = 1/(1+distance) => distance = 1/0.8 - 1 = 0.25
        assert item.distance == pytest.approx(0.25)
        assert item.document_name == "MOM设计.md"
        assert item.chunk_index == 0

    def test_search_with_distance_passthrough(self, mock_db):
        """若结果自带 distance，应原样使用，不做反推"""
        raw_results = [
            {
                "id": "doc_2_chunk_0",
                "content": "WMS 仓储管理",
                "metadata": {},
                "score": 0.5,
                "distance": 1.0,
            }
        ]
        request = SearchRequest(query="WMS", top_k=5)

        with patch(
            "app.plugins.knowledge_base.service.vector_store.search_with_score",
            return_value=raw_results,
        ):
            resp = KnowledgeBaseService.search(mock_db, 1, 7, request)

        assert resp.results[0].distance == 1.0

    def test_search_zero_score_safe(self, mock_db):
        """score=0 时不应除零崩溃，distance 回退为 1.0"""
        raw_results = [
            {
                "id": "doc_3_chunk_0",
                "content": "零分结果",
                "metadata": {},
                "score": 0.0,
            }
        ]
        request = SearchRequest(query="test", top_k=5)

        with patch(
            "app.plugins.knowledge_base.service.vector_store.search_with_score",
            return_value=raw_results,
        ):
            resp = KnowledgeBaseService.search(mock_db, 1, 7, request)

        assert resp.results[0].distance == 1.0

    def test_search_empty_results(self, mock_db):
        """空结果应返回 total=0 且不报错"""
        request = SearchRequest(query="空", top_k=5)
        with patch(
            "app.plugins.knowledge_base.service.vector_store.search_with_score",
            return_value=[],
        ):
            resp = KnowledgeBaseService.search(mock_db, 1, 7, request)
        assert resp.total == 0
        assert resp.results == []
