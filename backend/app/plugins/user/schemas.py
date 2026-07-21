"""
用户数据模式（Pydantic Schemas）
定义 API 请求和响应的数据结构
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ========== 请求模型 ==========

class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱")


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserUpdateRequest(BaseModel):
    """用户信息更新请求"""
    email: Optional[EmailStr] = Field(None, description="邮箱")
    avatar: Optional[str] = Field(None, description="头像 URL")
    password: Optional[str] = Field(None, min_length=6, max_length=50, description="新密码")


# ========== 响应模型 ==========

class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: Optional[str] = None
    avatar: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """登录令牌响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
