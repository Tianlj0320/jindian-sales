"""
订单费用 Pydantic 模型
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class OrderFeeCreate(BaseModel):
    """添加订单费用"""
    fee_type: str = Field(..., description="费用类型 code")
    fee_type_label: str = Field(default="", description="费用类型显示名")
    amount: float = Field(..., gt=0, description="金额")
    remark: str = Field(default="", max_length=200)


class OrderFeeUpdate(BaseModel):
    """更新订单费用"""
    fee_type: str | None = None
    fee_type_label: str | None = None
    amount: float | None = Field(None, gt=0, description="金额")
    remark: str | None = None


class OrderFeeResponse(BaseModel):
    """订单费用响应"""
    id: int
    order_id: int
    fee_type: str
    fee_type_label: str
    amount: float
    remark: str
    operator_name: str
    created_at: str
    updated_at: str
