"""
知识库数据模式（Pydantic Schemas）
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ========== 知识库相关 ==========

class KnowledgeBaseCreateRequest(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., min_length=1, max_length=100, description="知识库名称")
    description: Optional[str] = Field("", description="知识库描述")


class KnowledgeBaseUpdateRequest(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: int
    name: str
    description: str
    user_id: int
    doc_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBaseListResponse(BaseModel):
    """知识库列表响应"""
    items: List[KnowledgeBaseResponse]
    total: int
    page: int
    page_size: int


# ========== 文档相关 ==========

class DocumentResponse(BaseModel):
    """文档响应"""
    id: int
    kb_id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_msg: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int


# ========== 搜索相关 ==========

class SearchRequest(BaseModel):
    """语义搜索请求"""
    query: str = Field(..., min_length=1, description="搜索查询文本")
    top_k: int = Field(5, ge=1, le=50, description="返回结果数量")


class SearchResultItem(BaseModel):
    """搜索结果项"""
    id: str
    content: str
    score: float
    distance: float
    document_id: Optional[int] = None
    document_name: Optional[str] = None
    chunk_index: Optional[int] = None


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str
    results: List[SearchResultItem]
    total: int
