"""
知识库模型
定义知识库和文档的数据表结构
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class KnowledgeBase(Base):
    """知识库模型"""

    __tablename__ = "knowledge_bases"

    # 知识库 ID
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 知识库名称
    name = Column(String(100), nullable=False, index=True)
    # 知识库描述
    description = Column(Text, nullable=True, default="")
    # 创建者用户 ID
    user_id = Column(Integer, index=True, nullable=False)
    # 文档数量
    doc_count = Column(Integer, default=0, nullable=False)
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # 更新时间
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关联文档
    documents = relationship(
        "Document", back_populates="knowledge_base", cascade="all, delete-orphan"
    )


class Document(Base):
    """文档模型"""

    __tablename__ = "documents"

    # 文档 ID
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 所属知识库 ID
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), index=True, nullable=False)
    # 文件名称
    filename = Column(String(255), nullable=False)
    # 文件类型（md, txt, pdf 等）
    file_type = Column(String(20), nullable=False, default="txt")
    # 文件大小（字节）
    file_size = Column(Integer, default=0, nullable=False)
    # 处理状态：processing（处理中）、ready（已就绪）、failed（处理失败）
    status = Column(String(20), default="processing", nullable=False, index=True)
    # 分块数量
    chunk_count = Column(Integer, default=0, nullable=False)
    # 错误信息（处理失败时记录）
    error_msg = Column(Text, nullable=True)
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联知识库
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
