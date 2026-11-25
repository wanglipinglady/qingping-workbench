"""
选材剪藏服务层
"""
import re
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.plugins.clipper.extractor import (
    build_markdown,
    extract_article,
    fetch_html,
    normalize_url,
    url_fingerprint,
)
from app.plugins.clipper.models import Clipping
from app.plugins.clipper.schemas import (
    ClipRequest,
    ClippingDetailResponse,
    ClippingListResponse,
    ClippingResponse,
)
from app.plugins.knowledge_base.models import KnowledgeBase
from app.plugins.knowledge_base.schemas import KnowledgeBaseCreateRequest
from app.plugins.knowledge_base.service import kb_service

# 默认剪藏知识库名称
DEFAULT_KB_NAME = "剪藏"


class ClipperService:
    """剪藏服务"""

    @staticmethod
    def _get_or_create_default_kb(db: Session, user_id: int) -> int:
        """获取（或创建）用户的默认剪藏知识库"""
        kb = (
            db.query(KnowledgeBase)
            .filter(KnowledgeBase.user_id == user_id, KnowledgeBase.name == DEFAULT_KB_NAME)
            .first()
        )
        if kb:
            return kb.id

        created = kb_service.create_kb(
            db, user_id, KnowledgeBaseCreateRequest(name=DEFAULT_KB_NAME, description="网页剪藏自动归档")
        )
        return created.id

    @staticmethod
    def _safe_filename(title: str) -> str:
        """把标题转成安全的文件名"""
        name = re.sub(r"[\\/:*?\"<>|\n\r\t]", "_", title).strip()
        name = re.sub(r"\s+", " ", name)
        return (name[:80] or "clip") + ".md"

    @staticmethod
    def clip(db: Session, user_id: int, request: ClipRequest) -> ClippingDetailResponse:
        """
        剪藏一个网页：抓取 → 抽取正文 → 写入知识库 → 记录剪藏元数据

        同一用户重复剪藏同一链接时直接返回已有记录（幂等）。
        """
        normalized = normalize_url(request.url)
        fingerprint = url_fingerprint(normalized)

        existing = (
            db.query(Clipping)
            .filter(Clipping.user_id == user_id, Clipping.url_hash == fingerprint)
            .first()
        )
        if existing:
            return ClippingDetailResponse.model_validate(existing)

        kb_id = request.kb_id or ClipperService._get_or_create_default_kb(db, user_id)

        # 校验知识库归属
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise BusinessException(message="知识库不存在", code=2001, http_status=404)
        if kb.user_id != user_id:
            raise BusinessException(message="无权限操作该知识库", code=2002, http_status=403)

        tags: List[str] = [t.strip() for t in (request.tags or []) if t and t.strip()]
        category = (request.category or "").strip()

        try:
            html = fetch_html(normalized)
            article = extract_article(html, normalized)
            content_md = build_markdown(article, normalized, tags, category)

            doc = kb_service.upload_document(
                db,
                user_id,
                kb_id,
                ClipperService._safe_filename(article["title"]),
                content_md.encode("utf-8"),
            )
        except BusinessException as e:
            # 失败也留痕，便于在前端看到失败原因
            failed = Clipping(
                user_id=user_id,
                kb_id=kb_id,
                url=normalized,
                url_hash=fingerprint,
                title=normalized,
                tags=",".join(tags),
                category=category,
                status="failed",
                error_msg=e.message,
            )
            db.add(failed)
            db.commit()
            raise

        clipping = Clipping(
            user_id=user_id,
            kb_id=kb_id,
            document_id=doc.id,
            url=normalized,
            url_hash=fingerprint,
            title=article["title"][:255],
            site_name=article["site_name"],
            author=article.get("author", ""),
            summary=article["summary"],
            content_md=content_md,
            tags=",".join(tags),
            category=category,
            content_length=len(article["content_md"]),
            status="ready",
        )
        db.add(clipping)
        db.commit()
        db.refresh(clipping)

        return ClippingDetailResponse.model_validate(clipping)

    @staticmethod
    def list_items(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
    ) -> ClippingListResponse:
        """分页获取剪藏列表"""
        query = db.query(Clipping).filter(Clipping.user_id == user_id)
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                Clipping.title.like(like)
                | Clipping.summary.like(like)
                | Clipping.tags.like(like)
            )
        if category:
            query = query.filter(Clipping.category == category)

        total = query.count()
        items = (
            query.order_by(Clipping.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return ClippingListResponse(
            items=[ClippingResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def get_detail(db: Session, user_id: int, clipping_id: int) -> ClippingDetailResponse:
        """获取剪藏详情（含正文）"""
        item = (
            db.query(Clipping)
            .filter(Clipping.id == clipping_id, Clipping.user_id == user_id)
            .first()
        )
        if not item:
            raise BusinessException(message="剪藏记录不存在", code=3010, http_status=404)
        return ClippingDetailResponse.model_validate(item)

    @staticmethod
    def delete_item(db: Session, user_id: int, clipping_id: int) -> None:
        """删除剪藏记录，同时删除知识库中的对应文档与向量"""
        item = (
            db.query(Clipping)
            .filter(Clipping.id == clipping_id, Clipping.user_id == user_id)
            .first()
        )
        if not item:
            raise BusinessException(message="剪藏记录不存在", code=3010, http_status=404)

        if item.document_id:
            try:
                kb_service.delete_document(db, user_id, item.kb_id, item.document_id)
            except BusinessException:
                # 文档已被单独删除时忽略
                pass

        db.delete(item)
        db.commit()


clipper_service = ClipperService()
