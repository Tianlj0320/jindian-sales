"""
加工类型与辅料规则 Pydantic 模型
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProcessingMaterialRuleCreate(BaseModel):
    """创建辅料规则"""
    material_name: str = Field(..., description="辅料名称")
    default_product_name: str = Field(default="")
    product_id: int | None = None
    unit: str = Field(default="米")
    qty_formula: str = Field(default="1", description="数量计算公式")
    unit_price: float = Field(default=0, description="默认单价")
    sort_order: int = Field(default=0)
    is_required: bool = Field(default=True)


class ProcessingMaterialRuleUpdate(BaseModel):
    material_name: str | None = None
    default_product_name: str | None = None
    product_id: int | None = None
    unit: str | None = None
    qty_formula: str | None = None
    unit_price: float | None = None
    sort_order: int | None = None
    is_required: bool | None = None


class ProcessingMaterialRuleResponse(BaseModel):
    id: int
    processing_type_id: int
    material_name: str
    default_product_name: str = ""
    product_id: int | None = None
    unit: str = "米"
    qty_formula: str = "1"
    unit_price: float = 0
    sort_order: int = 0
    is_required: bool = True


class ProcessingTypeCreate(BaseModel):
    """创建加工类型"""
    name: str = Field(..., description="加工类型名称")
    code: str = Field(..., description="编码")
    description: str = Field(default="")
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    rules: list[ProcessingMaterialRuleCreate] = Field(default_factory=list)


class ProcessingTypeUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class ProcessingTypeResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str = ""
    sort_order: int = 0
    is_active: bool = True
    rules: list[ProcessingMaterialRuleResponse] = []
