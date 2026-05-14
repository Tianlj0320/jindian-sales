"""
安装管理模型
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import DECIMAL, JSON, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base, TimestampMixin


class InstallTeam(Base, TimestampMixin):
    """安装队"""

    __tablename__ = "install_teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="安装队名称")
    leader_name: Mapped[str] = mapped_column(String(50), default="", comment="队长姓名")
    leader_phone: Mapped[str] = mapped_column(String(20), default="", comment="队长电话")
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否启用")
    remark: Mapped[str] = mapped_column(String(200), default="", comment="备注")


class Installer(Base, TimestampMixin):
    """安装工"""

    __tablename__ = "installers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="姓名")
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment="手机号")
    password_hash: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="登录密码")
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否启用")
    remark: Mapped[str] = mapped_column(String(200), default="", comment="备注")


class InstallTeamMember(Base, TimestampMixin):
    """安装队成员关系"""

    __tablename__ = "install_team_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("install_teams.id"), nullable=False, comment="安装队ID")
    installer_id: Mapped[int] = mapped_column(Integer, ForeignKey("installers.id"), nullable=False, comment="安装工ID")


class InstallationOrder(Base, TimestampMixin):
    """安装单"""

    __tablename__ = "installation_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ins_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, comment="安装单号")

    # 关联订单
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False, comment="订单ID")
    order_no: Mapped[str] = mapped_column(String(30), default="", comment="订单号")

    # 客户信息
    customer_name: Mapped[str] = mapped_column(String(50), default="", comment="客户姓名")
    customer_phone: Mapped[str] = mapped_column(String(20), default="", comment="客户电话")
    address: Mapped[str] = mapped_column(String(300), default="", comment="安装地址")

    # 安装内容
    product_details: Mapped[dict | None] = mapped_column(JSON, default=dict, comment="产品明细")
    measure_summary: Mapped[str] = mapped_column(Text, default="", comment="测量摘要")
    install_requirements: Mapped[str] = mapped_column(Text, default="", comment="安装要求")

    # 排期
    team_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("install_teams.id"), nullable=True, comment="安装队ID")
    installer_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="安装工ID")
    installer_name: Mapped[str] = mapped_column(String(50), default="", comment="安装工姓名")
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="预约日期")
    install_time_slot: Mapped[str] = mapped_column(String(20), default="", comment="安装时段")

    # 状态
    status: Mapped[str] = mapped_column(String(20), default="待分配", comment="状态: 待分配/已派工/安装中/已完成/已验收")

    # 金额
    labor_cost: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="人工费")
    material_cost: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="材料费")
    total_cost: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="总费用")

    # 验收
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="验收评分 1-5")
    install_photos: Mapped[list | None] = mapped_column(JSON, default=list, comment="安装照片")
    customer_signature: Mapped[str] = mapped_column(Text, default="", comment="客户签名")

    # 时间
    actual_start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="实际开始时间")
    actual_end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="实际结束时间")
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="验收时间")

    # 收款
    receivable_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="应收金额")
    received_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="已收金额")
    unpaid_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="未收金额")

    remark: Mapped[str] = mapped_column(String(500), default="", comment="备注")
