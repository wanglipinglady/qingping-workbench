"""技术专家组 Pydantic Schema

定义所有 API 请求和响应的数据结构。
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ========== 通用响应格式 ==========

class ApiResponse(BaseModel):
    """统一响应格式"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))


# ========== 会话相关 ==========

class SessionCreateRequest(BaseModel):
    """创建会话请求"""
    title: str = Field(default="新的技术协作", description="会话标题")
    initial_message: Optional[str] = Field(default=None, description="初始需求描述（可选）")


class SessionUpdateRequest(BaseModel):
    """更新会话请求"""
    title: Optional[str] = Field(default=None, description="会话标题")


class SessionResponse(BaseModel):
    """会话详情响应"""
    id: int
    user_id: int
    title: str
    current_state: str
    iteration_count: int
    max_iterations: int
    status: str
    total_tokens: int
    acceptance_criteria: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SessionListItem(BaseModel):
    """会话列表项"""
    id: int
    title: str
    current_state: str
    iteration_count: int
    status: str
    total_tokens: int
    updated_at: Optional[str] = None


# ========== 消息相关 ==========

class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    session_id: int
    role: str
    expert_type: Optional[str] = None
    state_label: Optional[str] = None
    iteration: int
    content: str
    token_usage: int
    created_at: Optional[str] = None


class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., description="用户消息内容")


# ========== 状态控制相关 ==========

class StateInfoResponse(BaseModel):
    """当前状态信息响应"""
    current_state: str
    current_state_label: str
    current_expert: Optional[str] = None
    current_expert_name: Optional[str] = None
    iteration: int
    can_confirm: bool
    can_rollback_to: List[str]
    pause_for_human: bool


class RollbackRequest(BaseModel):
    """回退状态请求"""
    target_state: str = Field(..., description="目标状态")
    reason: str = Field(default="", description="回退原因")


class SwitchExpertRequest(BaseModel):
    """切换专家请求"""
    expert_type: str = Field(..., description="目标专家类型: architect/coder/reviewer/tester")


class StateTransitionResponse(BaseModel):
    """状态转移响应"""
    from_state: str
    to_state: str
    transition_type: str
    reason: str = ""


# ========== 验收标准相关 ==========

class AcceptanceCriteriaRequest(BaseModel):
    """设置验收标准请求"""
    criteria: Dict[str, Any] = Field(default_factory=dict, description="验收标准内容")


class AcceptanceCriteriaResponse(BaseModel):
    """验收标准响应"""
    criteria: Optional[Dict[str, Any]] = None
    message: str = ""


# ========== 专家信息相关 ==========

class ExpertInfo(BaseModel):
    """专家信息"""
    type: str
    name: str
    icon: str
    color: str
    description: str
    state: Optional[str] = None


# ========== SSE 事件 ==========

class SSEEvent:
    """SSE 事件类型常量"""
    STATE_ENTER = "state_enter"          # 进入新状态
    STATE_PAUSE = "state_pause"          # 状态完成，暂停等待人工确认
    MESSAGE_CHUNK = "message_chunk"      # 消息内容块（流式）
    MESSAGE_END = "message_end"          # 单条消息生成完成
    STATE_TRANSITION = "state_transition" # 状态转移
    ERROR = "error"                      # 错误
