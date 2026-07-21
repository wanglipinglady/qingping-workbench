"""
认证模块
提供 JWT 令牌生成/验证、密码哈希、当前用户获取等功能
"""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.plugins.user.models import User

# OAuth2 令牌获取方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login", auto_error=False)


def hash_password(password: str) -> str:
    """
    对密码进行 bcrypt 哈希处理

    Args:
        password: 明文密码

    Returns:
        哈希后的密码字符串
    """
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        是否匹配
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    创建 JWT 访问令牌

    Args:
        subject: 令牌主题（通常为用户 ID）
        expires_delta: 过期时间增量，为 None 则使用配置的默认值

    Returns:
        JWT 令牌字符串
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码 JWT 访问令牌

    Args:
        token: JWT 令牌字符串

    Returns:
        解码后的 payload 字典，令牌无效则返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    获取当前登录用户的依赖函数

    Args:
        token: OAuth2 令牌
        db: 数据库会话

    Returns:
        当前用户对象

    Raises:
        HTTPException: 令牌无效或用户不存在时抛出 401 异常
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌中缺少用户信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    可选获取当前用户（游客也可访问）

    Args:
        token: OAuth2 令牌
        db: 数据库会话

    Returns:
        当前用户对象，未登录则返回 None
    """
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    return user
