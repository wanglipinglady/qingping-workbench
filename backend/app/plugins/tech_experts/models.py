"""技术专家组数据模型

包含三张核心表：
- expert_sessions: 专家会话（状态机载体）
- expert_messages: 专家消息（对话历史）
- expert_state_transitions: 状态转移记录（审计追踪）
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.sql import func

from app.core.database import Base


class ExpertSession(Base):
    """专家会话 - 状态机的载体

    每个会话对应一个完整的技术专家组协作流程，
    包含当前状态、迭代次数、验收标准等信息。
    """

    __tablename__ = "expert_sessions"

    # 主键
    id = Column(Integer, primary_key=True, index=True)
    # 所属用户
    user_id = Column(Integer, nullable=False, index=True)
    # 会话标题
    title = Column(String(200), default="新的技术协作")
    # 当前状态节点（对应 TechExpertState 枚举值）
    current_state = Column(String(50), default="idle", index=True)
    # 当前迭代轮次（从 0 开始）
    iteration_count = Column(Integer, default=0)
    # 最大迭代轮次（防止无限循环）
    max_iterations = Column(Integer, default=10)
    # 验收标准（JSON 格式，预留字段）
    acceptance_criteria = Column(JSON, nullable=True)
    # 会话状态: active(活跃) / paused(暂停) / completed(已完成)
    status = Column(String(20), default="active", index=True)
    # 累计 token 消耗
    total_tokens = Column(Integer, default=0)
    # 创建时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # 更新时间
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_session_user_status", "user_id", "status"),
    )


class ExpertMessage(Base):
    """专家消息 - 对话历史记录

    记录每一轮对话的详细信息，包括发言角色、所属状态、迭代轮次等。
    """

    __tablename__ = "expert_messages"

    # 主键
    id = Column(Integer, primary_key=True, index=True)
    # 所属会话
    session_id = Column(Integer, nullable=False, index=True)
    # 消息角色: user / assistant / system
    role = Column(String(20), nullable=False)
    # 专家类型: architect / coder / reviewer / tester / null(用户消息)
    expert_type = Column(String(50), nullable=True, index=True)
    # 所属状态节点（发送消息时的状态）
    state_label = Column(String(50), nullable=True, index=True)
    # 迭代轮次
    iteration = Column(Integer, default=0)
    # 消息内容
    content = Column(Text, default="")
    # 本条消息消耗的 token 数
    token_usage = Column(Integer, default=0)
    # 创建时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_message_session_state", "session_id", "state_label"),
    )


class ExpertStateTransition(Base):
    """状态转移记录 - 审计追踪

    记录每一次状态变化，包括自动转移和人工介入导致的转移，
    便于回溯和调试。
    """

    __tablename__ = "expert_state_transitions"

    # 主键
    id = Column(Integer, primary_key=True, index=True)
    # 所属会话
    session_id = Column(Integer, nullable=False, index=True)
    # 源状态
    from_state = Column(String(50), nullable=False)
    # 目标状态
    to_state = Column(String(50), nullable=False)
    # 转移类型:
    #   auto - 自动转移（状态机正常流转）
    #   human_confirm - 人工确认后正向转移
    #   human_rollback - 人工回退
    #   human_switch - 人工手动切换专家
    transition_type = Column(String(30), nullable=False, index=True)
    # 转移原因说明
    reason = Column(Text, default="")
    # 创建时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_transition_session_time", "session_id", "created_at"),
    )
