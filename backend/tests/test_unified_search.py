"""
统一检索能力层单元测试
覆盖：多集合检索合并、去重、按 score 排序、source 标注、单集合失败容错
注意：mock 向量库，不依赖真实 ChromaDB
"""
import pytest
from unittest.mock import patch

from app.capabilities.rag.unified_search import (
    search_collections,
    merge_results,
    norm_obsidian_result,
    normalize_result,
)


class TestMergeResults:
    """合并 / 去重 / 排序"""

    def test_merge_sorts_by_score_desc(self):
        groups = [
            [
                {"path": "a.md", "source": "obsidian", "score": 0.5, "content": "A"},
                {"path": "b.md", "source": "obsidian", "score": 0.9, "content": "B"},
            ],
            [
                {"path": "c.md", "source": "knowledge_base", "score": 0.7, "content": "C"},
            ],
        ]
        merged = merge_results(groups, top_k=10)
        assert [r["path"] for r in merged] == ["b.md", "c.md", "a.md"]

    def test_dedup_by_source_and_path(self):
        """同来源同路径去重；不同来源同路径保留（如 Obsidian 与知识库都有 MOM.md）"""
        groups = [
            [
                {"path": "MOM.md", "source": "obsidian", "score": 0.9, "content": "笔记"},
                {"path": "MOM.md", "source": "obsidian", "score": 0.6, "content": "笔记重复"},
            ],
            [
                {"path": "MOM.md", "source": "knowledge_base", "score": 0.8, "content": "文档"},
            ],
        ]
        merged = merge_results(groups, top_k=10)
        assert len(merged) == 2
        assert {r["source"] for r in merged} == {"obsidian", "knowledge_base"}

    def test_top_k_limit(self):
        group = [[{"path": f"d{i}.md", "source": "obsidian", "score": 0.9 - i * 0.01, "content": ""} for i in range(10)]]
        merged = merge_results(group, top_k=3)
        assert len(merged) == 3


class TestSearchCollections:
    """多集合统一检索"""

    def test_search_multiple_collections_with_source_label(self):
        specs = [
            {"collection_name": "kb_7", "source": "knowledge_base", "source_label": "知识库: MOM库"},
            {"collection_name": "kb_9", "source": "knowledge_base", "source_label": "知识库: WMS库"},
        ]

        def fake_search(collection_name, query, n_results):
            if collection_name == "kb_7":
                return [
                    {
                        "id": "doc_1_chunk_0",
                        "content": "MOM 内容",
                        "metadata": {"document_name": "MOM设计.md"},
                        "score": 0.8,
                    }
                ]
            return [
                {
                    "id": "doc_2_chunk_0",
                    "content": "WMS 内容",
                    "metadata": {"document_name": "WMS设计.md"},
                    "score": 0.6,
                }
            ]

        with patch(
            "app.capabilities.rag.unified_search.vector_store.search_with_score",
            side_effect=fake_search,
        ):
            results = search_collections(specs, "仓储", top_k=5)

        assert len(results) == 2
        assert results[0]["score"] >= results[1]["score"]
        assert results[0]["source"] == "knowledge_base"
        assert results[0]["source_label"] == "知识库: MOM库"
        assert results[0]["title"] == "MOM设计.md"

    def test_single_collection_failure_does_not_break(self):
        """一个集合检索失败（如不存在）不影响其他集合"""
        specs = [
            {"collection_name": "missing_kb", "source": "knowledge_base", "source_label": "空库"},
            {"collection_name": "kb_7", "source": "knowledge_base", "source_label": "MOM库"},
        ]

        def fake_search(collection_name, query, n_results):
            if collection_name == "missing_kb":
                raise RuntimeError("collection not found")
            return [
                {
                    "id": "x",
                    "content": "ok",
                    "metadata": {},
                    "score": 0.7,
                }
            ]

        with patch(
            "app.capabilities.rag.unified_search.vector_store.search_with_score",
            side_effect=fake_search,
        ):
            results = search_collections(specs, "test", top_k=5)

        assert len(results) == 1
        assert results[0]["content"] == "ok"

    def test_normalize_obsidian_result(self):
        raw = {
            "path": "notes/ai.md",
            "title": "AI 入门",
            "content": "内容",
            "score": 0.95,
            "date": "2026-01-15",
        }
        normalized = norm_obsidian_result(raw)
        assert normalized["source"] == "obsidian"
        assert normalized["path"] == "notes/ai.md"
        assert normalized["title"] == "AI 入门"
