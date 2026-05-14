"""
仓库与库存 Pydantic 模型
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class WarehouseCreate(BaseModel):
    name: str = Field(..., description="仓库名称")
    code: str = Field(default="")
    address: str = Field(default="")
    warehouse_type: str = Field(default="main", description="仓库类型: main/auxiliary/finished")
    remark: str = Field(default="")


class WarehouseUpdate(BaseModel):
    """更新仓库"""
    name: str | None = None
    code: str | None = None
    address: str | None = None
    is_active: bool | None = None
    warehouse_type: str | None = None
    remark: str | None = None


class InventoryAdjust(BaseModel):
    """手动库存调整"""
    product_id: int = Field(..., description="产品ID")
    warehouse_id: int = Field(..., description="仓库ID")
    quantity: float = Field(..., description="调整数量（正数=入库，负数=出库）")
    remark: str = Field(default="库存手动调整")


class WarehouseResponse(BaseModel):
    id: int
    name: str
    code: str
    address: str
    is_active: bool
    remark: str


class InventoryResponse(BaseModel):
    product_id: int
    product_name: str
    product_code: str
    warehouse_id: int
    warehouse_name: str
    quantity: float
    safety_stock: float


class InventoryFlowResponse(BaseModel):
    id: int
    product_id: int
    product_name: str = ""
    flow_type: str
    qty_before: float
    qty_change: float
    qty_after: float
    ref_type: str
    ref_id: int | None
    remark: str
    created_at: str


# ─── 仓库三级分类 ───────────────────────────────────────


class StorageLocationCreate(BaseModel):
    """创建存储位置"""
    warehouse_id: int = Field(..., description="所属仓库ID")
    level: int = Field(..., description="层级: 1=区域, 2=货架, 3=库位")
    name: str = Field(..., description="名称")
    code: str = Field(default="")
    parent_id: int | None = Field(None, description="父级ID")


class StorageLocationUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    remark: str | None = None


class StorageLocationResponse(BaseModel):
    id: int
    warehouse_id: int
    level: int
    name: str
    code: str
    parent_id: int | None = None
    remark: str
    children: list[StorageLocationResponse] | None = None


class InventorySetLocation(BaseModel):
    """设置库存位置"""
    zone: str = Field(default="", description="区域")
    shelf: str = Field(default="", description="货架")
    bin: str = Field(default="", description="库位")
