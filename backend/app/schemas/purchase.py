"""
采购相关 Pydantic 模型
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PurchaseOrderItemCreate(BaseModel):
    product_id: int = Field(..., description="产品ID")
    product_name: str = Field(default="")
    product_code: str = Field(default="")
    spec: str = Field(default="")
    quantity: float = Field(default=1)
    unit: str = Field(default="米")
    unit_price: float = Field(default=0)
    material_type: str = Field(default="主料")
    procurement_type: str = Field(default="物料", description="采购类型: 物料/成品/辅料")


class PurchaseOrderCreate(BaseModel):
    supplier_id: int = Field(..., description="供应商ID")
    contact: str = Field(default="")
    phone: str = Field(default="")
    order_ids: str = Field(default="")
    expected_date: str | None = None
    remark: str = Field(default="")
    items: list[PurchaseOrderItemCreate] = Field(default_factory=list)


class PurchaseOrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_code: str
    spec: str
    quantity: float
    unit: str
    unit_price: float
    subtotal: float
    arrived_qty: float
    material_type: str
    procurement_type: str = "物料"


class PurchaseOrderResponse(BaseModel):
    id: int
    po_no: str
    supplier_id: int
    supplier_name: str
    contact: str
    phone: str
    total_amount: float
    paid_amount: float
    debt_amount: float
    status: str
    order_date: str | None
    expected_date: str | None
    arrived_date: str | None
    remark: str
    items: list
    po_items: list[PurchaseOrderItemResponse] = []


class ReceiveItem(BaseModel):
    product_id: int
    qty: float
    unit: str = Field(default="米")
    product_name: str = Field(default="")


class ReceiveCreate(BaseModel):
    """收货请求"""
    items: list[ReceiveItem] = Field(default_factory=list)
    operator: str = Field(default="系统")
    warehouse_id: int = Field(default=1, description="收货仓库ID，默认1号仓库")


class BatchReceiveRequest(BaseModel):
    """批量收货请求"""
    po_ids: list[int] = Field(..., description="采购单ID列表")
    warehouse_id: int = Field(default=1, description="收货仓库ID，默认1号仓库")


class ReceiveRollbackItem(BaseModel):
    product_id: int
    qty: float = Field(default=0, description="回退数量，0=全部回退")
    unit: str = Field(default="")


class ReceiveRollbackCreate(BaseModel):
    """收货回退请求"""
    items: list[ReceiveRollbackItem] = Field(default_factory=list)
    warehouse_id: int = Field(default=1, description="收货仓库ID，默认1号仓库")


class PurchasePreviewRequest(BaseModel):
    """采购拆分预览请求"""
    order_ids: list[int] = Field(..., description="选定的订单ID列表")


class PurchaseGenerateRequest(BaseModel):
    """生成采购单请求"""
    order_ids: list[int] = Field(..., description="选定的订单ID列表")
