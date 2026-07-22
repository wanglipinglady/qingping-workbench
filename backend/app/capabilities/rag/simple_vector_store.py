"""
纯 Python 向量存储（不依赖原生扩展）
基于 SQLite + NumPy 的轻量级向量数据库
完全兼容 Python 3.10-3.13，跨平台无依赖
"""
import os
import json
import time
import sqlite3
import hashlib
from typing import List, Dict, Any, Optional

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def _p(msg: str) -> None:
    print(msg, flush=True)


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """计算余弦相似度（纯 Python 实现，无需 numpy"""
    if HAS_NUMPY:
        a = np.array(vec_a)
        b = np.array(vec_b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
    else:
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a * a for a in vec_a) ** 0.5
        norm_b = sum(b * b for b in vec_b) ** 0.5
        return dot / (norm_a * norm_b + 1e-10)


class SimpleVectorStore:
    """
    纯 Python 向量存储实现
    使用 SQLite 存储文档和元数据，内存中计算余弦相似度
    适用于中小规模数据集（< 10万条向量）
    """

    def __init__(self, persist_dir: Optional[str] = None):
        from app.core.config import settings
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        os.makedirs(self.persist_dir, exist_ok=True)
        self.db_path = os.path.join(self.persist_dir, "simple_vector.db")
        _p(f"[SimpleVectorStore] 初始化, db_path={self.db_path}")
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                collection_name TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                vector BLOB NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_collection ON documents(collection_name)")
        conn.commit()
        conn.close()

    def _vector_to_blob(self, vector: List[float]) -> bytes:
        if HAS_NUMPY:
            return np.array(vector, dtype=np.float32).tobytes()
        else:
            return json.dumps(vector).encode('utf-8')

    def _blob_to_vector(self, blob: bytes) -> List[float]:
        if HAS_NUMPY:
            return np.frombuffer(blob, dtype=np.float32).tolist()
        else:
            return json.loads(blob.decode('utf-8'))

    def create_collection(self, name: str, metadata: Optional[Dict] = None):
        _p(f"[SimpleVectorStore] create_collection: {name}")
        return name  # collection 就是名字就是表中的 collection_name 字段

    def delete_collection(self, name: str) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM documents WHERE collection_name = ?", (name,))
        conn.commit()
        conn.close()
        _p(f"[SimpleVectorStore] 集合已删除: {name}")

    def get_collection(self, name: str):
        return name  # 简单返回名字，操作时直接用

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None,
        batch_size: int = 50,
    ) -> None:
        from app.capabilities.llm.minimax_client import minimax_client

        _p(f"[SimpleVectorStore] add_documents: collection={collection_name}, total_docs={len(documents)}")
        t_total = time.time()

        final_embeddings = embeddings
        if final_embeddings is None:
            _p(f"[SimpleVectorStore] 开始生成向量...")
            final_embeddings = minimax_client.embed(documents)
            _p(f"[SimpleVectorStore] 向量生成完成: {len(final_embeddings)} 个")

        final_metadatas = metadatas or [{} for _ in documents]

        assert len(documents) == len(ids) == len(final_metadatas) == len(final_embeddings)

        conn = sqlite3.connect(self.db_path)
        total_batches = (len(documents) + batch_size - 1) // batch_size
        _p(f"[SimpleVectorStore] 共 {total_batches} 批, 每批最多 {batch_size} 条")

        for batch_idx in range(total_batches):
            start = batch_idx * batch_size
            end = min(start + batch_size, len(documents))
            t0 = time.time()

            batch_data = []
            for i in range(start, end):
                batch_data.append((
                    ids[i],
                    collection_name,
                    documents[i],
                    json.dumps(final_metadatas[i], ensure_ascii=False),
                    self._vector_to_blob(final_embeddings[i]),
                ))

            conn.executemany(
                "INSERT OR REPLACE INTO documents (id, collection_name, content, metadata, vector) VALUES (?, ?, ?, ?, ?)",
                batch_data
            )
            conn.commit()
            _p(f"[SimpleVectorStore] 第 {batch_idx + 1}/{total_batches} 批写入完成 (耗时 {time.time()-t0:.3f}s)")

        conn.close()
        _p(f"[SimpleVectorStore] 全部写入完成: 共 {len(documents)} 条 (总耗时 {time.time()-t_total:.3f}s)")

    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        from app.capabilities.llm.minimax_client import minimax_client

        _p(f"[SimpleVectorStore] search: collection={collection_name}, query='{query[:50]}...', n_results={n_results}")

        # 生成查询向量
        query_embedding = minimax_client.embed([query], embed_type="query")
        if not query_embedding:
            return {"ids": [[]], "distances": [[]], "documents": [[]], "metadatas": [[]]}

        query_vec = query_embedding[0]

        # 从数据库读取所有该集合的向量
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT id, content, metadata, vector FROM documents WHERE collection_name = ?",
            (collection_name,)
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"ids": [[]], "distances": [[]], "documents": [[]], "metadatas": [[]]}

        _p(f"[SimpleVectorStore] 计算 {len(rows)} 条向量进行相似度排序...")

        # 计算相似度并排序
        scored = []
        for row in rows:
            doc_id, content, meta_str, vec_blob = row
            vec = self._blob_to_vector(vec_blob)
            sim = _cosine_similarity(query_vec, vec)
            scored.append((doc_id, content, meta_str, sim))

        # 按相似度降序排序
        scored.sort(key=lambda x: x[3], reverse=True)
        top = scored[:n_results]

        ids = [item[0] for item in top]
        documents = [item[1] for item in top]
        metadatas = [json.loads(item[2]) if item[2] else {} for item in top]
        distances = [1.0 - item[3] for item in top]  # 转成距离（1 - 相似度）

        _p(f"[SimpleVectorStore] 搜索完成: {len(ids)} 条结果")
        return {
            "ids": [ids],
            "distances": [distances],
            "documents": [documents],
            "metadatas": [metadatas],
        }

    def search_with_score(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        results = self.search(collection_name, query, n_results, where)
        ids_list = results.get("ids", [[]])[0]
        docs_list = results.get("documents", [[]])[0]
        metas_list = results.get("metadatas", [[]])[0]
        dist_list = results.get("distances", [[]])[0]

        formatted = []
        for i in range(len(ids_list)):
            distance = dist_list[i] if i < len(dist_list) else 1.0
            score = 1.0 - distance  # 直接是相似度
            formatted.append({
                "id": ids_list[i],
                "content": docs_list[i],
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
        conn = sqlite3.connect(self.db_path)
        if ids:
            placeholders = ",".join(["?"] * len(ids))
            conn.execute(
                f"DELETE FROM documents WHERE collection_name = ? AND id IN ({placeholders})",
                [collection_name] + ids
            )
            _p(f"[SimpleVectorStore] 删除文档: {len(ids)} 条")
        elif where:
            # 简单的 where 支持：按 metadata 中的字段匹配
            conditions = []
            params = [collection_name]
            for k, v in where.items():
                conditions.append("json_extract(metadata, ?) = ?")
                params.append(f"$.{k}")
                params.append(v)
            where_sql = " AND ".join(conditions)
            conn.execute(
                f"DELETE FROM documents WHERE collection_name = ? AND {where_sql}",
                params
            )
            _p(f"[SimpleVectorStore] 删除文档: by where={where}")
        conn.commit()
        conn.close()

    def count_documents(self, collection_name: str) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM documents WHERE collection_name = ?",
            (collection_name,)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def list_collections(self) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT DISTINCT collection_name FROM documents")
        names = [row[0] for row in cursor.fetchall()]
        conn.close()
        return names
