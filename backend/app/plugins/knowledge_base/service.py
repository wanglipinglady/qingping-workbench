"""
知识库服务层
处理知识库和文档的业务逻辑
"""
import os
import uuid
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BusinessException
from app.plugins.knowledge_base.models import KnowledgeBase, Document
from app.plugins.knowledge_base.schemas import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseUpdateRequest,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
    DocumentResponse,
    DocumentListResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from app.capabilities.rag.text_splitter import TextSplitter
from app.capabilities.rag.vector_store import vector_store


# 支持的文件类型
SUPPORTED_FILE_TYPES = {".txt", ".md", ".markdown", ".pdf"}

# 文本分块器
text_splitter = TextSplitter(chunk_size=500, chunk_overlap=100)


class KnowledgeBaseService:
    """知识库服务类"""

    # ========== 知识库 CRUD ==========

    @staticmethod
    def create_kb(
        db: Session,
        user_id: int,
        request: KnowledgeBaseCreateRequest,
    ) -> KnowledgeBaseResponse:
        """
        创建知识库

        Args:
            db: 数据库会话
            user_id: 用户 ID
            request: 创建请求

        Returns:
            知识库响应
        """
        kb = KnowledgeBase(
            name=request.name,
            description=request.description or "",
            user_id=user_id,
            doc_count=0,
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)

        # 在 ChromaDB 中创建对应的集合
        collection_name = f"kb_{kb.id}"
        vector_store.create_collection(
            collection_name,
            metadata={"kb_id": kb.id, "user_id": user_id, "name": kb.name},
        )

        return KnowledgeBaseResponse.model_validate(kb)

    @staticmethod
    def get_kb_list(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
    ) -> KnowledgeBaseListResponse:
        """
        获取知识库列表

        Args:
            db: 数据库会话
            user_id: 用户 ID
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键词

        Returns:
            知识库列表响应
        """
        query = db.query(KnowledgeBase).filter(KnowledgeBase.user_id == user_id)

        # 关键词搜索
        if keyword:
            query = query.filter(KnowledgeBase.name.like(f"%{keyword}%"))

        # 总数
        total = query.count()

        # 分页
        items = (
            query.order_by(KnowledgeBase.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return KnowledgeBaseListResponse(
            items=[KnowledgeBaseResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def get_kb_detail(
        db: Session,
        user_id: int,
        kb_id: int,
    ) -> KnowledgeBaseResponse:
        """
        获取知识库详情

        Args:
            db: 数据库会话
            user_id: 用户 ID
            kb_id: 知识库 ID

        Returns:
            知识库响应

        Raises:
            BusinessException: 知识库不存在或无权限
        """
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise BusinessException(message="知识库不存在", code=2001, http_status=404)
        if kb.user_id != user_id:
            raise BusinessException(message="无权限访问该知识库", code=2002, http_status=403)

        return KnowledgeBaseResponse.model_validate(kb)

    @staticmethod
    def update_kb(
        db: Session,
        user_id: int,
        kb_id: int,
        request: KnowledgeBaseUpdateRequest,
    ) -> KnowledgeBaseResponse:
        """
        更新知识库

        Args:
            db: 数据库会话
            user_id: 用户 ID
            kb_id: 知识库 ID
            request: 更新请求

        Returns:
            更新后的知识库响应
        """
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise BusinessException(message="知识库不存在", code=2001, http_status=404)
        if kb.user_id != user_id:
            raise BusinessException(message="无权限操作该知识库", code=2002, http_status=403)

        if request.name is not None:
            kb.name = request.name
        if request.description is not None:
            kb.description = request.description

        db.commit()
        db.refresh(kb)

        return KnowledgeBaseResponse.model_validate(kb)

    @staticmethod
    def delete_kb(
        db: Session,
        user_id: int,
        kb_id: int,
    ) -> None:
        """
        删除知识库

        Args:
            db: 数据库会话
            user_id: 用户 ID
            kb_id: 知识库 ID
        """
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise BusinessException(message="知识库不存在", code=2001, http_status=404)
        if kb.user_id != user_id:
            raise BusinessException(message="无权限操作该知识库", code=2002, http_status=403)

        # 删除 ChromaDB 中的集合
        collection_name = f"kb_{kb_id}"
        vector_store.delete_collection(collection_name)

        # 删除数据库记录（级联删除文档）
        db.delete(kb)
        db.commit()

    # ========== 文档管理 ==========

    @staticmethod
    def _get_file_extension(filename: str) -> str:
        """获取文件扩展名（小写）"""
        _, ext = os.path.splitext(filename)
        return ext.lower()

    @staticmethod
    def _extract_text_from_file(file_path: str, file_type: str) -> str:
        """
        从文件中提取文本内容

        Args:
            file_path: 文件路径
            file_type: 文件类型（扩展名，如 .txt, .md, .pdf）

        Returns:
            提取的文本内容
        """
        if file_type in {".txt", ".md", ".markdown"}:
            # 文本类文件直接读取
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except UnicodeDecodeError:
                # 尝试用 gbk 编码读取
                with open(file_path, "r", encoding="gbk", errors="ignore") as f:
                    return f.read()

        elif file_type == ".pdf":
            # PDF 文件提取文本
            try:
                from pypdf import PdfReader

                reader = PdfReader(file_path)
                text_parts = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                return "\n\n".join(text_parts)
            except ImportError:
                raise BusinessException(
                    message="PDF 处理库未安装，请安装 pypdf",
                    code=2010,
                )
            except Exception as e:
                raise BusinessException(
                    message=f"PDF 解析失败: {str(e)}",
                    code=2011,
                )

        else:
            raise BusinessException(
                message=f"不支持的文件类型: {file_type}",
                code=2012,
            )

    @staticmethod
    def upload_document(
        db: Session,
        user_id: int,
        kb_id: int,
        filename: str,
        file_content: bytes,
    ) -> DocumentResponse:
        """
        上传并处理文档

        Args:
            db: 数据库会话
            user_id: 用户 ID
            kb_id: 知识库 ID
            filename: 文件名
            file_content: 文件内容（字节）

        Returns:
            文档响应
        """
        # 验证知识库权限
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise BusinessException(message="知识库不存在", code=2001, http_status=404)
        if kb.user_id != user_id:
            raise BusinessException(message="无权限操作该知识库", code=2002, http_status=403)

        # 检查文件类型
        file_ext = KnowledgeBaseService._get_file_extension(filename)
        if file_ext not in SUPPORTED_FILE_TYPES:
            raise BusinessException(
                message=f"不支持的文件类型，支持: {', '.join(sorted(SUPPORTED_FILE_TYPES))}",
                code=2012,
            )

        # 确保上传目录存在
        kb_upload_dir = os.path.join(settings.UPLOAD_DIR, f"kb_{kb_id}")
        os.makedirs(kb_upload_dir, exist_ok=True)

        # 生成保存文件名（避免重名）
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(kb_upload_dir, unique_name)

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)

        file_size = len(file_content)
        file_type = file_ext.lstrip(".")

        # 创建文档记录（处理中状态）
        doc = Document(
            kb_id=kb_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            status="processing",
            chunk_count=0,
        )
        db.add(doc)
        db.flush()  # 获取 doc.id

        try:
            # 提取文本
            text = KnowledgeBaseService._extract_text_from_file(file_path, file_ext)

            if not text.strip():
                doc.status = "failed"
                doc.error_msg = "文件内容为空或无法提取文本"
                db.commit()
                db.refresh(doc)
                return DocumentResponse.model_validate(doc)

            # 文本分块
            chunks = text_splitter.split_text(text)
            chunk_count = len(chunks)

            if chunk_count == 0:
                doc.status = "failed"
                doc.error_msg = "文本分块结果为空"
                db.commit()
                db.refresh(doc)
                return DocumentResponse.model_validate(doc)

            # 向量化并存入 ChromaDB
            collection_name = f"kb_{kb_id}"
            chunk_ids = [f"doc_{doc.id}_chunk_{i}" for i in range(chunk_count)]
            metadatas = [
                {
                    "document_id": doc.id,
                    "document_name": filename,
                    "chunk_index": i,
                    "kb_id": kb_id,
                }
                for i in range(chunk_count)
            ]

            vector_store.add_documents(
                collection_name=collection_name,
                documents=chunks,
                ids=chunk_ids,
                metadatas=metadatas,
            )

            # 更新文档状态
            doc.status = "ready"
            doc.chunk_count = chunk_count

            # 更新知识库文档计数
            kb.doc_count = kb.doc_count + 1

            db.commit()
            db.refresh(doc)

            return DocumentResponse.model_validate(doc)

        except BusinessException as e:
            # 业务异常，记录错误信息
            doc.status = "failed"
            doc.error_msg = e.message
            db.commit()
            db.refresh(doc)
            raise e

        except Exception as e:
            # 其他异常
            doc.status = "failed"
            doc.error_msg = str(e)
            db.commit()
            db.refresh(doc)
            raise BusinessException(
                message=f"文档处理失败: {str(e)}",
                code=2013,
            ) from e

    @staticmethod
    def get_document_list(
        db: Session,
        user_id: int,
        kb_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> DocumentListResponse:
        """
        获取文档列表

        Args:
            db: 数据库会话
            user_id: 用户 ID
            kb_id: 知识库 ID
            page: 页码
            page_size: 每页数量
            status: 状态筛选

        Returns:
            文档列表响应
        """
        # 验证知识库权限
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise BusinessException(message="知识库不存在", code=2001, http_status=404)
        if kb.user_id != user_id:
            raise BusinessException(message="无权限访问该知识库", code=2002, http_status=403)

        query = db.query(Document).filter(Document.kb_id == kb_id)

        if status:
            query = query.filter(Document.status == status)

        total = query.count()
        items = (
            query.order_by(Document.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return DocumentListResponse(
            items=[DocumentResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def delete_document(
        db: Session,
        user_id: int,
        kb_id: int,
        doc_id: int,
    ) -> None:
        """
        删除文档

        Args:
            db: 数据库会话
            user_id: 用户 ID
            kb_id: 知识库 ID
            doc_id: 文档 ID
        """
        # 验证知识库权限
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise BusinessException(message="知识库不存在", code=2001, http_status=404)
        if kb.user_id != user_id:
            raise BusinessException(message="无权限操作该知识库", code=2002, http_status=403)

        doc = db.query(Document).filter(Document.id == doc_id, Document.kb_id == kb_id).first()
        if not doc:
            raise BusinessException(message="文档不存在", code=2021, http_status=404)

        # 从 ChromaDB 中删除相关向量
        collection_name = f"kb_{kb_id}"
        try:
            # 按文档 ID 删除所有相关分块
            vector_store.delete_documents(
                collection_name=collection_name,
                where={"document_id": doc_id},
            )
        except Exception:
            # 删除向量失败不影响数据库删除
            pass

        # 删除文件（可选，保留文件用于后续重新处理）
        # 这里选择保留文件

        # 更新知识库文档计数
        if kb.doc_count > 0:
            kb.doc_count = kb.doc_count - 1

        # 删除数据库记录
        db.delete(doc)
        db.commit()

    # ========== 语义搜索 ==========

    @staticmethod
    def search(
        db: Session,
        user_id: int,
        kb_id: int,
        request: SearchRequest,
    ) -> SearchResponse:
        """
        在知识库中进行语义搜索

        Args:
            db: 数据库会话
            user_id: 用户 ID
            kb_id: 知识库 ID
            request: 搜索请求

        Returns:
            搜索响应
        """
        # 验证知识库权限
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise BusinessException(message="知识库不存在", code=2001, http_status=404)
        if kb.user_id != user_id:
            raise BusinessException(message="无权限访问该知识库", code=2002, http_status=403)

        # 在 ChromaDB 中搜索
        collection_name = f"kb_{kb_id}"
        results = vector_store.search_with_score(
            collection_name=collection_name,
            query=request.query,
            n_results=request.top_k,
        )

        # 格式化结果
        search_items = []
        for item in results:
            metadata = item.get("metadata", {})
            search_items.append(
                SearchResultItem(
                    id=item["id"],
                    content=item["content"],
                    score=item["score"],
                    distance=item["distance"],
                    document_id=metadata.get("document_id"),
                    document_name=metadata.get("document_name"),
                    chunk_index=metadata.get("chunk_index"),
                )
            )

        return SearchResponse(
            query=request.query,
            results=search_items,
            total=len(search_items),
        )


# 全局服务实例
kb_service = KnowledgeBaseService()
