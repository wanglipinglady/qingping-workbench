"""
知识库路由
定义知识库相关的 API 端点
"""
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.exceptions import unified_response
from app.plugins.user.models import User
from app.plugins.knowledge_base.schemas import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseUpdateRequest,
    SearchRequest,
)
from app.plugins.knowledge_base.service import kb_service

router = APIRouter(
    prefix="/knowledge-bases",
    tags=["知识库管理"],
)


# ========== 知识库 CRUD ==========

@router.post("", summary="创建知识库")
async def create_knowledge_base(
    request: KnowledgeBaseCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    创建新的知识库

    - **name**: 知识库名称（1-100字符）
    - **description**: 知识库描述（可选）
    """
    result = kb_service.create_kb(db, current_user.id, request)
    return unified_response(data=result.model_dump())


@router.get("", summary="获取知识库列表")
async def list_knowledge_bases(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的知识库列表，支持分页和关键词搜索"""
    result = kb_service.get_kb_list(db, current_user.id, page, page_size, keyword)
    return unified_response(data=result.model_dump())


@router.get("/{kb_id}", summary="获取知识库详情")
async def get_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """根据 ID 获取知识库详情"""
    result = kb_service.get_kb_detail(db, current_user.id, kb_id)
    return unified_response(data=result.model_dump())


@router.put("/{kb_id}", summary="更新知识库")
async def update_knowledge_base(
    kb_id: int,
    request: KnowledgeBaseUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    更新知识库信息

    - **name**: 新名称（可选）
    - **description**: 新描述（可选）
    """
    result = kb_service.update_kb(db, current_user.id, kb_id, request)
    return unified_response(data=result.model_dump())


@router.delete("/{kb_id}", summary="删除知识库")
async def delete_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除知识库及其所有文档和向量数据"""
    kb_service.delete_kb(db, current_user.id, kb_id)
    return unified_response(message="删除成功")


# ========== 文档管理 ==========

@router.post("/{kb_id}/documents/upload", summary="上传文档")
async def upload_document(
    kb_id: int,
    file: UploadFile = File(..., description="上传的文件（支持 .md, .txt, .pdf）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    上传文档到知识库

    支持的文件格式：.md, .txt, .pdf
    系统会自动提取文本、分块、向量化并存入向量数据库
    """
    # 读取文件内容
    file_content = await file.read()
    filename = file.filename or "unknown"

    result = kb_service.upload_document(
        db, current_user.id, kb_id, filename, file_content
    )
    return unified_response(data=result.model_dump())


@router.get("/{kb_id}/documents", summary="获取文档列表")
async def list_documents(
    kb_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选: processing/ready/failed"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取知识库中的文档列表"""
    result = kb_service.get_document_list(
        db, current_user.id, kb_id, page, page_size, status
    )
    return unified_response(data=result.model_dump())


@router.delete("/{kb_id}/documents/{doc_id}", summary="删除文档")
async def delete_document(
    kb_id: int,
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除文档及其对应的向量数据"""
    kb_service.delete_document(db, current_user.id, kb_id, doc_id)
    return unified_response(message="删除成功")


# ========== 语义搜索 ==========

@router.post("/{kb_id}/search", summary="语义搜索")
async def search_knowledge_base(
    kb_id: int,
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    在知识库中进行语义搜索

    - **query**: 搜索查询文本
    - **top_k**: 返回结果数量（默认 5，最多 50）

    返回相关的文本片段、来源文档、相似度分数等
    """
    result = kb_service.search(db, current_user.id, kb_id, request)
    return unified_response(data=result.model_dump())
