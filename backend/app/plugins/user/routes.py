"""
用户路由
定义用户相关的 API 端点
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.exceptions import unified_response
from app.plugins.user.models import User
from app.plugins.user.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserUpdateRequest,
    UserResponse,
    TokenResponse,
)
from app.plugins.user.service import user_service

router = APIRouter(
    prefix="/users",
    tags=["用户管理"],
)


@router.post("/register", summary="用户注册")
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    新用户注册

    - **username**: 用户名（3-50字符）
    - **password**: 密码（6-50字符）
    - **email**: 邮箱（可选）
    """
    result = user_service.register(db, request)
    return unified_response(data=result.model_dump())


@router.post("/login", summary="用户登录")
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """
    用户登录，返回访问令牌

    - **username**: 用户名
    - **password**: 密码
    """
    result = user_service.login(db, request)
    return unified_response(data=result.model_dump())


@router.get("/me", summary="获取当前用户信息")
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """获取当前登录用户的详细信息"""
    return unified_response(
        data=UserResponse.model_validate(current_user).model_dump()
    )


@router.put("/me", summary="更新当前用户信息")
async def update_me(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    更新当前用户信息

    - **email**: 新邮箱（可选）
    - **avatar**: 新头像 URL（可选）
    - **password**: 新密码（可选）
    """
    result = user_service.update_user(db, current_user, request)
    return unified_response(data=result.model_dump())
