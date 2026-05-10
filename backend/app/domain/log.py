"""
操作日志模型
"""

from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base, TimestampMixin


class OperationalLog(Base, TimestampMixin):
    """操作日志（审计追踪）"""

    __tablename__ = "operational_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operator_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="操作人ID")
    operator_name: Mapped[str] = mapped_column(String(50), default="", comment="操作人姓名")
    action: Mapped[str] = mapped_column(String(20), nullable=False, comment="操作: CREATE/UPDATE/DELETE/RESTORE")
    resource: Mapped[str] = mapped_column(String(50), nullable=False, comment="资源: order/customer/product/...")
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="资源ID")
    detail: Mapped[str] = mapped_column(Text, default="", comment="操作详情")
    ip_address: Mapped[str] = mapped_column(String(50), default="", comment="IP地址")
