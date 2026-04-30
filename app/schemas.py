# app/schemas.py

from pydantic import BaseModel

# ─── Track API ────────────────────────────────────────────────────────────────


class StatusHistoryItem(BaseModel):
    step: int
    key: str
    label: str
    time: str | None = None
    done: bool
    is_current: bool = False


class NextStep(BaseModel):
    type: str
    label: str
    date: str | None = None
    time_slot: str | None = None
    installer_name: str | None = None
    installer_phone_masked: str | None = None


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
    status_history: list[StatusHistoryItem]
    next_step: NextStep | None = None
    order_items: list[OrderItem]
    store_phone: str


class TrackResponse(BaseModel):
    success: bool
    data: TrackResponseData | None = None
    error: str | None = None


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
    data: LoginResponseData | None = None
    error: str | None = None


# ─── SMS API ─────────────────────────────────────────────────────────────────


class SmsSendRequest(BaseModel):
    phone: str
    type: str = "installer_login"


class SmsResponseData(BaseModel):
    code: str
    expires_in: int


class SmsResponse(BaseModel):
    success: bool
    data: SmsResponseData | None = None
    error: str | None = None


# ─── Installer Tasks API ─────────────────────────────────────────────────────


class TaskItem(BaseModel):
    id: int
    order_no: str
    customer_name: str
    customer_phone_masked: str
    raw_customer_phone: str | None = None  # 仅App端返回
    address: str
    content: str | None = None
    time_slot: str | None = None
    priority: str
    status: str
    navigate_url: str | None = None


class TasksResponseData(BaseModel):
    installer_name: str
    date: str
    today_completed: int
    today_pending: int
    tasks: list[TaskItem]


class TasksResponse(BaseModel):
    success: bool
    data: TasksResponseData | None = None
    error: str | None = None


# ─── Complete Task API ───────────────────────────────────────────────────────


class CompleteRequest(BaseModel):
    completed_at: str
    remark: str | None = ""


class CompleteResponseData(BaseModel):
    task_id: int
    order_status_key: str
    completed_at: str


class CompleteResponse(BaseModel):
    success: bool
    data: CompleteResponseData | None = None
    error: str | None = None


# ─── History API ─────────────────────────────────────────────────────────────


class HistoryRecord(BaseModel):
    id: int
    order_no: str
    customer_name: str
    address: str
    content: str | None = None
    completed_at: str
    remark: str | None = None


class HistoryResponseData(BaseModel):
    monthly_completed: int
    monthly_pending: int
    total: int
    page: int
    page_size: int
    records: list[HistoryRecord]


class HistoryResponse(BaseModel):
    success: bool
    data: HistoryResponseData | None = None
    error: str | None = None


# ─── 通用响应 ────────────────────────────────────────────────────────────────


class CommonData(BaseModel):
    id: int


class CommonResponse(BaseModel):
    success: bool
    data: dict | None = None
    error: str | None = None


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
    items: list[dict]


class OrderListResponse(BaseModel):
    success: bool
    total: int
    page: int
    page_size: int
    items: list[OrderListItem]


class OrderDetailData(BaseModel):
    id: int
    order_no: str
    customer_id: int | None
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
    history: list[dict]
    items: list[dict]
    install_address: str
    install_date: str
    install_time_slot: str
    created_at: str


class OrderResponse(BaseModel):
    success: bool
    data: OrderDetailData | None = None
    error: str | None = None


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
    items: list[CustomerListItem]


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
    data: CustomerDetailData | None = None
    error: str | None = None


# ─── 产品 ─────────────────────────────────────────────────────────────────


class ProductListItem(BaseModel):
    id: int
    code: str
    name: str
    supplier_id: int
    supplier_name: str
    category_id: int
    category_name: str
    product_type: str
    classification: str = ""
    model: str = ""
    material: str
    series: str = ""
    width: int = 280
    weight: int = 0
    cf: int = 0
    unit_price: float
    stock: int
    unit: str
    remark: str = ""


class ProductListResponse(BaseModel):
    success: bool
    total: int
    page: int
    page_size: int
    items: list[ProductListItem]


class ProductDetailData(BaseModel):
    id: int
    code: str
    name: str
    supplier_id: int
    supplier_name: str
    category_id: int
    category_name: str
    product_type: str
    classification: str = ""
    model: str = ""
    material: str
    series: str = ""
    width: int = 280
    weight: int = 0
    cf: int = 0
    unit_price: float
    unit: str
    stock: int
    remark: str = ""


class ProductResponse(BaseModel):
    success: bool
    data: ProductDetailData | None = None
    error: str | None = None


# ─── 供应商 ─────────────────────────────────────────────────────────────────


class SupplierListItem(BaseModel):
    id: int
    code: str
    name: str
    type: str
    contact: str
    phone: str
    delivery_days: int
    address: str = ""
    payment: str = ""


class SupplierListResponse(BaseModel):
    success: bool
    total: int
    items: list[SupplierListItem]


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
    items: list[EmployeeListItem]


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
    data: DashboardData | None = None
