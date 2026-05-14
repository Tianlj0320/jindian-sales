"""加工单管理 Pydantic 模型"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ProcessingOrderItemUpdate(BaseModel):
    """加工单明细更新"""
    process_fee_unit: float | None = None
    checked: bool | None = None
    remark: str | None = None


class ProcessingOrderStatusUpdate(BaseModel):
    """加工单状态更新"""
    status: str = Field(..., description="目标状态: pending/processing/completed")


class ProcessingOrderItemResponse(BaseModel):
    """加工单明细响应"""
    id: int
    processing_order_id: int
    order_item_id: int
    product_name: str = ""
    product_code: str = ""
    width: float = 0
    height: float = 0
    qty: float = 0
    unit: str = ""
    process_desc: str = ""
    process_fee_unit: float = 0
    process_fee_subtotal: float = 0
    checked: bool = False
    remark: str = ""


class ProcessingOrderResponse(BaseModel):
    """加工单详情响应"""
    id: int
    po_no: str
    order_id: int
    order_no: str = ""
    customer_name: str = ""
    warehouse_id: int | None = None
    processing_factory: str = ""
    total_items: int = 0
    total_process_fee: float = 0
    status: str = "pending"
    printed: bool = False
    remark: str = ""
    completed_at: str | None = None
    created_at: str = ""
    updated_at: str = ""
    items: list[ProcessingOrderItemResponse] = []


class ProcessingOrderListResponse(BaseModel):
    """加工单列表项响应"""
    id: int
    po_no: str
    order_id: int
    order_no: str = ""
    customer_name: str = ""
    processing_factory: str = ""
    total_items: int = 0
    total_process_fee: float = 0
    status: str = "pending"
    printed: bool = False
    remark: str = ""
    completed_at: str | None = None
    created_at: str = ""
