"""
剪藏模型
记录网页剪藏的元数据，正文同时写入知识库文档与向量库
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.core.database import Base


class Clipping(Base):
    """剪藏记录"""

    __tablename__ = "clippings"
    __table_args__ = (
        # 同一用户同一 URL 只保留一条，保证剪藏幂等
        UniqueConstraint("user_id", "url_hash", name="uq_clipping_user_url"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 所属用户
    user_id = Column(Integer, index=True, nullable=False)
    # 落库的知识库 ID
    kb_id = Column(Integer, index=True, nullable=False)
    # 对应的知识库文档 ID（解析失败时为空）
    document_id = Column(Integer, index=True, nullable=True)
    # 原始链接
    url = Column(Text, nullable=False)
    # 规范化链接的 SHA256（用于去重）
    url_hash = Column(String(64), index=True, nullable=False)
    # 标题
    title = Column(String(255), nullable=False, default="")
    # 站点名称
    site_name = Column(String(100), nullable=True, default="")
    # 作者
    author = Column(String(100), nullable=True, default="")
    # 摘要（正文前 200 字）
    summary = Column(Text, nullable=True, default="")
    # 正文 Markdown（便于再次复用，不必重新抓取）
    content_md = Column(Text, nullable=True, default="")
    # 标签（逗号分隔）
    tags = Column(String(255), nullable=True, default="")
    # 分类（如 技术/行业/管理）
    category = Column(String(50), nullable=True, default="")
    # 正文字符数
    content_length = Column(Integer, default=0, nullable=False)
    # 状态：ready / failed
    status = Column(String(20), default="ready", nullable=False, index=True)
    # 失败原因
    error_msg = Column(Text, nullable=True)
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
