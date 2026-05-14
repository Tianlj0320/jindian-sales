"""
角色权限管理 API
"""

from __future__ import annotations

import json

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUserDep, SessionDep, require_permission
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import success
from app.domain.role import Role
from app.schemas.role import RoleCreate, RolePermissionUpdate, RoleUpdate

router = APIRouter(prefix="/api/v1/roles", tags=["角色权限"])


@router.get("")
async def list_roles(session: SessionDep, current_user: CurrentUserDep):
    """角色列表"""
    result = await session.execute(
        select(Role).order_by(Role.sort_order, Role.id)
    )
    roles = result.scalars().all()
    return success(data=[
        {
            "id": r.id,
            "name": r.name,
            "code": r.code,
            "description": r.description,
            "permissions": json.loads(r.permissions) if r.permissions else [],
            "sort_order": r.sort_order,
            "is_active": r.is_active,
        }
        for r in roles
    ])


@router.post("")
async def create_role(
    session: SessionDep, current_user: CurrentUserDep,
    req: RoleCreate, _: None = require_permission("admin"),
):
    """创建角色"""
    # 检查编码重复
    result = await session.execute(select(Role).where(Role.code == req.code))
    if result.scalar_one_or_none():
        raise BusinessError("角色编码已存在")

    role = Role(
        name=req.name,
        code=req.code,
        description=req.description,
        permissions=json.dumps(req.permissions, ensure_ascii=False),
        sort_order=req.sort_order,
    )
    session.add(role)
    await session.flush()
    return success(data={"id": role.id}, message="角色创建成功")


@router.put("/{role_id}")
async def update_role(
    session: SessionDep, current_user: CurrentUserDep,
    role_id: int, req: RoleUpdate, _: None = require_permission("admin"),
):
    """更新角色"""
    result = await session.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise NotFoundError("角色不存在")

    if req.name is not None:
        role.name = req.name
    if req.description is not None:
        role.description = req.description
    if req.permissions is not None:
        role.permissions = json.dumps(req.permissions, ensure_ascii=False)
    if req.sort_order is not None:
        role.sort_order = req.sort_order
    if req.is_active is not None:
        role.is_active = req.is_active

    await session.flush()
    return success(message="角色更新成功")


@router.put("/{role_id}/permissions")
async def update_role_permissions(
    session: SessionDep, current_user: CurrentUserDep,
    role_id: int, req: RolePermissionUpdate, _: None = require_permission("admin"),
):
    """更新角色权限"""
    result = await session.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise NotFoundError("角色不存在")

    role.permissions = json.dumps(req.permissions, ensure_ascii=False)
    await session.flush()
    return success(message="权限更新成功")


@router.delete("/{role_id}")
async def delete_role(
    session: SessionDep, current_user: CurrentUserDep,
    role_id: int, _: None = require_permission("admin"),
):
    """删除角色（软禁用）"""
    result = await session.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise NotFoundError("角色不存在")
    role.is_active = False
    await session.flush()
    return success(message="角色已禁用")
