"""
日报/资金日报 Pydantic 模型
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DepositItem(BaseModel):
    """定金条目"""
    customer_name: str = ""
    amount: float = 0
    payment_method: str = ""
    has_order: bool = False
    order_no: str | None = None


class DepositSummary(BaseModel):
    """定金汇总"""
    today_total: float = 0
    items: list[DepositItem] = []


class NewOrderItem(BaseModel):
    """新订单条目"""
    id: int
    order_no: str
    customer_name: str
    amount: float


class NewOrderSummary(BaseModel):
    """新订单汇总"""
    count: int = 0
    total_amount: float = 0
    items: list[NewOrderItem] = []


class PendingPurchaseItem(BaseModel):
    """待采购条目"""
    order_no: str = ""
    customer_name: str = ""
    suppliers: list[str] = []


class PendingPurchaseSummary(BaseModel):
    """待采购汇总"""
    count: int = 0
    items: list[PendingPurchaseItem] = []


class PendingInstallationItem(BaseModel):
    """待安装条目"""
    order_no: str = ""
    customer_name: str = ""
    install_date: str | None = None


class PendingInstallationSummary(BaseModel):
    """待安装汇总"""
    count: int = 0
    items: list[PendingInstallationItem] = []


class CollectionItem(BaseModel):
    """收款条目"""
    customer_name: str = ""
    amount: float = 0
    payment_method: str = ""
    order_no: str = ""


class CollectionSummary(BaseModel):
    """收款汇总"""
    today_total: float = 0
    items: list[CollectionItem] = []


class DailyReportResponse(BaseModel):
    """日报响应"""
    date: str = ""
    deposits: DepositSummary = Field(default_factory=DepositSummary)
    new_orders: NewOrderSummary = Field(default_factory=NewOrderSummary)
    pending_purchases: PendingPurchaseSummary = Field(default_factory=PendingPurchaseSummary)
    pending_installations: PendingInstallationSummary = Field(default_factory=PendingInstallationSummary)
    collections: CollectionSummary = Field(default_factory=CollectionSummary)


class HistoryReportItem(BaseModel):
    """历史日报条目"""
    date: str = ""
    deposits_total: float = 0
    orders_count: int = 0
    orders_total: float = 0
    collections_total: float = 0


class UnlinkedDepositItem(BaseModel):
    """未关联订单的定金条目"""
    id: int
    customer_id: int
    customer_name: str
    amount: float
    balance: float
    payment_method: str
    received_at: str | None
    operator_name: str
    remark: str
