"""
认证 API
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUserDep, SessionDep
from app.core.exceptions import BusinessError, NotFoundError, UnauthorizedError
from app.core.response import success
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.auth import User
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo, UserCreate

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/login")
async def login(session: SessionDep, req: LoginRequest):
    """用户登录"""
    result = await session.execute(
        select(User).where(User.username == req.username, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise BusinessError("用户名或密码错误")

    if not verify_password(req.password, user.password_hash):
        raise BusinessError("用户名或密码错误")

    token = create_access_token(
        sub=user.id,
        name=user.name,
        role=user.role,
    )

    return success(data={
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "phone": user.phone,
            "role": user.role,
            "position": user.position,
        },
    })


@router.get("/me")
async def get_me(session: SessionDep, current_user: CurrentUserDep):
    """获取当前用户信息"""
    return success(data={
        "id": current_user.id,
        "name": current_user.name,
        "username": current_user.username,
        "phone": current_user.phone,
        "role": current_user.role,
        "position": current_user.position,
    })


# ── 用户管理（管理员用） ──────────────────────────────────────


@router.get("/users")
async def list_users(session: SessionDep, current_user: CurrentUserDep):
    """用户列表"""
    result = await session.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return success(data=[
        {
            "id": u.id,
            "name": u.name,
            "username": u.username,
            "phone": u.phone,
            "role": u.role,
            "position": u.position,
            "is_active": u.is_active,
        }
        for u in users
    ])


@router.post("/users")
async def create_user(session: SessionDep, current_user: CurrentUserDep, req: UserCreate):
    """创建用户"""
    # 检查用户名重复
    result = await session.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise BusinessError("用户名已存在")

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        name=req.name,
        phone=req.phone,
        role=req.role,
        position=req.position,
    )
    session.add(user)
    await session.flush()

    return success(data={
        "id": user.id,
        "name": user.name,
        "username": user.username,
    }, message="用户创建成功")


@router.put("/users/{user_id}")
async def update_user(session: SessionDep, current_user: CurrentUserDep, user_id: int, req: UserUpdate):
    """更新用户"""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户不存在")

    if req.name is not None:
        user.name = req.name
    if req.phone is not None:
        user.phone = req.phone
    if req.role is not None:
        user.role = req.role
    if req.position is not None:
        user.position = req.position
    if req.is_active is not None:
        user.is_active = req.is_active
    if req.password:
        user.password_hash = hash_password(req.password)

    await session.flush()
    return success(message="用户更新成功")


@router.delete("/users/{user_id}")
async def delete_user(session: SessionDep, current_user: CurrentUserDep, user_id: int):
    """删除用户（软禁用）"""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户不存在")
    user.is_active = False
    await session.flush()
    return success(message="用户已禁用")
