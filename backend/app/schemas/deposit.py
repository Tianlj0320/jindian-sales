"""
定金管理 Pydantic 模型
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class DepositCreate(BaseModel):
    """创建定金记录"""
    customer_id: int = Field(..., description="客户ID")
    amount: float = Field(..., description="金额")
    payment_method: str = Field(default="", description="收款方式")
    received_at: str | None = Field(None, description="收款日期")
    remark: str = Field(default="", description="备注")


class DepositUpdate(BaseModel):
    """更新定金记录"""
    amount: float | None = None
    payment_method: str | None = None
    received_at: str | None = None
    remark: str | None = None


class DepositResponse(BaseModel):
    """定金记录响应"""
    id: int
    customer_id: int
    amount: float
    balance: float
    payment_method: str
    received_at: str | None
    operator_id: int | None
    operator_name: str
    remark: str
    created_at: str
    updated_at: str


class DepositListResponse(BaseModel):
    """定金列表响应"""
    total: int = 0
    items: list[DepositResponse] = []
