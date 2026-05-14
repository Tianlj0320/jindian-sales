"""
安全与认证模块
JWT Token 签发/验证、密码哈希
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(
    sub: int | str,
    name: str,
    role: str = "staff",
    expires_hours: int | None = None,
) -> str:
    """签发 JWT Token"""
    now = datetime.now(timezone.utc)
    expire_hours = expires_hours or settings.JWT_EXPIRE_HOURS
    payload = {
        "sub": str(sub),
        "name": name,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=expire_hours),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """解码并验证 JWT Token，返回 payload 或 None"""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None
