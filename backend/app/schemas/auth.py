"""
认证相关 Pydantic 模型
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名/手机号")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    name: str
    username: str
    phone: str
    role: str
    position: str


class UserCreate(BaseModel):
    """创建用户"""
    username: str = Field(..., description="用户名/手机号")
    password: str = Field(..., description="密码")
    name: str = Field(..., description="姓名")
    phone: str = Field(..., description="手机号")
    role: str = Field(default="staff", description="角色")
    position: str = Field(default="", description="职务")


class UserUpdate(BaseModel):
    """更新用户"""
    name: str | None = None
    phone: str | None = None
    role: str | None = None
    position: str | None = None
    is_active: bool | None = None
    password: str | None = None
