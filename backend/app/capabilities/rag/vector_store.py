"""
向量存储模块
基于 ChromaDB 的向量数据库封装
"""
import os
import sys
import time
import threading
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.capabilities.llm.minimax_client import minimax_client


# ChromaDB 单批次写入超时时间（秒）—— 防止 Python 3.13/Windows 下挂起
CHROMA_BATCH_TIMEOUT = 30


def _p(msg: str) -> None:
    """打印并立即刷新输出，确保日志可见（解决 Windows/Python 3.13 下缓冲问题）"""
    print(msg, flush=True)


def _sanitize_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """清理元数据，确保所有值都是 ChromaDB 支持的类型 (str, int, float, bool)"""
    clean = {}
    for k, v in meta.items():
        if v is None:
            continue  # 跳过 None 值
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        else:
            # 其他类型转为字符串
            clean[k] = str(v)
    return clean


def _create_minimax_ef():
    """创建 MiniMax EmbeddingFunction（带 print 日志，确保一定有输出）"""
    from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

    class MiniMaxEmbeddingFunction(EmbeddingFunction):
        """使用 MiniMax API 的 Embedding 函数"""

        def __call__(self, input: Documents) -> Embeddings:
            texts = list(input)
            _p(f"[MiniMaxEF] ChromaDB 调用 embedding_function: {len(texts)} 段文本")
            if not texts:
                return []
            try:
                vectors = minimax_client.embed(texts)
                if vectors is None:
                    _p("[MiniMaxEF] embed 返回 None")
                    raise RuntimeError("MiniMax Embedding API 返回 None")
                _p(f"[MiniMaxEF] 完成: {len(vectors)} 个向量")
                return vectors
            except Exception as e:
                _p(f"[MiniMaxEF] 失败: {e}")
                raise

    return MiniMaxEmbeddingFunction()


