"""
API 通用依赖注入
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.database import get_session
from app.domain.auth import User

# ── 数据库会话依赖 ────────────────────────────────────────────
SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ── 用户认证依赖 ──────────────────────────────────────────────
async def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))] = None,
) -> User:
    """从 JWT Token 获取当前用户"""
    if credentials is None:
        raise UnauthorizedError("请先登录")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedError("登录已过期，请重新登录")

    user_id = int(payload.get("sub", 0))
    if not user_id:
        raise UnauthorizedError("Token无效")

    result = await session.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedError("用户不存在或已停用")

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


# ── 分页参数依赖 ──────────────────────────────────────────────
class PageParams:
    """分页查询参数"""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="页码"),
        page_size: int = Query(default=20, ge=1, le=200, description="每页条数"),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


PageDep = Annotated[PageParams, Depends()]
