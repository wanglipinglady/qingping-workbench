"""
用户服务层
处理用户相关的业务逻辑
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.core.auth import hash_password, verify_password, create_access_token
from app.core.exceptions import BusinessException
from app.plugins.user.models import User
from app.plugins.user.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserUpdateRequest,
    UserResponse,
    TokenResponse,
)


class UserService:
    """用户服务类"""

    @staticmethod
    def register(db: Session, request: UserRegisterRequest) -> TokenResponse:
        """
        用户注册

        Args:
            db: 数据库会话
            request: 注册请求

        Returns:
            登录令牌响应

        Raises:
            BusinessException: 用户名已存在时抛出
        """
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == request.username).first()
        if existing_user:
            raise BusinessException(message="用户名已存在", code=1001)

        # 检查邮箱是否已存在
        if request.email:
            existing_email = db.query(User).filter(User.email == request.email).first()
            if existing_email:
                raise BusinessException(message="邮箱已被注册", code=1002)

        # 创建新用户
        user = User(
            username=request.username,
            email=request.email,
            hashed_password=hash_password(request.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 生成令牌
        access_token = create_access_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    @staticmethod
    def login(db: Session, request: UserLoginRequest) -> TokenResponse:
        """
        用户登录

        Args:
            db: 数据库会话
            request: 登录请求

        Returns:
            登录令牌响应

        Raises:
            BusinessException: 用户名或密码错误时抛出
        """
        # 查找用户
        user = db.query(User).filter(User.username == request.username).first()
        if not user:
            raise BusinessException(message="用户名或密码错误", code=1003)

        # 验证密码
        if not verify_password(request.password, user.hashed_password):
            raise BusinessException(message="用户名或密码错误", code=1003)

        # 生成令牌
        access_token = create_access_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        根据 ID 获取用户

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            用户对象，不存在则返回 None
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def update_user(
        db: Session,
        user: User,
        request: UserUpdateRequest,
    ) -> UserResponse:
        """
        更新用户信息

        Args:
            db: 数据库会话
            user: 当前用户对象
            request: 更新请求

        Returns:
            更新后的用户信息

        Raises:
            BusinessException: 邮箱已被占用时抛出
        """
        # 更新邮箱
        if request.email is not None:
            # 检查邮箱是否已被其他用户使用
            existing = (
                db.query(User)
                .filter(User.email == request.email, User.id != user.id)
                .first()
            )
            if existing:
                raise BusinessException(message="邮箱已被其他用户使用", code=1002)
            user.email = request.email

        # 更新头像
        if request.avatar is not None:
            user.avatar = request.avatar

        # 更新密码
        if request.password is not None:
            user.hashed_password = hash_password(request.password)

        db.commit()
        db.refresh(user)

        return UserResponse.model_validate(user)


# 全局服务实例
user_service = UserService()
