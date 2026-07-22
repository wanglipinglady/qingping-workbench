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
from app.plugins.wechat_writer.obsidian_reader import obsidian_reader

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

@router.post("/sessions/{session_id}/start", summary="开始写作（从 idle 进入选题确认）")
async def start_writing(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    开始写作流程：从 idle 进入选题确认阶段，调用选题编辑专家分析主题

    返回选题编辑的分析结果（选题确认单）
    """
    result = wechat_writer_service.start_topic_confirm(db, current_user.id, session_id)
    return unified_response(data=result)


@router.post("/sessions/{session_id}/confirm", summary="确认当前状态，进入下一步")
async def confirm_current_state(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    确认当前状态的输出，进入下一个状态

    - 在 topic_confirm 状态：保存选题确认单为 confirmed_topic，进入 research
    - 在 research 状态：确认资料卡片，进入 outline
    - 在 outline 状态：确认大纲，进入 draft
    - 在 draft 状态：确认初稿，进入 polish
    - 在 polish 状态：确认润色稿，进入 done
    """
    result = wechat_writer_service.confirm_state(db, current_user.id, session_id)
    return unified_response(data=result)


@router.post("/sessions/{session_id}/regenerate", summary="重新生成当前步骤的输出")
async def regenerate_current_step(
    session_id: int,
    request: StateTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    重新生成当前步骤的输出

    - **feedback**: 用户填写的修改建议（可选，留空则 AI 自动换角度）
    """
    result = wechat_writer_service.regenerate(
        db, current_user.id, session_id, feedback=request.feedback
    )
    return unified_response(data=result)


@router.post("/sessions/{session_id}/rollback", summary="回退到指定状态")
async def rollback_to_state(
    session_id: int,
    request: StateTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    回退到指定的前置状态

    - **target_state**: 目标状态（必须是当前状态的前置状态）
    - **feedback**: 回退原因（可选）
    """
    if not request.target_state:
        raise ValueError("target_state 不能为空")
    result = wechat_writer_service.rollback(
        db, current_user.id, session_id,
        target_state=request.target_state.value if hasattr(request.target_state, 'value') else request.target_state,
        reason=request.feedback or "",
    )
    return unified_response(data=result)


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


# ========== Obsidian 同步 ==========

@router.post("/obsidian/sync", summary="手动触发 Obsidian 同步")
async def sync_obsidian(
    current_user: User = Depends(get_current_user),
):
    """
    手动触发 Obsidian Vault 同步

    执行增量同步：
    - 扫描 Vault 中所有 .md 文件
    - 解析 Frontmatter 和标签
    - 新增/修改的文件向量化后存入 ChromaDB
    - 删除的文件从向量库移除

    返回同步结果统计
    """
    result = obsidian_reader.sync(current_user.id)
    return unified_response(data=result)


@router.get("/obsidian/status", summary="获取 Obsidian 同步状态")
async def get_obsidian_status(
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户的 Obsidian 同步状态

    返回：
    - vault_path: Vault 路径
    - vault_exists: Vault 是否存在
    - last_sync_time: 上次同步时间戳（0 表示未同步）
    - total_notes: 已索引的笔记数量
    - total_chunks: 向量分块总数
    """
    result = obsidian_reader.get_sync_status(current_user.id)
    return unified_response(data=result)


@router.post("/obsidian/search", summary="在 Obsidian 笔记中语义搜索")
async def search_obsidian(
    request: dict,
    current_user: User = Depends(get_current_user),
):
    """
    在 Obsidian 笔记中进行语义搜索

    - **query**: 搜索关键词（必填）
    - **top_k**: 返回结果数量（可选，默认 5）
    - **tags**: 按标签过滤（可选，列表）
    """
    query = request.get("query", "")
    if not query:
        raise ValueError("query 不能为空")
    top_k = request.get("top_k", 5)
    tags = request.get("tags")
    results = obsidian_reader.search(current_user.id, query, top_k=top_k, tags=tags)
    return unified_response(data=results)
