"""
选材剪藏路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.exceptions import unified_response
from app.plugins.clipper.schemas import ClipRequest
from app.plugins.clipper.service import clipper_service
from app.plugins.user.models import User

router = APIRouter(prefix="/clipper", tags=["选材剪藏"])


@router.post("/clip", summary="剪藏网页到知识库")
async def clip_url(
    request: ClipRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    抓取网页正文并写入知识库

    - **url**: 网页链接（可省略 https://）
    - **kb_id**: 目标知识库，不传则写入默认「剪藏」知识库
    - **category**: 业务分类（可选）
    - **tags**: 标签列表（可选）

    同一链接重复剪藏会直接返回已有记录，不会重复入库。
    """
    result = clipper_service.clip(db, current_user.id, request)
    return unified_response(data=result.model_dump(), message="剪藏成功")


@router.get("/items", summary="获取剪藏列表")
async def list_clippings(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="标题/摘要/标签关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """分页获取当前用户的剪藏记录"""
    result = clipper_service.list_items(
        db, current_user.id, page, page_size, keyword, category
    )
    return unified_response(data=result.model_dump())


@router.get("/items/{clipping_id}", summary="获取剪藏详情")
async def get_clipping(
    clipping_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取剪藏详情，包含抽取后的 Markdown 正文"""
    result = clipper_service.get_detail(db, current_user.id, clipping_id)
    return unified_response(data=result.model_dump())


@router.delete("/items/{clipping_id}", summary="删除剪藏")
async def delete_clipping(
    clipping_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除剪藏记录，并同步删除知识库文档与向量"""
    clipper_service.delete_item(db, current_user.id, clipping_id)
    return unified_response(message="删除成功")
