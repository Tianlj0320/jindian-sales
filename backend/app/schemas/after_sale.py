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
    remark: str = Field(default="", max_length=500)


class AfterSaleUpdate(BaseModel):
    """更新售后单（处理/关闭）"""
    service_type: str | None = None
    service_type_label: str | None = None
    description: str | None = None
    status: str | None = None
    handler_name: str | None = None
    resolution: str | None = None
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
    status: str
    handler_id: int | None
    handler_name: str
    resolution: str
    resolved_at: str | None
    remark: str
    created_at: str
    updated_at: str


class AfterSaleStats(BaseModel):
    """售后统计"""
    pending_count: int = 0
    processing_count: int = 0
    completed_count: int = 0
    total_count: int = 0
