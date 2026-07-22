"""
微信公众号写作助手 - 数据模型
定义 5 张核心表：会话、资料卡片、消息记录、输出版本、写作模板
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, SmallInteger
from sqlalchemy.orm import relationship

from app.core.database import Base


class WeChatWriterSession(Base):
    """写作会话表
    基于状态机驱动，7 个状态：idle → topic_confirm → research → outline → draft → polish → done
    """

    __tablename__ = "wechat_writer_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="会话ID")
    user_id = Column(Integer, index=True, nullable=False, comment="所属用户ID")
    title = Column(String(200), nullable=False, comment="会话标题（默认用文章主题）")
    topic = Column(Text, nullable=False, comment="用户给出的原始主题")
    confirmed_topic = Column(Text, nullable=True, comment="确认后的细化主题+写作角度")
    current_state = Column(
        String(50), nullable=False, default="idle", index=True,
        comment="当前状态: idle/topic_confirm/research/outline/draft/polish/done"
    )
    iteration_count = Column(Integer, nullable=False, default=0, comment="迭代次数（含回退后的重试）")
    status = Column(
        String(20), nullable=False, default="active", index=True,
        comment="会话状态: active/completed/archived"
    )
    total_tokens = Column(Integer, nullable=False, default=0, comment="累计Token消耗")
    obsidian_sync_time = Column(DateTime, nullable=True, comment="Obsidian上次同步时间")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        nullable=False, index=True, comment="更新时间"
    )

    # 关联
    materials = relationship(
        "WeChatWriterMaterial", back_populates="session", cascade="all, delete-orphan"
    )
    messages = relationship(
        "WeChatWriterMessage", back_populates="session", cascade="all, delete-orphan",
        order_by="WeChatWriterMessage.created_at"
    )
    outputs = relationship(
        "WeChatWriterOutput", back_populates="session", cascade="all, delete-orphan"
    )


class WeChatWriterMaterial(Base):
    """资料卡片表
    存储从 Obsidian、知识库和网络搜集的资料卡片
    """

    __tablename__ = "wechat_writer_materials"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="资料ID")
    session_id = Column(
        Integer, ForeignKey("wechat_writer_sessions.id", ondelete="CASCADE"),
        index=True, nullable=False, comment="关联会话ID"
    )
    source_type = Column(
        String(20), nullable=False, index=True,
        comment="来源类型: obsidian/knowledge_base/web"
    )
    title = Column(String(500), nullable=False, comment="资料标题")
    url = Column(String(1000), nullable=True, comment="来源URL或文件路径")
    core_idea = Column(Text, nullable=True, comment="核心观点（1-2句话）")
    useful_snippets = Column(Text, nullable=True, comment="可用片段（JSON数组，每段一句话）")
    credibility_score = Column(
        Integer, nullable=False, default=3, index=True,
        comment="可信度评分（1-5）"
    )
    suggested_usage = Column(
        String(100), nullable=True,
        comment="推荐使用场景: intro/argument/ending"
    )
    is_useful = Column(
        SmallInteger, nullable=False, default=1, index=True,
        comment="用户标记是否有用（1=有用，0=没用）"
    )
    tags = Column(String(500), nullable=True, comment="标签（逗号分隔）")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="创建时间")

    # 关联
    session = relationship("WeChatWriterSession", back_populates="materials")


class WeChatWriterMessage(Base):
    """写作消息记录表
    存储会话中的每条消息，带专家角色和状态标签
    """

    __tablename__ = "wechat_writer_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="消息ID")
    session_id = Column(
        Integer, ForeignKey("wechat_writer_sessions.id", ondelete="CASCADE"),
        index=True, nullable=False, comment="关联会话ID"
    )
    role = Column(String(20), nullable=False, index=True, comment="消息角色: user/assistant")
    expert_type = Column(
        String(50), nullable=True, index=True,
        comment="专家类型: topic_editor/researcher/outliner/writer"
    )
    state_label = Column(
        String(50), nullable=True, index=True,
        comment="发送时的状态标签"
    )
    iteration = Column(Integer, nullable=False, default=1, index=True, comment="第几轮迭代")
    content = Column(Text, nullable=False, comment="消息内容（Markdown）")
    token_usage = Column(Integer, nullable=False, default=0, comment="本条消息Token消耗")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="创建时间")

    # 关联
    session = relationship("WeChatWriterSession", back_populates="messages")


class WeChatWriterOutput(Base):
    """输出版本表
    存储各步骤的历史输出，支持版本对比和回滚
    """

    __tablename__ = "wechat_writer_outputs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="输出ID")
    session_id = Column(
        Integer, ForeignKey("wechat_writer_sessions.id", ondelete="CASCADE"),
        index=True, nullable=False, comment="关联会话ID"
    )
    step = Column(
        String(50), nullable=False, index=True,
        comment="对应步骤: topic/research/outline/draft/polish"
    )
    content_type = Column(
        String(50), nullable=False, index=True,
        comment="内容类型: analysis/materials/outline/draft/final"
    )
    content = Column(Text, nullable=False, comment="具体内容（Markdown）")
    version = Column(Integer, nullable=False, default=1, index=True, comment="版本号（每次重生成本+1）")
    is_confirmed = Column(
        SmallInteger, nullable=False, default=0, index=True,
        comment="用户是否确认了这个版本"
    )
    feedback = Column(Text, nullable=True, comment="重新生成时用户填写的修改建议")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="创建时间")

    # 关联
    session = relationship("WeChatWriterSession", back_populates="outputs")


class WeChatWriterTemplate(Base):
    """写作模板表
    存储预设和用户自定义的写作模板
    """

    __tablename__ = "wechat_writer_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="模板ID")
    name = Column(String(200), nullable=False, comment="模板名称")
    description = Column(Text, nullable=True, comment="模板描述")
    category = Column(
        String(50), nullable=False, default="custom", index=True,
        comment="模板分类:干货/情感/热点/科普/教程/测评/复盘/其他/custom"
    )
    icon = Column(String(50), nullable=True, default="📝", comment="模板图标（emoji）")

    # 模板配置
    topic_prompt = Column(Text, nullable=True, comment="选题阶段自定义 Prompt")
    research_prompt = Column(Text, nullable=True, comment="研究员自定义 Prompt")
    outline_prompt = Column(Text, nullable=True, comment="结构师自定义 Prompt")
    writer_prompt = Column(Text, nullable=True, comment="撰稿人自定义 Prompt")

    # 预设内容
    suggested_topics = Column(Text, nullable=True, comment="推荐主题（JSON 数组字符串）")
    default_style = Column(String(200), nullable=True, comment="默认文章风格")
    default_audience = Column(String(200), nullable=True, comment="默认目标读者")

    # 元数据
    user_id = Column(Integer, nullable=True, index=True, comment="创建者用户ID（NULL=系统预设）")
    is_public = Column(SmallInteger, nullable=False, default=0, comment="是否公开（1=公开，0=私有）")
    is_system = Column(SmallInteger, nullable=False, default=0, index=True, comment="是否系统预设（1=是，0=否）")
    use_count = Column(Integer, nullable=False, default=0, index=True, comment="使用次数")
    sort_order = Column(Integer, nullable=False, default=0, index=True, comment="排序（越小越靠前）")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
