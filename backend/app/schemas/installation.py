"""
安装管理 Pydantic 模型
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class InstallTeamCreate(BaseModel):
    name: str = Field(..., description="安装队名称")
    leader_name: str = Field(default="")
    leader_phone: str = Field(default="")
    remark: str = Field(default="")


class InstallTeamUpdate(BaseModel):
    """更新安装队"""
    name: str | None = None
    leader_name: str | None = None
    leader_phone: str | None = None
    is_active: bool | None = None
    remark: str | None = None


class InstallerUpdate(BaseModel):
    """更新安装工"""
    name: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class InstallTeamResponse(BaseModel):
    id: int
    name: str
    leader_name: str
    leader_phone: str
    is_active: bool
    member_count: int = 0


class InstallerCreate(BaseModel):
    name: str = Field(..., description="姓名")
    phone: str = Field(..., description="手机号")
    password: str | None = None


class InstallerResponse(BaseModel):
    id: int
    name: str
    phone: str
    is_active: bool


class InstallationOrderCreate(BaseModel):
    """创建安装单"""
    order_id: int = Field(..., description="订单ID")
    team_id: int | None = None
    installer_id: int | None = None
    scheduled_date: str | None = None
    install_time_slot: str = Field(default="")
    labor_cost: float = Field(default=0)
    material_cost: float = Field(default=0)
    remark: str = Field(default="")


class InstallationOrderResponse(BaseModel):
    id: int
    ins_no: str
    order_id: int
    order_no: str
    customer_name: str
    customer_phone: str
    address: str
    team_id: int | None
    installer_id: int | None
    installer_name: str
    scheduled_date: str | None
    install_time_slot: str
    status: str
    labor_cost: float
    material_cost: float
    total_cost: float
    quality_score: int | None
    receivable_amount: float
    received_amount: float
    unpaid_amount: float
    remark: str
    created_at: str
