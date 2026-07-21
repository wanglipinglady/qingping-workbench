"""
微信公众号写作助手 - 路由
定义写作助手相关的 API 端点
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.exceptions import unified_response
from app.plugins.user.models import User
from app.plugins.wechat_writer.schemas import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    SessionListResponse,
    SessionDetailResponse,
    StateTransitionRequest,
    StateResponse,
    MessageResponse,
)
from app.plugins.wechat_writer.service import wechat_writer_service

router = APIRouter(
    prefix="/wechat-writer",
    tags=["微信公众号写作助手"],
)


# ========== 会话 CRUD ==========

@router.post("/sessions", summary="创建写作会话")
async def create_session(
    request: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    创建新的写作会话

    - **topic**: 文章主题（1-500字符）
    - **title**: 会话标题（可选，默认用主题）
    """
    result = wechat_writer_service.create_session(db, current_user.id, request)
    return unified_response(data=SessionResponse.model_validate(result).model_dump())


@router.get("/sessions", summary="获取会话列表")
async def list_sessions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选: active/completed/archived"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的写作会话列表"""
    items, total = wechat_writer_service.get_session_list(
        db, current_user.id, page, page_size, status, keyword
    )
    data = SessionListResponse(
        items=[SessionResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )
    return unified_response(data=data.model_dump())


@router.get("/sessions/{session_id}", summary="获取会话详情")
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """根据 ID 获取会话详情"""
    result = wechat_writer_service.get_session(db, current_user.id, session_id)
    data = SessionDetailResponse.model_validate(result)
    # 补充统计数据
    data.material_count = len(result.materials) if result.materials else 0
    data.message_count = len(result.messages) if result.messages else 0
    data.output_count = len(result.outputs) if result.outputs else 0
    return unified_response(data=data.model_dump())


@router.put("/sessions/{session_id}", summary="更新会话")
async def update_session(
    session_id: int,
    request: SessionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新会话信息（标题、确认主题、状态等）"""
    result = wechat_writer_service.update_session(db, current_user.id, session_id, request)
    return unified_response(data=SessionResponse.model_validate(result).model_dump())


@router.delete("/sessions/{session_id}", summary="删除会话")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除写作会话及其所有关联数据"""
    wechat_writer_service.delete_session(db, current_user.id, session_id)
    return unified_response(message="删除成功")


# ========== 状态机操作 ==========

@router.post("/sessions/{session_id}/state", summary="状态操作（确认/重生成/回退）")
async def transition_state(
    session_id: int,
    request: StateTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    操作会话状态

    - **action**: confirm（确认前进）/ regenerate（重新生成）/ rollback（回退）/ switch_expert（切换专家）
    - **target_state**: 回退时的目标状态
    - **feedback**: 重新生成时的用户建议
    - **expert_type**: 切换专家时的专家类型
    """
    # T3 实现完整逻辑，当前返回占位响应
    return unified_response(data=StateResponse(
        session_id=session_id,
        current_state="idle",
        previous_state=None,
        message=f"状态操作 {request.action} 已接收（T3 实现）",
    ).model_dump())


# ========== 资料卡片 ==========

@router.get("/sessions/{session_id}/materials", summary="获取资料卡片列表")
async def list_materials(
    session_id: int,
    source_type: Optional[str] = Query(None, description="来源类型: obsidian/knowledge_base/web"),
    is_useful: Optional[bool] = Query(None, description="是否有用"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取会话的资料卡片列表"""
    items = wechat_writer_service.get_materials(db, current_user.id, session_id, source_type, is_useful)
    return unified_response(data=[i.__dict__ for i in items])


# ========== 输出版本 ==========

@router.get("/sessions/{session_id}/outputs", summary="获取输出版本列表")
async def list_outputs(
    session_id: int,
    step: Optional[str] = Query(None, description="步骤筛选: topic/research/outline/draft/polish"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取会话的输出版本列表"""
    items = wechat_writer_service.get_outputs(db, current_user.id, session_id, step)
    return unified_response(data=[i.__dict__ for i in items])


# ========== SSE 流式输出（T3 实现） ==========

@router.get("/sessions/{session_id}/stream", summary="SSE 流式输出（T3 实现）")
async def stream_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
):
    """SSE 流式输出 AI 生成过程（T3 实现）"""
    return unified_response(message="SSE 流式输出将在 T3 实现")
