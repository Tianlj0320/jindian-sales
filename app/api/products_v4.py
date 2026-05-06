# app/api/products_v4.py
# V4.0 产品管理 API（P0: 4个 + P1: 2个）
from datetime import datetime
from fastapi import APIRouter, Body, Path, Query
from sqlalchemy import and_, func, select

from app.core.response import success_response, error_response
from app.database import async_session
from app.models import Product, FabricCategory, Supplier

router = APIRouter(prefix="/api/v4/products", tags=["V4.0 产品管理"])


# ─── 产品列表 ─────────────────────────────────────────────────────────────────
@router.get("")
async def list_products_v4(
    keyword: str | None = Query(None, description="搜索：编码/名称/型号"),
    category_id: int | None = Query(None, alias="category_id"),
    product_type: str | None = Query(None, alias="product_type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    GET /api/v4/products - 产品列表（支持分类/类型筛选）
    product_type: 面料/辅料
    """
    async with async_session() as session:
        conditions = []
        if keyword:
            kw = f"%{keyword}%"
            conditions.append(
                (Product.code.ilike(kw))
                | (Product.name.ilike(kw))
                | (Product.model.ilike(kw))
            )
        if category_id:
            conditions.append(Product.category_id == category_id)
        if product_type:
            conditions.append(Product.product_type == product_type)

        where_clause = and_(*conditions) if conditions else True

        r = await session.execute(select(func.count(Product.id)).where(where_clause))
        total = r.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(Product)
            .where(where_clause)
            .order_by(Product.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(query)
        products = result.scalars().all()

        return success_response(
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [
                    {
                        "id": p.id,
                        "code": p.code or "",
                        "name": p.name or "",
                        "model": p.model or "",
                        "material": p.material or "",
                        "product_type": p.product_type or "",
                        "classification": p.classification or "",
                        "width": p.width or 0,
                        "weight": p.weight or 0,
                        "unit_price": float(p.unit_price or 0),
                        "unit": p.unit or "米",
                        "stock": p.stock or 0,
                        "category_id": p.category_id,
                        "supplier_id": p.supplier_id,
                        "series": p.series or "",
                        "remark": p.remark or "",
                    }
                    for p in products
                ],
            }
        )


# ─── 新建产品 ─────────────────────────────────────────────────────────────────
@router.post("")
async def create_product_v4(req: dict = Body(...)):
    """
    POST /api/v4/products - 新建产品
    Body: { code, name, model, material, product_type, classification,
            width, weight, unit_price, unit, category_id, supplier_id, series, remark }
    """
    if not req.get("name"):
        return error_response("产品名称不能为空")

    async with async_session() as session:
        # 检查编码重复
        if req.get("code"):
            r = await session.execute(
                select(Product).where(Product.code == req["code"])
            )
            if r.scalar_one_or_none():
                return error_response("产品编码已存在")

        product = Product(
            code=req.get("code", ""),
            name=req.get("name", ""),
            model=req.get("model", ""),
            material=req.get("material", ""),
            product_type=req.get("product_type", "面料"),
            classification=req.get("classification", ""),
            width=req.get("width", 0),
            weight=req.get("weight", 0),
            unit_price=req.get("unit_price", 0),
            unit=req.get("unit", "米"),
            stock=req.get("stock", 0),
            cost_price=req.get("cost_price", 0),
            min_price=req.get("min_price", 0),
            selling_price=req.get("selling_price", 0),
            category_id=req.get("category_id"),
            supplier_id=req.get("supplier_id"),
            series=req.get("series", ""),
            remark=req.get("remark", ""),
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)

        return success_response(data={"id": product.id, "code": product.code})


# ─── 产品详情 ─────────────────────────────────────────────────────────────────
@router.get("/{product_id}", response_model=dict)
async def get_product_v4(product_id: int = Path(...)):
    """GET /api/v4/products/{id} - 产品详情"""
    async with async_session() as session:
        r = await session.execute(select(Product).where(Product.id == product_id))
        p = r.scalar_one_or_none()
        if not p:
            return error_response("产品不存在")

        # 获取分类和供应商名称
        category_name = ""
        supplier_name = ""
        if p.category_id:
            cr = await session.execute(select(FabricCategory).where(FabricCategory.id == p.category_id))
            cat = cr.scalar_one_or_none()
            if cat:
                category_name = cat.name or ""
        if p.supplier_id:
            sr = await session.execute(select(Supplier).where(Supplier.id == p.supplier_id))
            sup = sr.scalar_one_or_none()
            if sup:
                supplier_name = sup.name or ""

        return success_response(
            data={
                "id": p.id,
                "code": p.code or "",
                "name": p.name or "",
                "model": p.model or "",
                "material": p.material or "",
                "product_type": p.product_type or "",
                "classification": p.classification or "",
                "width": p.width or 0,
                "weight": p.weight or 0,
                "cf": p.cf or 0,
                "unit_price": float(p.unit_price or 0),
                "cost_price": float(getattr(p, "cost_price", 0) or 0),
                "min_price": float(getattr(p, "min_price", 0) or 0),
                "selling_price": float(getattr(p, "selling_price", 0) or 0),
                "unit": p.unit or "米",
                "stock": p.stock or 0,
                "category_id": p.category_id,
                "category_name": category_name,
                "supplier_id": p.supplier_id,
                "supplier_name": supplier_name,
                "series": p.series or "",
                "remark": p.remark or "",
            }
        )


# ─── 更新产品 ─────────────────────────────────────────────────────────────────
@router.put("/{product_id}")
async def update_product_v4(product_id: int = Path(...), req: dict = Body(...)):
    """
    PUT /api/v4/products/{id} - 更新产品
    可更新字段: name, model, material, product_type, classification,
               width, weight, unit_price, unit, category_id, supplier_id, series, remark
    """
    async with async_session() as session:
        r = await session.execute(select(Product).where(Product.id == product_id))
        p = r.scalar_one_or_none()
        if not p:
            return error_response("产品不存在")

        for field in [
            "name", "model", "material", "product_type", "classification",
            "width", "weight", "unit_price", "unit", "series", "remark",
        ]:
            if field in req:
                setattr(p, field, req[field])

        if "category_id" in req:
            p.category_id = req["category_id"]
        if "supplier_id" in req:
            p.supplier_id = req["supplier_id"]

        await session.commit()
        return success_response(data={"id": product_id})


# ══════════════════════════════════════════════════════════════
# P1: 价格三角校验 + 库存调拨
# ══════════════════════════════════════════════════════════════


# ─── 更新产品价格（含价格三角校验）─────────────────────────────────────────
@router.put("/{product_id}/price")
async def update_product_price(product_id: int = Path(...), req: dict = Body(...)):
    """
    PUT /api/v4/products/{id}/price - 更新产品价格（价格三角校验）
    规则: selling_price >= min_price >= cost_price
    Body: { cost_price, min_price, selling_price }
    """
    async with async_session() as session:
        r = await session.execute(select(Product).where(Product.id == product_id))
        p = r.scalar_one_or_none()
        if not p:
            return error_response("产品不存在")

        # 获取当前值（用于部分更新）
        cur_cost = float(getattr(p, "cost_price", 0) or 0)
        cur_min = float(getattr(p, "min_price", 0) or 0)
        cur_sell = float(getattr(p, "selling_price", 0) or 0)

        # 只更新传入的字段（部分更新）
        new_cost = float(req.get("cost_price", cur_cost) or cur_cost)
        new_min = float(req.get("min_price", cur_min) or cur_min)
        new_sell = float(req.get("selling_price", cur_sell) or cur_sell)

        # 价格三角校验（用新值）
        if new_min < new_cost:
            return error_response(f"最低售价({new_min})不能小于成本价({new_cost})")
        if new_sell < new_min:
            return error_response(f"销售单价({new_sell})不能小于最低售价({new_min})")

        # 应用更新（只更新传了值的字段）
        if "cost_price" in req:
            p.cost_price = new_cost
        if "min_price" in req:
            p.min_price = new_min
        if "selling_price" in req:
            p.selling_price = new_sell

        await session.commit()
        return success_response(
            data={
                "id": product_id,
                "cost_price": new_cost,
                "min_price": new_min,
                "selling_price": new_sell,
            }
        )


# ─── 库存调拨 ──────────────────────────────────────────────────────────────
# 注意：此接口已迁移至 /api/v4/inventory/transfer
# 为避免路由冲突，此处保留空实现