def _run_with_timeout(func, timeout: float, description: str = "operation"):
    """
    在独立线程中执行函数，超时则抛出异常。
    跨平台兼容（Windows 不支持 signal.alarm）。

    Args:
        func: 要执行的函数（无参数）
        timeout: 超时时间（秒）
        description: 操作描述，用于错误信息

    Returns:
        func 的返回值

    Raises:
        TimeoutError: 超时
        Exception: func 抛出的任何异常
    """
    result_container = {"result": None, "exception": None, "done": False}

    def worker():
        try:
            result_container["result"] = func()
        except Exception as e:
            result_container["exception"] = e
        finally:
            result_container["done"] = True

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        # 超时了——线程还在跑，但我们不等了
        raise TimeoutError(
            f"ChromaDB 操作超时（{timeout}s）: {description}。"
            f"这通常是 Python 版本（当前 {sys.version.split()[0]}）与 ChromaDB 不兼容导致。"
            f"建议：1) 删除 data/chroma 目录后重试 2) 降级到 Python 3.10/3.11"
        )

    if result_container["exception"] is not None:
        raise result_container["exception"]

    return result_container["result"]


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
        _p(f"[VectorStore] 初始化 ChromaDB 客户端, persist_dir={self.persist_dir}")
        _p(f"[VectorStore] Python 版本: {sys.version.split()[0]}, ChromaDB 版本: {chromadb.__version__}")

        # 创建 ChromaDB 客户端（本地持久化模式）
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=False,
            ),
        )
        _p(f"[VectorStore] ChromaDB 客户端已创建")

        # 缓存 embedding_function，避免每次创建集合都重新实例化
        self._ef = _create_minimax_ef()

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
        _p(f"[VectorStore] create_collection: {name}")
        t0 = time.time()
        # 注意：ChromaDB 新版本（Python 3.13 下）不允许 metadata 为空字典
        # 必须传入 None 或非空字典
        # 同时必须指定 embedding_function，否则 ChromaDB 会尝试加载默认的
        # ONNXMiniLM_L6_V2，它依赖 onnxruntime（在 Python 3.13 下有 DLL 问题）
        collection = self.client.get_or_create_collection(
            name=name,
            metadata=metadata if metadata else None,
            embedding_function=self._ef,
        )
        _p(f"[VectorStore] 集合已创建/获取: {name} (耗时 {time.time()-t0:.3f}s, 当前 {collection.count()} 条)")
        return collection

    def delete_collection(self, name: str) -> None:
        """
        删除集合

        Args:
            name: 集合名称
        """
        try:
            self.client.delete_collection(name=name)
            _p(f"[VectorStore] 集合已删除: {name}")
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
            return self.client.get_collection(name=name, embedding_function=self._ef)
        except Exception:
            return None

    def list_collections(self) -> List[str]:
        """
        列出所有集合

        Returns:
            集合名称列表
        """
        return [col.name for col in self.client.list_collections()]

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None,
        batch_size: int = 5,
    ) -> None:
        """
        向集合中添加文档（分批写入，避免单次请求过大）

        Args:
            collection_name: 集合名称
            documents: 文档内容列表
            ids: 文档 ID 列表
            metadatas: 元数据列表（可选）
            embeddings: 向量列表（可选，不提供则自动向量化）
            batch_size: 每批写入的文档数量（默认 5）
        """
        _p(f"[VectorStore] add_documents: collection={collection_name}, total_docs={len(documents)}, batch_size={batch_size}")
        t_total = time.time()

        # 1. 创建/获取集合
        _p(f"[VectorStore] 步骤1: 获取集合...")
        collection = self.create_collection(collection_name)

        # 2. 生成向量（如果没提供）
        _p(f"[VectorStore] 步骤2: 向量化...")
        final_embeddings = embeddings
        if final_embeddings is None:
            _p(f"[VectorStore] 开始生成向量...")
            final_embeddings = minimax_client.embed(documents)
            _p(f"[VectorStore] 向量生成完成: {len(final_embeddings)} 个")
        else:
            _p(f"[VectorStore] 使用外部传入的 embeddings: {len(final_embeddings)} 个")

        # 3. 准备元数据（清理类型）
        _p(f"[VectorStore] 步骤3: 准备元数据...")
        raw_metadatas = metadatas or [{} for _ in documents]
        final_metadatas = [_sanitize_metadata(m) for m in raw_metadatas]
        _p(f"[VectorStore] 元数据已清理: {len(final_metadatas)} 条")

        # 校验长度一致
        assert len(documents) == len(ids) == len(final_metadatas) == len(final_embeddings), \
            f"长度不一致: docs={len(documents)}, ids={len(ids)}, metas={len(final_metadatas)}, embs={len(final_embeddings)}"

        # 4. 分批写入 ChromaDB（带超时保护）
        _p(f"[VectorStore] 准备写入 ChromaDB: docs={len(documents)}, embeddings={len(final_embeddings)}, metadatas={len(final_metadatas)}")
        total_batches = (len(documents) + batch_size - 1) // batch_size
        _p(f"[VectorStore] 共 {total_batches} 批, 每批最多 {batch_size} 条, 单批超时 {CHROMA_BATCH_TIMEOUT}s")

        for batch_idx in range(total_batches):
            start = batch_idx * batch_size
            end = min(start + batch_size, len(documents))

            batch_docs = documents[start:end]
            batch_ids = ids[start:end]
            batch_metas = final_metadatas[start:end]
            batch_embs = final_embeddings[start:end]

            _p(f"[VectorStore] 写入第 {batch_idx + 1}/{total_batches} 批: {len(batch_docs)} 条 (IDs: {batch_ids[0]}...)")
            t0 = time.time()
            try:
                # 用超时保护调用 collection.add()
                def _add_batch():
                    collection.add(
                        documents=batch_docs,
                        ids=batch_ids,
                        metadatas=batch_metas,
                        embeddings=batch_embs,
                    )

                _run_with_timeout(
                    _add_batch,
                    timeout=CHROMA_BATCH_TIMEOUT,
                    description=f"写入第 {batch_idx + 1}/{total_batches} 批 ({len(batch_docs)} 条)",
                )
                _p(f"[VectorStore] 第 {batch_idx + 1}/{total_batches} 批写入完成 (耗时 {time.time()-t0:.3f}s)")
            except TimeoutError as e:
                _p(f"[VectorStore] 第 {batch_idx + 1} 批写入超时: {e}")
                raise
            except Exception as e:
                _p(f"[VectorStore] 第 {batch_idx + 1} 批写入失败: {e}")
                import traceback
                traceback.print_exc()
                raise

        _p(f"[VectorStore] 全部写入完成: 共 {len(documents)} 条 (总耗时 {time.time()-t_total:.3f}s)")

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
        _p(f"[VectorStore] search: collection={collection_name}, query='{query[:50]}...', n_results={n_results}")
        collection = self.get_collection(collection_name)
        if collection is None:
            _p(f"[VectorStore] 集合不存在: {collection_name}")
            return {
                "ids": [[]],
                "distances": [[]],
                "documents": [[]],
                "metadatas": [[]],
            }

        # 生成查询向量
        _p(f"[VectorStore] 生成查询向量...")
        query_embedding = minimax_client.embed([query], embed_type="query")
        if not query_embedding:
            _p("[VectorStore] 查询向量生成失败")
            return {
                "ids": [[]],
                "distances": [[]],
                "documents": [[]],
                "metadatas": [[]],
            }
        _p(f"[VectorStore] 查询向量生成完成")

        _p(f"[VectorStore] 执行搜索...")
        t0 = time.time()
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where=where,
        )
        _p(f"[VectorStore] 搜索完成: {len(results.get('ids', [[]])[0])} 条结果 (耗时 {time.time()-t0:.3f}s)")
        return results

    def search_with_score(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        语义搜索（带相似度分数，返回格式化列表）

        Args:
            collection_name: 集合名称
            query: 查询文本
            n_results: 返回结果数量
            where: 过滤条件（可选）

        Returns:
            [{content, metadata, score}, ...] 格式的结果列表
        """
        results = self.search(collection_name, query, n_results, where)

        ids_list = results.get("ids", [[]])[0]
        docs_list = results.get("documents", [[]])[0]
        metas_list = results.get("metadatas", [[]])[0]
        dist_list = results.get("distances", [[]])[0]

        formatted = []
        for i in range(len(ids_list)):
            # ChromaDB 返回的是距离 (L2 或 cosine distance)，转为相似度分数
            distance = dist_list[i] if i < len(dist_list) else 1.0
            # 简单转换: score = 1 / (1 + distance)，范围 (0, 1]
            score = 1.0 / (1.0 + distance) if distance >= 0 else 1.0

            formatted.append({
                "id": ids_list[i] if i < len(ids_list) else "",
                "content": docs_list[i] if i < len(docs_list) else "",
                "metadata": metas_list[i] if i < len(metas_list) else {},
                "score": score,
            })

        return formatted

    def delete_documents(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        从集合中删除文档

        Args:
            collection_name: 集合名称
            ids: 要删除的文档 ID 列表（与 where 二选一）
            where: 过滤条件（与 ids 二选一）
        """
        collection = self.get_collection(collection_name)
        if collection is None:
            return

        if ids:
            _p(f"[VectorStore] 删除文档: {len(ids)} 条 (by ids)")
            collection.delete(ids=ids)
        elif where:
            _p(f"[VectorStore] 删除文档: by where={where}")
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


# 全局单例
vector_store = VectorStore()
