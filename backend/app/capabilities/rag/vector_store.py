"""
向量存储模块
基于 ChromaDB 的向量数据库封装
"""
import os
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.capabilities.llm.minimax_client import minimax_client


class VectorStore:
    """
    ChromaDB 向量存储封装
    提供集合创建、文档添加、语义搜索等功能
    """

    def __init__(self, persist_dir: Optional[str] = None):
        """
        初始化向量存储

        Args:
            persist_dir: 持久化目录，默认从配置读取
        """
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR

        # 确保持久化目录存在
        os.makedirs(self.persist_dir, exist_ok=True)

        # 创建 ChromaDB 客户端（本地持久化模式）
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=False,
            ),
        )

    def create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> chromadb.Collection:
        """
        创建或获取集合

        Args:
            name: 集合名称
            metadata: 集合元数据

        Returns:
            ChromaDB 集合对象
        """
        # 使用 get_or_create 避免重复创建
        # 注意：ChromaDB 新版本（Python 3.13 下）不允许 metadata 为空字典
        # 必须传入 None 或非空字典
        # 同时必须指定 embedding_function，否则 ChromaDB 会尝试加载默认的
        # ONNXMiniLM_L6_V2，它依赖 onnxruntime（在 Python 3.13 下有 DLL 问题）
        # 我们始终使用 MiniMax API 生成向量，所以这里传一个空函数即可
        from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

        class NoOpEmbeddingFunction(EmbeddingFunction):
            """空实现的 Embedding 函数，我们始终自己传 embeddings"""

            def __call__(self, input: Documents) -> Embeddings:
                # 这个函数理论上不会被调用，因为我们总是传 embeddings
                raise RuntimeError("ChromaDB 不应该调用这个函数，因为我们总是传 embeddings")

        collection = self.client.get_or_create_collection(
            name=name,
            metadata=metadata if metadata else None,
            embedding_function=NoOpEmbeddingFunction(),
        )
        return collection

    def delete_collection(self, name: str) -> None:
        """
        删除集合

        Args:
            name: 集合名称
        """
        try:
            self.client.delete_collection(name=name)
        except Exception:
            # 集合不存在时忽略
            pass

    def get_collection(self, name: str) -> Optional[chromadb.Collection]:
        """
        获取集合

        Args:
            name: 集合名称

        Returns:
            集合对象，不存在则返回 None
        """
        try:
            return self.client.get_collection(name=name)
        except Exception:
            return None

    def list_collections(self) -> List[str]:
        """
        列出所有集合名称

        Returns:
            集合名称列表
        """
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception:
            return []

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None,
    ) -> None:
        """
        向集合中添加文档

        Args:
            collection_name: 集合名称
            documents: 文档内容列表
            ids: 文档 ID 列表
            metadatas: 元数据列表（可选）
            embeddings: 向量列表（可选，不提供则自动向量化）
        """
        collection = self.create_collection(collection_name)

        # 如果没有提供向量，使用 MiniMax API 生成
        if embeddings is None:
            embeddings = minimax_client.embed(documents)

        # ChromaDB 要求所有列表长度一致
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas or [{} for _ in documents],
            embeddings=embeddings,
        )

    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        语义搜索

        Args:
            collection_name: 集合名称
            query: 查询文本
            n_results: 返回结果数量
            where: 过滤条件（可选）

        Returns:
            搜索结果字典，包含 ids、distances、documents、metadatas
        """
        collection = self.get_collection(collection_name)
        if collection is None:
            return {
                "ids": [[]],
                "distances": [[]],
                "documents": [[]],
                "metadatas": [[]],
            }

        # 生成查询向量
        query_embedding = minimax_client.embed([query])

        # 执行搜索
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where=where,
        )

        return results

    def search_with_score(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        语义搜索，返回格式化的结果列表（带相似度分数）

        Args:
            collection_name: 集合名称
            query: 查询文本
            n_results: 返回结果数量
            where: 过滤条件

        Returns:
            结果列表，每项包含 id、content、metadata、score（相似度 0-1）
        """
        results = self.search(
            collection_name=collection_name,
            query=query,
            n_results=n_results,
            where=where,
        )

        formatted = []
        if results.get("ids") and len(results["ids"]) > 0:
            ids = results["ids"][0]
            distances = results["distances"][0] if results.get("distances") else []
            documents = results["documents"][0] if results.get("documents") else []
            metadatas = results["metadatas"][0] if results.get("metadatas") else []

            for i in range(len(ids)):
                # ChromaDB 返回的是距离，转换为相似度分数
                distance = distances[i] if i < len(distances) else 0
                # 使用 1 / (1 + distance) 转换为 0-1 的相似度
                score = 1.0 / (1.0 + distance) if distance >= 0 else 0.0

                formatted.append({
                    "id": ids[i],
                    "content": documents[i] if i < len(documents) else "",
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "score": round(score, 4),
                    "distance": round(distance, 4),
                })

        return formatted

    def delete_documents(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        删除集合中的文档

        Args:
            collection_name: 集合名称
            ids: 要删除的文档 ID 列表
            where: 按条件删除
        """
        collection = self.get_collection(collection_name)
        if collection is None:
            return

        if ids:
            collection.delete(ids=ids)
        elif where:
            collection.delete(where=where)

    def count_documents(self, collection_name: str) -> int:
        """
        统计集合中的文档数量

        Args:
            collection_name: 集合名称

        Returns:
            文档数量
        """
        collection = self.get_collection(collection_name)
        if collection is None:
            return 0
        return collection.count()


# 全局向量存储实例
vector_store = VectorStore()
