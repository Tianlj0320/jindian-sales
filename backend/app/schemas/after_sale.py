"""
售后管理 Pydantic 模型
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AfterSaleCreate(BaseModel):
    """创建售后单"""
    order_id: int | None = None
    order_no: str = Field(default="")
    customer_name: str = Field(default="", description="客户姓名")
    customer_phone: str = Field(default="", description="联系电话")
    service_type: str = Field(..., description="售后类型 code")
    service_type_label: str = Field(default="")
    description: str = Field(default="", description="问题描述")
    priority: str = Field(default="normal", description="优先级")
    source: str = Field(default="manual", description="来源")
    order_hold: bool = Field(default=False, description="是否阻塞关联订单推进")
    remark: str = Field(default="", max_length=500)


class AfterSaleUpdate(BaseModel):
    """更新售后单（处理/关闭/审核）"""
    service_type: str | None = None
    service_type_label: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    handler_name: str | None = None
    handler_id: int | None = None
    resolution: str | None = None
    resolved_type: str | None = None
    reviewer_name: str | None = None
    review_remark: str | None = None
    order_hold: bool | None = None
    customer_confirmed: bool | None = None
    refund_amount: float | None = None
    compensation_amount: float | None = None
    rework_cost: float | None = None
    remark: str | None = None


class AfterSaleResponse(BaseModel):
    """售后单响应"""
    id: int
    service_no: str
    order_id: int | None
    order_no: str
    customer_name: str
    customer_phone: str
    service_type: str
    service_type_label: str
    description: str
    priority: str
    source: str
    status: str
    handler_id: int | None
    handler_name: str
    resolution: str
    resolved_type: str
    resolved_at: str | None
    reviewer_name: str
    review_remark: str
    reviewed_at: str | None
    rejected_at: str | None
    closed_at: str | None
    order_hold: bool
    customer_confirmed: bool
    customer_confirmed_at: str | None
    refund_amount: float
    compensation_amount: float
    rework_cost: float
    remark: str
    created_at: str
    updated_at: str


class AfterSaleStats(BaseModel):
    """售后统计"""
    pending_count: int = 0
    processing_count: int = 0
    completed_count: int = 0
    total_count: int = 0
