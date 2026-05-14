"""
产品相关 Pydantic 模型
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., description="分类名称")
    code: str = Field(default="")
    parent_id: int | None = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    """更新分类"""
    name: str | None = None
    code: str | None = None
    parent_id: int | None = None
    sort_order: int | None = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    code: str
    parent_id: int | None
    sort_order: int
    children: list["CategoryResponse"] = []


class SupplierCreate(BaseModel):
    """创建供应商"""
    name: str = Field(..., description="供应商名称")
    code: str = Field(default="")
    type: str = Field(default="布艺")
    contact: str = Field(default="")
    phone: str = Field(default="")
    address: str = Field(default="")
    delivery_days: int = Field(default=7)
    payment_terms: str = Field(default="")
    qq: str = Field(default="")
    wechat: str = Field(default="")
    bank_account: str = Field(default="")
    bank_name: str = Field(default="")
    payee: str = Field(default="")


class SupplierUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    type: str | None = None
    contact: str | None = None
    phone: str | None = None
    address: str | None = None
    delivery_days: int | None = None
    payment_terms: str | None = None
    qq: str | None = None
    wechat: str | None = None
    bank_account: str | None = None
    bank_name: str | None = None
    payee: str | None = None
    is_active: bool | None = None


class SupplierResponse(BaseModel):
    id: int
    name: str
    code: str
    type: str
    contact: str
    phone: str
    address: str
    delivery_days: int
    payment_terms: str
    qq: str = ""
    wechat: str = ""
    bank_account: str = ""
    bank_name: str = ""
    payee: str = ""
    is_active: bool


class SeriesCreate(BaseModel):
    """创建系列/木板"""
    name: str = Field(..., description="系列名称")
    code: str = Field(default="")
    supplier_id: int = Field(..., description="所属供应商ID")
    sort_order: int = 0


class SeriesUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    supplier_id: int | None = None
    sort_order: int | None = None


class SeriesResponse(BaseModel):
    id: int
    name: str
    code: str = ""
    supplier_id: int
    sort_order: int = 0


class ProductCreate(BaseModel):
    """创建产品"""
    code: str = Field(default="")
    name: str = Field(..., description="产品名称")
    product_type: str = Field(default="面料")
    classification: str = Field(default="")
    category_id: int | None = None
    supplier_id: int | None = None
    series_id: int | None = None
    processing_type_id: int | None = None
    model: str = Field(default="")
    material: str = Field(default="")
    color: str = Field(default="")
    pattern: str = Field(default="")
    width: int = Field(default=280)
    standard_width: float = Field(default=0, description="门幅(m)")
    weight: int = Field(default=0)
    fold_ratio: float = Field(default=2.0)
    unit: str = Field(default="米")
    calc_type: str = Field(default="per_meter", description="计价方式: per_meter/per_square/per_window/fixed")
    cost_price: float = Field(default=0)
    min_price: float = Field(default=0)
    selling_price: float = Field(default=0)
    stock: int = Field(default=0)
    safety_stock: int = Field(default=0)
    series: str = Field(default="")
    is_purchase: bool = Field(default=True, description="True=需采购生成采购单, False=外加工单位负责不生成采购单")
    remark: str | None = None


class ProductUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    product_type: str | None = None
    classification: str | None = None
    category_id: int | None = None
    supplier_id: int | None = None
    series_id: int | None = None
    processing_type_id: int | None = None
    model: str | None = None
    material: str | None = None
    color: str | None = None
    pattern: str | None = None
    width: int | None = None
    standard_width: float | None = None
    weight: int | None = None
    fold_ratio: float | None = None
    unit: str | None = None
    calc_type: str | None = None
    cost_price: float | None = None
    min_price: float | None = None
    selling_price: float | None = None
    stock: int | None = None
    safety_stock: int | None = None
    is_purchase: bool | None = None
    series: str | None = None
    remark: str | None = None


class ProductResponse(BaseModel):
    id: int
    code: str
    name: str
    product_type: str
    classification: str
    category_id: int | None
    category_name: str = ""
    supplier_id: int | None
    supplier_name: str = ""
    series_id: int | None = None
    series_name: str = ""
    processing_type_id: int | None = None
    processing_type_name: str = ""
    model: str
    material: str
    color: str = ""
    pattern: str = ""
    width: int
    standard_width: float = 0
    weight: int
    fold_ratio: float
    unit: str
    calc_type: str = "per_meter"
    cost_price: float
    min_price: float
    selling_price: float
    stock: int
    safety_stock: int
    is_purchase: bool = True
    series: str
    is_active: bool
    remark: str | None
