"""
角色相关 Pydantic 模型
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    """创建角色"""
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色编码")
    description: str = Field(default="")
    permissions: list[str] = Field(default=[], description="权限列表")
    sort_order: int = Field(default=0)


class RoleUpdate(BaseModel):
    """更新角色"""
    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class RolePermissionUpdate(BaseModel):
    """更新角色权限"""
    permissions: list[str] = Field(..., description="权限列表")


class RoleResponse(BaseModel):
    """角色响应"""
    id: int
    name: str
    code: str
    description: str
    permissions: list[str]
    sort_order: int
    is_active: bool
