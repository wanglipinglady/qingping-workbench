"""
选材剪藏数据模式
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ClipRequest(BaseModel):
    """剪藏请求"""

    url: str = Field(..., min_length=8, max_length=2000, description="要剪藏的网页链接")
    kb_id: Optional[int] = Field(None, description="目标知识库 ID，不传则使用默认「剪藏」知识库")
    category: Optional[str] = Field("", max_length=50, description="业务分类，如 技术/行业/管理")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")


class ClippingResponse(BaseModel):
    """剪藏记录响应"""

    id: int
    url: str
    title: str
    site_name: str = ""
    author: str = ""
    summary: str = ""
    tags: str = ""
    category: str = ""
    content_length: int = 0
    kb_id: int
    document_id: Optional[int] = None
    status: str
    error_msg: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ClippingDetailResponse(ClippingResponse):
    """剪藏详情（含正文）"""

    content_md: str = ""


class ClippingListResponse(BaseModel):
    """剪藏列表响应"""

    items: List[ClippingResponse]
    total: int
    page: int
    page_size: int
