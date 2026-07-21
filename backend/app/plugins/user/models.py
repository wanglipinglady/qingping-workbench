"""
用户模型
定义用户数据表结构
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from app.core.database import Base


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    # 用户 ID
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 用户名（唯一）
    username = Column(String(50), unique=True, index=True, nullable=False)
    # 邮箱（唯一）
    email = Column(String(100), unique=True, index=True, nullable=True)
    # 哈希后的密码
    hashed_password = Column(String(255), nullable=False)
    # 头像 URL
    avatar = Column(String(500), nullable=True, default="")
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # 更新时间
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
