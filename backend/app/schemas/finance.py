"""
财务管理 Pydantic 模型
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReceivableResponse(BaseModel):
    """应收款响应"""
    id: int
    order_id: int
    order_no: str
    customer_name: str
    total_amount: float
    received_amount: float
    unpaid_amount: float
    status: str
    due_date: str | None
    remark: str
    created_at: str


class PayableResponse(BaseModel):
    """应付款响应"""
    id: int
    ref_type: str
    ref_id: int
    supplier_name: str
    total_amount: float
    paid_amount: float
    unpaid_amount: float
    status: str
    due_date: str | None
    remark: str
    created_at: str


class ExpenseCreate(BaseModel):
    """创建费用"""
    category: str = Field(..., description="费用类型")
    amount: float = Field(..., gt=0, description="金额")
    expense_date: str = Field(..., description="费用日期")
    remark: str = Field(default="")


class ExpenseUpdate(BaseModel):
    """更新费用"""
    category: str | None = None
    amount: float | None = Field(None, gt=0, description="金额")
    expense_date: str | None = None
    remark: str | None = None


class ExpenseResponse(BaseModel):
    id: int
    category: str
    amount: float
    expense_date: str
    operator_id: int | None
    remark: str
    created_at: str


class ReceivePayment(BaseModel):
    """收款确认"""
    order_id: int = Field(..., description="订单ID")
    amount: float = Field(..., gt=0, description="收款金额")
    method: str = Field(default="转账", description="收款方式")
    payment_type: str = Field(default="收款", description="收款类型: 定金/进度款/尾款/其他")
    remark: str = Field(default="")


class PayPayment(BaseModel):
    """付款确认"""
    ref_type: str = Field(..., description="关联类型: purchase/installation")
    ref_id: int = Field(..., description="关联ID")
    amount: float = Field(..., gt=0, description="付款金额")
    method: str = Field(default="转账", description="付款方式")
    remark: str = Field(default="")


class FinanceSummary(BaseModel):
    """财务摘要"""
    total_receivable: float = 0
    total_received: float = 0
    total_unpaid: float = 0
    total_payable: float = 0
    total_paid: float = 0
    total_unpaid_payable: float = 0
    month_received: float = 0
    month_paid: float = 0
    month_expense: float = 0
