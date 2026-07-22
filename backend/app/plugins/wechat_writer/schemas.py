"""
微信公众号写作助手 - Pydantic Schema
定义请求/响应的数据结构
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field


# ========== 枚举 ==========

class WriterState(str, Enum):
    """写作状态机的状态枚举"""
    IDLE = "idle"
    TOPIC_CONFIRM = "topic_confirm"
    RESEARCH = "research"
    OUTLINE = "outline"
    DRAFT = "draft"
    POLISH = "polish"
    DONE = "done"


class SessionStatus(str, Enum):
    """会话状态"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class SourceType(str, Enum):
    """资料来源类型"""
    OBSIDIAN = "obsidian"
    KNOWLEDGE_BASE = "knowledge_base"
    WEB = "web"


# ========== 会话相关 ==========

class SessionCreateRequest(BaseModel):
    """创建写作会话请求"""
    topic: str = Field(..., min_length=1, max_length=500, description="文章主题")
    title: Optional[str] = Field(None, max_length=200, description="会话标题（默认用主题）")


class SessionUpdateRequest(BaseModel):
    """更新写作会话请求"""
    title: Optional[str] = Field(None, max_length=200)
    confirmed_topic: Optional[str] = Field(None)
    status: Optional[SessionStatus] = Field(None)


class SessionResponse(BaseModel):
    """写作会话响应"""
    id: int
    user_id: int
    title: str
    topic: str
    confirmed_topic: Optional[str] = None
    current_state: str
    iteration_count: int
    status: str
    total_tokens: int
    obsidian_sync_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """会话列表响应"""
    items: List[SessionResponse]
    total: int
    page: int
    page_size: int


class SessionDetailResponse(SessionResponse):
    """会话详情响应（含关联数据的统计）"""
    material_count: int = 0
    message_count: int = 0
    output_count: int = 0


# ========== 状态操作相关 ==========

class StateTransitionRequest(BaseModel):
    """状态转换请求"""
    action: str = Field(..., description="操作: confirm/regenerate/rollback/switch_expert")
    target_state: Optional[WriterState] = Field(None, description="目标状态（回退时用）")
    feedback: Optional[str] = Field(None, description="重新生成时的用户建议")
    expert_type: Optional[str] = Field(None, description="切换的专家类型")


class StateResponse(BaseModel):
    """状态响应"""
    session_id: int
    current_state: str
    previous_state: Optional[str] = None
    message: str


# ========== 资料卡片相关 ==========

class MaterialResponse(BaseModel):
    """资料卡片响应"""
    id: int
    session_id: int
    source_type: str
    title: str
    url: Optional[str] = None
    core_idea: Optional[str] = None
    useful_snippets: Optional[str] = None
    credibility_score: int
    suggested_usage: Optional[str] = None
    is_useful: bool
    tags: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MaterialUpdateRequest(BaseModel):
    """更新资料卡片请求"""
    is_useful: Optional[bool] = None
    tags: Optional[str] = None
    credibility_score: Optional[int] = None


class MaterialCreateRequest(BaseModel):
    """创建资料卡片请求"""
    source_type: str = "obsidian"  # obsidian / knowledge_base / web
    title: str
    url: Optional[str] = None
    core_idea: Optional[str] = None
    useful_snippets: Optional[str] = None  # JSON 数组字符串
    credibility_score: int = 3
    suggested_usage: Optional[str] = None
    tags: Optional[str] = None


class MaterialParseRequest(BaseModel):
    """从 AI 输出文本批量解析资料卡片请求"""
    ai_output: str


# ========== 输出版本相关 ==========

class OutputResponse(BaseModel):
    """输出响应"""
    id: int
    session_id: int
    step: str
    content_type: str
    content: str
    version: int
    is_confirmed: bool
    feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OutputListResponse(BaseModel):
    """输出版本列表响应"""
    step: str
    items: List[OutputResponse]
    total: int


# ========== 通用响应 ==========

class MessageResponse(BaseModel):
    """操作消息响应"""
    message: str
    success: bool = True
