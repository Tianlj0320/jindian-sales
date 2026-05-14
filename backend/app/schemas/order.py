"""
订单相关 Pydantic 模型
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    """创建订单明细"""
    item_type: str = Field(default="窗帘")
    product_id: int | None = None
    product_name: str = Field(default="")
    product_code: str = Field(default="")
    room: str = Field(default="")
    width: float = Field(default=0)
    height: float = Field(default=0)
    fold_ratio: float = Field(default=2.0)
    unit: str = Field(default="米")
    unit_price: float = Field(default=0)
    qty: float = Field(default=1)
    discount: float = Field(default=1.0)
    amount: float = Field(default=0)
    open_type: str = Field(default="")
    style_code: str = Field(default="")
    process_desc: str = Field(default="")
    classification: str = Field(default="")
    material_type: str = Field(default="主料")
    procurement_type: str = Field(default="物料")
    is_purchase: bool = Field(default=True, description="是否采购: False=跳过此明细不生成采购单")
    calc_type: str = Field(default="per_meter")
    panel_count: float = Field(default=0, description="幅数")
    supplier_id: int | None = None
    note: str = Field(default="")


class OrderCreate(BaseModel):
    """创建订单"""
    customer_id: int | None = None
    customer_name: str = Field(default="")
    customer_phone: str = Field(default="")
    order_type: str = Field(default="窗帘")
    order_date: str = Field(default="")
    delivery_date: str = Field(default="")
    delivery_method: str = Field(default="上门安装")
    salesperson_id: int | None = None
    salesperson_name: str = Field(default="")
    discount_amount: float = Field(default=0)
    round_amount: float = Field(default=0)
    discount_reason: str = Field(default="")
    received: float = Field(default=0)
    deposit_deduction: float = Field(default=0, description="定金抵扣金额")
    content: str = Field(default="")
    remark: str = Field(default="")
    install_address: str = Field(default="")
    install_date: str | None = None
    install_time_slot: str = Field(default="")
    items: list[OrderItemCreate] = Field(default_factory=list)


class OrderUpdate(BaseModel):
    """更新订单"""
    customer_name: str | None = None
    customer_phone: str | None = None
    order_type: str | None = None
    delivery_method: str | None = None
    delivery_date: str | None = None
    order_date: str | None = None
    salesperson_id: int | None = None
    discount_amount: float | None = None
    round_amount: float | None = None
    discount_reason: str | None = None
    received: float | None = None
    content: str | None = None
    remark: str | None = None
    install_address: str | None = None
    install_date: str | None = None
    install_time_slot: str | None = None
    items: list[OrderItemCreate] | None = None


class OrderStatusUpdate(BaseModel):
    """状态更新"""
    status_key: str = Field(..., description="目标状态key")


class OrderRollbackRequest(BaseModel):
    """异常回滚请求"""
    status_key: str = Field(..., description="目标状态key")
    remark: str = Field(default="", description="回滚原因说明，异常处理时必填")


class OrderItemResponse(BaseModel):
    id: int
    item_type: str
    product_id: int | None
    product_name: str
    product_code: str
    room: str
    width: float
    height: float
    fold_ratio: float
    unit: str
    unit_price: float
    qty: float
    discount: float
    amount: float
    final_amount: float
    open_type: str
    style_code: str
    process_desc: str
    classification: str
    calc_type: str = "per_meter"
    material_type: str
    procurement_type: str = "物料"
    is_purchase: bool = True
    panel_count: float = 0
    supplier_id: int | None = None
    supplier_name: str = ""
    note: str


class OrderListResponse(BaseModel):
    id: int
    order_no: str
    customer_name: str
    customer_phone: str
    order_type: str
    content: str
    amount: float
    received: float
    debt: float
    status_key: str
    status_label: str
    status_color: str
    order_date: str
    delivery_date: str
    salesperson_name: str
    created_at: str


class OrderDetailResponse(BaseModel):
    id: int
    order_no: str
    customer_id: int | None
    customer_name: str
    customer_phone: str
    order_type: str
    salesperson_id: int | None
    salesperson_name: str
    quote_amount: float
    discount_amount: float
    round_amount: float
    amount: float
    received: float
    debt: float
    discount_reason: str
    order_date: str
    delivery_date: str
    delivery_method: str
    status_key: str
    status_label: str
    status_color: str
    content: str
    remark: str
    install_address: str
    install_date: str | None
    install_time_slot: str
    history: list
    items: list[OrderItemResponse]
    created_at: str
