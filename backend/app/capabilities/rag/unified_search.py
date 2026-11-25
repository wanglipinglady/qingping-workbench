"""
统一检索能力层
=============
把不同来源（知识库文档、Obsidian 笔记等）的向量检索结果归一化成统一结构，
并提供合并 / 去重 / 排序能力。

设计原则：
- 本层只依赖 vector_store，不反向依赖任何 plugin（避免架构耦合）。
- "某用户有哪些知识库集合"由调用方查询数据库后，通过 collection_specs 传入。
- 每条结果带 source / source_label 字段，下游可据此标注资料来源。
"""
from typing import Any, Dict, List

from app.capabilities.rag.vector_store import vector_store


def normalize_result(
    item: Dict[str, Any], source: str, source_label: str = ""
) -> Dict[str, Any]:
    """把 vector_store.search_with_score 的一条结果转成统一结构。"""
    metadata = item.get("metadata", {}) or {}
    path = (
        metadata.get("path")
        or metadata.get("document_name")
        or metadata.get("filename")
        or item.get("id", "")
    )
    return {
        "id": item.get("id", ""),
        "content": item.get("content", ""),
        "score": item.get("score", 0.0),
        "source": source,
        "source_label": source_label or source,
        "path": path,
        "title": metadata.get("title")
        or metadata.get("document_name")
        or metadata.get("filename")
        or "未知标题",
        "date": metadata.get("date", ""),
        "metadata": metadata,
    }


def norm_obsidian_result(item: Dict[str, Any]) -> Dict[str, Any]:
    """把 obsidian_reader.search 的结果转成统一结构（已带 path/title）。"""
    return {
        "id": item.get("path", ""),
        "content": item.get("content", ""),
        "score": item.get("score", 0.0),
        "source": "obsidian",
        "source_label": "Obsidian 笔记",
        "path": item.get("path", ""),
        "title": item.get("title", "未知标题"),
        "date": item.get("date", ""),
        "tags": item.get("tags", []),
        "metadata": {},
    }


def merge_results(
    result_groups: List[List[Dict[str, Any]]], top_k: int = 10
) -> List[Dict[str, Any]]:
    """合并多组检索结果：按 score 降序，按 (source, path) 去重，截断到 top_k。"""
    seen = set()
    merged: List[Dict[str, Any]] = []
    for group in result_groups:
        for r in group or []:
            key = (r.get("source", ""), r.get("path", "") or r.get("id", ""))
            if key in seen:
                continue
            seen.add(key)
            merged.append(r)
    merged.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return merged[:top_k]


def search_collections(
    collection_specs: List[Dict[str, Any]], query: str, top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    对多个向量集合检索并合并为统一结果。

    collection_specs 每项形如：
        {
          "collection_name": "kb_3",
          "source": "knowledge_base",
          "source_label": "MOM 项目资料库",
        }

    单个集合检索失败（如集合尚未创建）不影响其他来源。
    """
    group: List[Dict[str, Any]] = []
    for spec in collection_specs:
        name = spec.get("collection_name")
        if not name:
            continue
        try:
            results = vector_store.search_with_score(
                collection_name=name, query=query, n_results=top_k
            )
        except Exception:
            continue
        for item in results:
            group.append(
                normalize_result(
                    item,
                    source=spec.get("source", "unknown"),
                    source_label=spec.get("source_label", ""),
                )
            )
    return merge_results([group], top_k=top_k)
