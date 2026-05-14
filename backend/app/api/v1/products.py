"""
产品资料 API（产品、分类、供应商）
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.exceptions import NotFoundError
from app.core.response import paginated, success
from app.domain.product import Product, ProductCategory, ProductSeries, Supplier
from app.domain.processing import ProcessingType
from app.schemas.product import (
    CategoryCreate,
    CategoryUpdate,
    ProductCreate,
    ProductUpdate,
    SeriesCreate,
    SeriesUpdate,
    SupplierCreate,
    SupplierUpdate,
)

router = APIRouter(prefix="/api/v1/products", tags=["产品资料"])


# ══════════════════════════════════════════════════════════════
# 产品搜索（轻量级，用于下拉提示）
# ══════════════════════════════════════════════════════════════


@router.get("/search")
async def search_products(
    session: SessionDep,
    current_user: CurrentUserDep,
    keyword: str = Query("", description="搜索编码或名称"),
):
    """产品搜索（轻量级，用于订单明细中的自动补全）"""
    conditions = [Product.is_active == True]
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(or_(Product.code.ilike(kw), Product.name.ilike(kw)))

    result = await session.execute(
        select(Product).where(and_(*conditions)).order_by(Product.id.desc()).limit(20)
    )
    products = result.scalars().all()

    return success(data=[
        {
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "product_type": p.product_type,
            "unit": p.unit,
            "selling_price": float(p.selling_price),
            "unit_price": float(p.selling_price),
            "width": p.width,
            "standard_width": float(p.standard_width),
            "fold_ratio": float(p.fold_ratio),
            "classification": p.classification,
            "calc_type": p.calc_type,
            "processing_type_id": p.processing_type_id,
            "supplier_id": p.supplier_id,
            "supplier_name": p.supplier.name if p.supplier else None,
            "supplier_code": p.supplier.code if p.supplier else None,
            "series_id": p.series_id,
            "series_name": p.series_rel.name if p.series_rel else "",
            "is_purchase": p.is_purchase if hasattr(p, 'is_purchase') else True,
        }
        for p in products
    ])


# ══════════════════════════════════════════════════════════════
# 产品分类
# ══════════════════════════════════════════════════════════════


@router.get("/categories")
async def list_categories(session: SessionDep, current_user: CurrentUserDep):
    """分类列表（树形结构）"""
    result = await session.execute(
        select(ProductCategory).order_by(ProductCategory.sort_order, ProductCategory.id)
    )
    categories = result.scalars().all()

    # 构建树
    cat_map = {}
    tree = []
    for cat in categories:
        node = {"id": cat.id, "name": cat.name, "code": cat.code, "parent_id": cat.parent_id, "children": []}
        cat_map[cat.id] = node
        if cat.parent_id is None:
            tree.append(node)
        else:
            parent = cat_map.get(cat.parent_id)
            if parent:
                parent["children"].append(node)

    return success(data=tree)


@router.post("/categories")
async def create_category(session: SessionDep, current_user: CurrentUserDep, req: CategoryCreate):
    """创建分类"""
    cat = ProductCategory(
        name=req.name,
        code=req.code,
        parent_id=req.parent_id,
        sort_order=req.sort_order,
    )
    session.add(cat)
    await session.flush()
    return success(data={"id": cat.id}, message="分类创建成功")


@router.put("/categories/{category_id}")
async def update_category(
    session: SessionDep, current_user: CurrentUserDep, category_id: int, req: CategoryUpdate
):
    """更新分类"""
    result = await session.execute(select(ProductCategory).where(ProductCategory.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise NotFoundError("分类不存在")

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(cat, field, value)
    await session.flush()
    return success(data={"id": category_id}, message="分类更新成功")


@router.delete("/categories/{category_id}")
async def delete_category(session: SessionDep, current_user: CurrentUserDep, category_id: int):
    """删除分类"""
    result = await session.execute(select(ProductCategory).where(ProductCategory.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise NotFoundError("分类不存在")

    # 检查是否有产品使用此分类
    prod_count = (await session.execute(
        select(func.count()).select_from(Product).where(Product.category_id == category_id)
    )).scalar() or 0
    if prod_count > 0:
        from app.core.exceptions import BusinessError
        raise BusinessError(f"该分类下有 {prod_count} 个产品，无法删除")

    await session.delete(cat)
    await session.flush()
    return success(message="分类已删除")


# ══════════════════════════════════════════════════════════════
# 供应商
# ══════════════════════════════════════════════════════════════


@router.get("/suppliers/all")
async def list_all_suppliers(session: SessionDep, current_user: CurrentUserDep):
    """所有供应商列表（无分页，用于左侧树形面板）"""
    result = await session.execute(
        select(Supplier).where(Supplier.is_active == True).order_by(Supplier.code, Supplier.id)
    )
    suppliers = result.scalars().all()
    return success(data=[
        {"id": s.id, "name": s.name, "code": s.code or "", "type": s.type}
        for s in suppliers
    ])


@router.get("/suppliers")
async def list_suppliers(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    keyword: str | None = Query(None, description="搜索名称/联系人/手机号"),
    type: str | None = Query(None, description="类型: 布艺/成品/配件/其他"),
):
    """供应商列表（支持关键字搜索和类型筛选）"""
    conditions = []
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(or_(
            Supplier.code.ilike(kw),
            Supplier.name.ilike(kw),
            Supplier.contact.ilike(kw),
            Supplier.phone.ilike(kw),
        ))
    if type:
        conditions.append(Supplier.type == type)

    where = and_(*conditions) if conditions else True
    total = (await session.execute(select(func.count()).select_from(Supplier).where(where))).scalar() or 0

    result = await session.execute(
        select(Supplier).where(where).order_by(Supplier.id).offset(page.offset).limit(page.page_size)
    )
    suppliers = result.scalars().all()

    return paginated(
        items=[
            {
                "id": s.id,
                "name": s.name,
                "code": s.code,
                "type": s.type,
                "contact": s.contact,
                "phone": s.phone,
                "address": s.address,
                "delivery_days": s.delivery_days,
                "payment_terms": s.payment_terms,
                "qq": s.qq or "",
                "wechat": s.wechat or "",
                "bank_account": s.bank_account or "",
                "bank_name": s.bank_name or "",
                "payee": s.payee or "",
                "is_active": s.is_active,
            }
            for s in suppliers
        ],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/suppliers")
async def create_supplier(session: SessionDep, current_user: CurrentUserDep, req: SupplierCreate):
    """创建供应商"""
    supplier = Supplier(**req.model_dump())
    session.add(supplier)
    await session.flush()
    return success(data={"id": supplier.id}, message="供应商创建成功")


@router.put("/suppliers/{supplier_id}")
async def update_supplier(
    session: SessionDep, current_user: CurrentUserDep, supplier_id: int, req: SupplierUpdate
):
    """更新供应商"""
    result = await session.execute(select(Supplier).where(Supplier.id == supplier_id))
    s = result.scalar_one_or_none()
    if not s:
        raise NotFoundError("供应商不存在")

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(s, field, value)
    await session.flush()
    return success(data={"id": supplier_id}, message="供应商更新成功")


@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(session: SessionDep, current_user: CurrentUserDep, supplier_id: int):
    """删除供应商"""
    result = await session.execute(select(Supplier).where(Supplier.id == supplier_id))
    s = result.scalar_one_or_none()
    if not s:
        raise NotFoundError("供应商不存在")
    await session.delete(s)
    await session.flush()
    return success(message="供应商已删除")


# ══════════════════════════════════════════════════════════════
# 系列/木板（二级分类，隶属于供应商）
# ══════════════════════════════════════════════════════════════


@router.get("/series")
async def list_series(
    session: SessionDep,
    current_user: CurrentUserDep,
    supplier_id: int | None = Query(None, description="按供应商筛选"),
):
    """系列列表（可按供应商筛选）"""
    conditions = []
    if supplier_id is not None:
        conditions.append(ProductSeries.supplier_id == supplier_id)

    where = and_(*conditions) if conditions else True
    result = await session.execute(
        select(ProductSeries).where(where).order_by(ProductSeries.sort_order, ProductSeries.id)
    )
    series_list = result.scalars().all()

    return success(data=[
        {
            "id": s.id,
            "name": s.name,
            "code": s.code or "",
            "supplier_id": s.supplier_id,
            "sort_order": s.sort_order,
            "product_count": 0,  # 前端自行统计或后续优化
        }
        for s in series_list
    ])


@router.post("/series")
async def create_series(session: SessionDep, current_user: CurrentUserDep, req: SeriesCreate):
    """创建系列/木板"""
    series = ProductSeries(name=req.name, code=req.code, supplier_id=req.supplier_id, sort_order=req.sort_order)
    session.add(series)
    await session.flush()
    return success(data={"id": series.id}, message="系列创建成功")


@router.put("/series/{series_id}")
async def update_series(
    session: SessionDep, current_user: CurrentUserDep, series_id: int, req: SeriesUpdate
):
    """更新系列/木板"""
    result = await session.execute(select(ProductSeries).where(ProductSeries.id == series_id))
    s = result.scalar_one_or_none()
    if not s:
        raise NotFoundError("系列不存在")

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(s, field, value)
    await session.flush()
    return success(data={"id": series_id}, message="系列更新成功")


@router.delete("/series/{series_id}")
async def delete_series(session: SessionDep, current_user: CurrentUserDep, series_id: int):
    """删除系列/木板"""
    result = await session.execute(select(ProductSeries).where(ProductSeries.id == series_id))
    s = result.scalar_one_or_none()
    if not s:
        raise NotFoundError("系列不存在")

    # 检查是否有产品使用此系列
    prod_count = (await session.execute(
        select(func.count()).select_from(Product).where(Product.series_id == series_id)
    )).scalar() or 0
    if prod_count > 0:
        from app.core.exceptions import BusinessError
        raise BusinessError(f"该系列下有 {prod_count} 个产品，无法删除")

    await session.delete(s)
    await session.flush()
    return success(message="系列已删除")


# ══════════════════════════════════════════════════════════════
# 产品
# ══════════════════════════════════════════════════════════════


@router.get("")
async def list_products(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    keyword: str | None = Query(None, description="搜索名称/编码"),
    product_type: str | None = Query(None),
    category_id: int | None = Query(None),
    supplier_id: int | None = Query(None),
    series_id: int | None = Query(None),
):
    """产品列表"""
    conditions = []
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(or_(Product.name.ilike(kw), Product.code.ilike(kw)))
    if product_type:
        conditions.append(Product.product_type == product_type)
    if category_id:
        conditions.append(Product.category_id == category_id)
    if supplier_id:
        conditions.append(Product.supplier_id == supplier_id)
    if series_id is not None:
        conditions.append(Product.series_id == series_id)

    where = and_(*conditions) if conditions else True
    total = (await session.execute(select(func.count()).select_from(Product).where(where))).scalar() or 0

    result = await session.execute(
        select(Product)
        .where(where)
        .order_by(Product.id.desc())
        .offset(page.offset)
        .limit(page.page_size)
    )
    products = result.scalars().all()

    items = []
    for p in products:
        items.append({
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "product_type": p.product_type,
            "classification": p.classification,
            "category_id": p.category_id,
            "category_name": p.category.name if p.category else "",
            "supplier_id": p.supplier_id,
            "supplier_name": p.supplier.name if p.supplier else "",
            "supplier_code": p.supplier.code if p.supplier else "",
            "series_id": p.series_id,
            "series_name": p.series_rel.name if p.series_rel else "",
            "processing_type_id": p.processing_type_id,
            "processing_type_name": p.processing_type.name if p.processing_type else "",
            "model": p.model,
            "material": p.material,
            "color": p.color or "",
            "pattern": p.pattern or "",
            "width": p.width,
            "standard_width": float(p.standard_width or 0),
            "weight": p.weight,
            "fold_ratio": float(p.fold_ratio),
            "unit": p.unit,
            "calc_type": p.calc_type or "per_meter",
            "cost_price": float(p.cost_price),
            "min_price": float(p.min_price),
            "selling_price": float(p.selling_price),
            "stock": p.stock,
            "safety_stock": p.safety_stock,
            "series": p.series,
            "is_purchase": p.is_purchase if hasattr(p, 'is_purchase') else True,
            "is_active": p.is_active,
            "remark": p.remark,
        })

    return paginated(items=items, total=total, page=page.page, page_size=page.page_size)


@router.get("/{product_id}")
async def get_product(session: SessionDep, current_user: CurrentUserDep, product_id: int):
    """产品详情"""
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(Product)
        .options(selectinload(Product.processing_type))
        .where(Product.id == product_id)
    )
    p = result.scalar_one_or_none()
    if not p:
        raise NotFoundError("产品不存在")

    return success(data={
        "id": p.id,
        "code": p.code,
        "name": p.name,
        "product_type": p.product_type,
        "classification": p.classification,
        "category_id": p.category_id,
        "category_name": p.category.name if p.category else "",
        "supplier_id": p.supplier_id,
        "supplier_name": p.supplier.name if p.supplier else "",
        "supplier_code": p.supplier.code if p.supplier else "",
        "series_id": p.series_id,
        "series_name": p.series_rel.name if p.series_rel else "",
        "processing_type_id": p.processing_type_id,
        "processing_type_name": p.processing_type.name if p.processing_type else "",
        "model": p.model,
        "material": p.material,
        "color": p.color or "",
        "pattern": p.pattern or "",
        "width": p.width,
        "standard_width": float(p.standard_width or 0),
        "weight": p.weight,
        "fold_ratio": float(p.fold_ratio),
        "unit": p.unit,
        "calc_type": p.calc_type or "per_meter",
        "cost_price": float(p.cost_price),
        "min_price": float(p.min_price),
        "selling_price": float(p.selling_price),
        "stock": p.stock,
        "safety_stock": p.safety_stock,
        "series": p.series,
        "is_purchase": p.is_purchase if hasattr(p, 'is_purchase') else True,
        "is_active": p.is_active,
        "remark": p.remark,
    })


@router.post("")
async def create_product(session: SessionDep, current_user: CurrentUserDep, req: ProductCreate):
    """创建产品"""
    try:
        data = req.model_dump()
        product = Product(**data)
        session.add(product)
        await session.flush()
        return success(data={"id": product.id}, message="产品创建成功")
    except Exception as e:
        import traceback
        traceback.print_exc()
        from app.core.logging import logger
        logger.error(f"创建产品失败: {e}")
        raise


@router.put("/{product_id}")
async def update_product(
    session: SessionDep, current_user: CurrentUserDep, product_id: int, req: ProductUpdate
):
    """更新产品"""
    result = await session.execute(select(Product).where(Product.id == product_id))
    p = result.scalar_one_or_none()
    if not p:
        raise NotFoundError("产品不存在")

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    await session.flush()
    return success(data={"id": product_id}, message="产品更新成功")
