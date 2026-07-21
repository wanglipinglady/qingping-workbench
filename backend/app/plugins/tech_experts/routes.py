"""技术专家组 API 路由

定义所有 HTTP 接口，包括：
- 会话管理（CRUD）
- 对话交互（同步 + 流式）
- 状态控制（确认/回退/切换）
- 专家信息
- 验收标准（预留）
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.plugins.tech_experts.service import TechExpertService
from app.plugins.tech_experts.schemas import (
    ApiResponse,
    SessionCreateRequest,
    ChatRequest,
    RollbackRequest,
    SwitchExpertRequest,
    AcceptanceCriteriaRequest,
)
from app.plugins.tech_experts.experts import get_all_experts
from app.plugins.tech_experts.state_machine import STATE_LABELS


router = APIRouter(
    prefix="/tech-experts",
    tags=["技术专家组"],
)


# =============================================================================
# 依赖注入辅助
# =============================================================================

def get_service(db: Session = Depends(get_db)) -> TechExpertService:
    """获取技术专家组服务实例"""
    return TechExpertService(db)


def get_session_or_404(
    session_id: int,
    user_id: int,
    service: TechExpertService,
):
    """获取会话，不存在则抛出 404"""
    session = service.get_session(session_id, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在或无权限访问",
        )
    return session


# =============================================================================
# 1. 会话管理接口
# =============================================================================

@router.get("/sessions", response_model=ApiResponse)
async def list_sessions(
    current_user=Depends(get_current_user),
    service: TechExpertService = Depends(get_service),
):
    """获取当前用户的会话列表

    返回用户创建的所有技术专家组会话，按更新时间倒序排列。
    """
    sessions = service.list_sessions(current_user.id)
    data = [
        {
            "id": s.id,
            "title": s.title,
            "current_state": s.current_state,
            "current_state_label": STATE_LABELS.get(s.current_state, s.current_state),
            "iteration_count": s.iteration_count,
            "status": s.status,
            "total_tokens": s.total_tokens,
            "updated_at": s.updated_at.isoformat() if s.updated_at else "",
        }
        for s in sessions
    ]
    return ApiResponse(data={"items": data, "total": len(data)}, message="获取会话列表成功")


@router.post("/sessions", response_model=ApiResponse)
async def create_session(
    req: SessionCreateRequest,
    current_user=Depends(get_current_user),
    service: TechExpertService = Depends(get_service),
):
    """创建新的技术专家组会话

    可以选择传入初始需求消息，创建后可直接开始对话。
    """
    session = service.create_session(
        user_id=current_user.id,
        title=req.title,
        initial_message=req.initial_message,
    )
    return ApiResponse(
        data={
            "id": session.id,
            "title": session.title,
            "current_state": session.current_state,
            "current_state_label": STATE_LABELS.get(session.current_state, session.current_state),
            "status": session.status,
            "created_at": session.created_at.isoformat() if session.created_at else "",
        },
        message="会话创建成功",
        code=0,
    )


@router.get("/sessions/{session_id}", response_model=ApiResponse)
async def get_session_detail(
    session_id: int,
    current_user=Depends(get_current_user),
    service: TechExpertService = Depends(get_service),
):
    """获取会话详情

    返回会话的完整信息，包括当前状态、迭代轮次等。
    """
    session = get_session_or_404(session_id, current_user.id, service)
    return ApiResponse(
        data={
            "id": session.id,
            "user_id": session.user_id,
            "title": session.title,
            "current_state": session.current_state,
            "current_state_label": STATE_LABELS.get(session.current_state, session.current_state),
            "iteration_count": session.iteration_count,
            "max_iterations": session.max_iterations,
            "status": session.status,
            "total_tokens": session.total_tokens,
            "acceptance_criteria": session.acceptance_criteria,
            "created_at": session.created_at.isoformat() if session.created_at else "",
            "updated_at": session.updated_at.isoformat() if session.updated_at else "",
        },
        message="获取会话详情成功",
    )


@router.delete("/sessions/{session_id}", response_model=ApiResponse)
async def delete_session(
    session_id: int,
    current_user=Depends(get_current_user),
    service: TechExpertService = Depends(get_service),
):
    """删除指定会话

    同时删除该会话的所有消息和状态转移记录。
    """
    success = service.delete_session(session_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在或无权限访问",
        )
    return ApiResponse(message="会话删除成功")


@router.get("/sessions/{session_id}/messages", response_model=ApiResponse)
async def get_session_messages(
    session_id: int,
    current_user=Depends(get_current_user),
    service: TechExpertService = Depends(get_service),
):
    """获取会话的消息列表

    返回会话中所有消息，按时间正序排列。
    """
    get_session_or_404(session_id, current_user.id, service)
    messages = service.get_messages(session_id, current_user.id)
    data = [
        {
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role,
            "expert_type": m.expert_type,
            "state_label": m.state_label,
            "iteration": m.iteration,
            "content": m.content,
            "token_usage": m.token_usage,
            "created_at": m.created_at.isoformat() if m.created_at else "",
        }
        for m in messages
    ]
    return ApiResponse(data=data, message="获取消息列表成功")


@router.get("/sessions/{session_id}/state", response_model=ApiResponse)
async def get_session_state(
    session_id: int,
    current_user=Depends(get_current_user),
    service: TechExpertService = Depends(get_service),
):
    """获取会话当前状态信息

    返回当前状态、对应专家、可操作选项等信息。
    """
    session = get_session_or_404(session_id, current_user.id, service)
    state_info = service.get_state_info(session)
    return ApiResponse(data=state_info, message="获取状态信息成功")


# =============================================================================
# 2. 对话交互接口
# =============================================================================

@router.post("/sessions/{session_id}/chat", response_model=ApiResponse)
async def chat(
    session_id: int,
    req: ChatRequest,
    current_user=Depends(get_current_user),
    service: TechExpertService = Depends(get_service),
):
    """发送消息（同步）

    触发当前状态对应的专家生成回复。
    首次对话会自动从 idle 进入 arch_design 状态。
    """
    session = get_session_or_404(session_id, current_user.id, service)

    # 检查会话状态
    if session.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="会话已完成，如需继续请重新创建或回退状态",
        )

    try:
        result = service.chat(session, req.message)
        return ApiResponse(data=result, message="对话成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"对话失败: {str(e)}",
        )


@router.post("/sessions/{session_id}/chat/stream")
async def chat_stream(
    session_id: int,
    req: ChatRequest,
    current_user=Depends(get_current_user),
    service: TechExpertService = Depends(get_service),
):
    """发送消息（SSE 流式输出）

    以 SSE 事件流的形式返回专家回复，支持实时展示。
    事件类型包括：state_enter、message_chunk、message_end、state_pause、error。
    """
    session = get_session_or_404(session_id, current_user.id, service)

    # 检查会话状态
    if session.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="会话已完成，如需继续请重新创建或回退状态",
        )

    return StreamingResponse(
        service.chat_stream(session, req.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# =============================================================================
# 3. 状态控制接口
# =============================================================================

@router.post("/sessions/{session_id}/state/confirm", response_model=ApiResponse)
async def confirm_state(
    session_id: int,
    current_user=Depends(get_current_user),
    service: TechExpertService = Depends(get_service),
):
    """确认当前状态，进入下一状态

    人工确认当前阶段成果后，状态机正向流转到下一个阶段。
    """
    session = get_session_or_404(session_id, current_user.id, service)

    try:
        result = service.confirm_state(session)
        return ApiResponse(data=result, message="状态确认成功")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/sessions/{session_id}/state/rollback", response_model=ApiResponse)
async def rollback_state(
    session_id: int,
    req: RollbackRequest,
    current_user=Depends(get_current_user),
    service: TechExpertService = Depends(get_service),
):
    """回退到指定状态

    用户可以根据审查或测试结果，手动回退到之前的某个阶段重新开始。
    回退路径受状态机规则限制。
    """
    session = get_session_or_404(session_id, current_user.id, service)

    try:
        result = service.rollback_state(session, req.target_state, req.reason)
        return ApiResponse(data=result, message="状态回退成功")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/sessions/{session_id}/state/switch", response_model=ApiResponse)
async def switch_expert(
    session_id: int,
    req: SwitchExpertRequest,
    current_user=Depends(get_current_user),
    service: TechExpertService = Depends(get_service),
):
    """手动切换专家

    用户可以在任意状态下手动切换到指定专家角色，
    灵活调整协作流程。
    """
    session = get_session_or_404(session_id, current_user.id, service)

    try:
        result = service.switch_expert(session, req.expert_type)
        return ApiResponse(data=result, message="专家切换成功")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# 4. 专家列表接口
# =============================================================================

@router.get("/experts", response_model=ApiResponse)
async def list_experts(
    current_user=Depends(get_current_user),
):
    """获取四大专家信息

    返回所有专家的名称、描述、颜色、图标等信息。
    """
    experts = get_all_experts()
    return ApiResponse(data=experts, message="获取专家列表成功")


# =============================================================================
# 5. 验收标准接口（预留）
# =============================================================================

@router.get("/sessions/{session_id}/acceptance-criteria", response_model=ApiResponse)
async def get_acceptance_criteria(
    session_id: int,
    current_user=Depends(get_current_user),
    service: TechExpertService = Depends(get_service),
):
    """获取验收标准（Step 2功能，即将上线）

    预留接口，用于管理项目验收标准。
    """
    session = get_session_or_404(session_id, current_user.id, service)
    result = service.get_acceptance_criteria(session)
    return ApiResponse(data=result, message="Step 2功能，即将上线")


@router.put("/sessions/{session_id}/acceptance-criteria", response_model=ApiResponse)
async def set_acceptance_criteria(
    session_id: int,
    req: AcceptanceCriteriaRequest,
    current_user=Depends(get_current_user),
    service: TechExpertService = Depends(get_service),
):
    """设置验收标准（Step 2功能，即将上线）

    预留接口，用于配置项目验收标准。
    """
    session = get_session_or_404(session_id, current_user.id, service)
    result = service.set_acceptance_criteria(session, req.criteria)
    return ApiResponse(data=result, message="Step 2功能，即将上线")
