"""
用户认证模型
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """系统用户（员工登录账号）"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="用户名/手机号")
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False, comment="密码哈希")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="真实姓名")
    phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="手机号")
    role: Mapped[str] = mapped_column(String(20), default="staff", comment="角色: admin/manager/staff")
    position: Mapped[str] = mapped_column(String(50), default="", comment="职务")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="头像URL")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name}, role={self.role})>"
