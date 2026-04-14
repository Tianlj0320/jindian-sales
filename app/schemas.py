# app/schemas.py
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List


# ─── Track API ────────────────────────────────────────────────────────────────

class StatusHistoryItem(BaseModel):
    step: int
    key: str
    label: str
    time: Optional[str] = None
    done: bool
    is_current: bool = False


class NextStep(BaseModel):
    type: str
    label: str
    date: Optional[str] = None
    time_slot: Optional[str] = None
    installer_name: Optional[str] = None
    installer_phone_masked: Optional[str] = None


class OrderItem(BaseModel):
    room: str
    product: str
    qty: int


class TrackResponseData(BaseModel):
    order_no: str
    customer_name: str
    customer_phone_masked: str
    order_type: str
    amount: float
    received: float
    status_key: str
    status_label: str
    progress_step: int
    progress_total: int
    status_history: List[StatusHistoryItem]
    next_step: Optional[NextStep] = None
    order_items: List[OrderItem]
    store_phone: str


class TrackResponse(BaseModel):
    success: bool
    data: Optional[TrackResponseData] = None
    error: Optional[str] = None


# ─── Installer Login API ─────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    phone: str
    code: str


class InstallerInfo(BaseModel):
    id: int
    name: str
    phone_masked: str


class LoginResponseData(BaseModel):
    token: str
    expires_in: int
    installer: InstallerInfo


class LoginResponse(BaseModel):
    success: bool
    data: Optional[LoginResponseData] = None
    error: Optional[str] = None


# ─── SMS API ─────────────────────────────────────────────────────────────────

class SmsSendRequest(BaseModel):
    phone: str
    type: str = "installer_login"


class SmsResponseData(BaseModel):
    code: str
    expires_in: int


class SmsResponse(BaseModel):
    success: bool
    data: Optional[SmsResponseData] = None
    error: Optional[str] = None


# ─── Installer Tasks API ─────────────────────────────────────────────────────

class TaskItem(BaseModel):
    id: int
    order_no: str
    customer_name: str
    customer_phone_masked: str
    raw_customer_phone: Optional[str] = None  # 仅App端返回
    address: str
    content: Optional[str] = None
    time_slot: Optional[str] = None
    priority: str
    status: str
    navigate_url: Optional[str] = None


class TasksResponseData(BaseModel):
    installer_name: str
    date: str
    today_completed: int
    today_pending: int
    tasks: List[TaskItem]


class TasksResponse(BaseModel):
    success: bool
    data: Optional[TasksResponseData] = None
    error: Optional[str] = None


# ─── Complete Task API ───────────────────────────────────────────────────────

class CompleteRequest(BaseModel):
    completed_at: str
    remark: Optional[str] = ""


class CompleteResponseData(BaseModel):
    task_id: int
    order_status_key: str
    completed_at: str


class CompleteResponse(BaseModel):
    success: bool
    data: Optional[CompleteResponseData] = None
    error: Optional[str] = None


# ─── History API ─────────────────────────────────────────────────────────────

class HistoryRecord(BaseModel):
    id: int
    order_no: str
    customer_name: str
    address: str
    content: Optional[str] = None
    completed_at: str
    remark: Optional[str] = None


class HistoryResponseData(BaseModel):
    monthly_completed: int
    monthly_pending: int
    total: int
    page: int
    page_size: int
    records: List[HistoryRecord]


class HistoryResponse(BaseModel):
    success: bool
    data: Optional[HistoryResponseData] = None
    error: Optional[str] = None


# ─── 通用响应 ────────────────────────────────────────────────────────────────

class CommonData(BaseModel):
    id: int

class CommonResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


# ─── 订单 ─────────────────────────────────────────────────────────────────

class OrderListItem(BaseModel):
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
    salesperson: str
    install_date: str
    items: List[dict]

class OrderListResponse(BaseModel):
    success: bool
    total: int
    page: int
    page_size: int
    items: List[OrderListItem]

class OrderDetailData(BaseModel):
    id: int
    order_no: str
    customer_id: Optional[int]
    customer_name: str
    customer_phone: str
    order_type: str
    status_key: str
    status_label: str
    status_color: str
    amount: float
    quote_amount: float
    discount_amount: float
    round_amount: float
    received: float
    debt: float
    order_date: str
    delivery_date: str
    delivery_method: str
    content: str
    salesperson: str
    history: List[dict]
    items: List[dict]
    install_address: str
    install_date: str
    install_time_slot: str
    created_at: str

class OrderResponse(BaseModel):
    success: bool
    data: Optional[OrderDetailData] = None
    error: Optional[str] = None


# ─── 客户 ─────────────────────────────────────────────────────────────────

class CustomerListItem(BaseModel):
    id: int
    name: str
    phone: str
    type: str
    address: str
    community: str
    source: str
    salesperson: str
    debt: float
    created_at: str

class CustomerListResponse(BaseModel):
    success: bool
    total: int
    page: int
    page_size: int
    items: List[CustomerListItem]

class CustomerDetailData(BaseModel):
    id: int
    name: str
    phone: str
    type: str
    address: str
    community: str
    source: str
    salesperson: str
    debt: float
    created_at: str

class CustomerResponse(BaseModel):
    success: bool
    data: Optional[CustomerDetailData] = None
    error: Optional[str] = None


# ─── 产品 ─────────────────────────────────────────────────────────────────

class ProductListItem(BaseModel):
    id: int
    code: str
    name: str
    supplier_name: str
    category_name: str
    product_type: str
    material: str
    unit_price: float
    stock: int
    unit: str

class ProductListResponse(BaseModel):
    success: bool
    total: int
    page: int
    page_size: int
    items: List[ProductListItem]

class ProductDetailData(BaseModel):
    id: int
    code: str
    name: str
    supplier_id: int
    supplier_name: str
    category_id: int
    category_name: str
    product_type: str
    classification: str
    model: str
    material: str
    width: int
    weight: int
    unit_price: float
    unit: str
    stock: int

class ProductResponse(BaseModel):
    success: bool
    data: Optional[ProductDetailData] = None
    error: Optional[str] = None


# ─── 供应商 ─────────────────────────────────────────────────────────────────

class SupplierListItem(BaseModel):
    id: int
    code: str
    name: str
    type: str
    contact: str
    phone: str
    delivery_days: int

class SupplierListResponse(BaseModel):
    success: bool
    total: int
    items: List[SupplierListItem]


# ─── 员工 ─────────────────────────────────────────────────────────────────

class EmployeeListItem(BaseModel):
    id: int
    code: str
    name: str
    gender: str
    phone: str
    position: str
    department: str
    max_discount: float
    round_limit: int
    is_installer: bool
    status: str

class EmployeeListResponse(BaseModel):
    success: bool
    total: int
    items: List[EmployeeListItem]


# ─── 首页统计 ────────────────────────────────────────────────────────────────

class DashboardData(BaseModel):
    today_orders: int
    month_sales: float
    pending_install: int
    overdue_orders: int
    pending_payment: int
    total_customers: int

class DashboardResponse(BaseModel):
    success: bool
    data: Optional[DashboardData] = None
