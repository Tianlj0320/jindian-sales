# app/api/products.py
from fastapi import APIRouter, Query, Body, Path
from app.database import async_session
from app.models import Supplier, FabricCategory, Product
from app.schemas import (
    SupplierListResponse, SupplierListItem,
    ProductListResponse, ProductListItem, ProductDetailData, ProductResponse,
    CommonResponse
)
from sqlalchemy import select, func, and_
from typing import Optional

router = APIRouter(prefix="/api/products", tags=["产品资料"])


# ─── 供应商 ───────────────────────────────────────────────────────────────────

@router.get("/suppliers", response_model=SupplierListResponse)
async def list_suppliers():
    async with async_session() as session:
        result = await session.execute(
            select(Supplier).order_by(Supplier.code)
        )
        suppliers = result.scalars().all()
        items = [
            SupplierListItem(
                id=s.id, code=s.code or "", name=s.name or "",
                type=s.type or "", contact=s.contact or "",
                phone=s.phone or "", delivery_days=s.delivery_days or 7
            )
            for s in suppliers
        ]
        await session.commit()
        return SupplierListResponse(success=True, total=len(items), items=items)


@router.post("/suppliers", response_model=CommonResponse)
async def create_supplier(req: dict = Body(...)):
    async with async_session() as session:
        # 查最大编号
        seq_result = await session.execute(
            select(func.count(Supplier.id))
        )
        seq = (seq_result.scalar() or 0) + 1
        code = f"{seq:02d}"

        supplier = Supplier(
            code=code,
            name=req.get("name", ""),
            type=req.get("type", "布艺"),
            contact=req.get("contact", ""),
            phone=req.get("phone", ""),
            delivery_days=req.get("delivery_days", 7),
            address=req.get("address", "")
        )
        session.add(supplier)
        await session.commit()
        await session.refresh(supplier)
        return CommonResponse(success=True, data={"id": supplier.id, "code": supplier.code})


# ─── 布版/系列 ────────────────────────────────────────────────────────────────

@router.get("/categories", response_model=dict)
async def list_categories(supplier_id: Optional[int] = Query(None)):
    """布版系列列表（按供应商筛选）"""
    async with async_session() as session:
        query = select(FabricCategory)
        if supplier_id:
            query = query.where(FabricCategory.supplier_id == supplier_id)
        query = query.order_by(FabricCategory.code)
        result = await session.execute(query)
        cats = result.scalars().all()

        # 加载供应商名
        sup_result = await session.execute(select(Supplier))
        sup_map = {s.id: s.name for s in sup_result.scalars().all()}

        items = [
            {
                "id": c.id, "code": c.code or "", "name": c.name or "",
                "supplier_id": c.supplier_id,
                "supplier_name": sup_map.get(c.supplier_id, ""),
                "description": c.description or ""
            }
            for c in cats
        ]
        await session.commit()
        return {"success": True, "items": items}


@router.post("/categories", response_model=CommonResponse)
async def create_category(req: dict = Body(...)):
    async with async_session() as session:
        # 生成4位编号（前缀=供应商序号）
        supplier_id = req.get("supplier_id")
        prefix = "01"
        if supplier_id:
            sr = await session.execute(select(Supplier).where(Supplier.id == supplier_id))
            sup = sr.scalar_one_or_none()
            if sup:
                prefix = sup.code or "01"

        seq_result = await session.execute(
            select(func.count(FabricCategory.id))
            .where(FabricCategory.supplier_id == supplier_id)
        )
        seq = (seq_result.scalar() or 0) + 1
        code = f"{prefix}{seq:02d}"

        cat = FabricCategory(
            code=code,
            name=req.get("name", ""),
            supplier_id=supplier_id,
            description=req.get("description", "")
        )
        session.add(cat)
        await session.commit()
        await session.refresh(cat)
        return CommonResponse(success=True, data={"id": cat.id, "code": cat.code})


# ─── 产品 ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=ProductListResponse)
async def list_products(
    keyword: Optional[str] = Query(None, description="搜索：名称/编号"),
    supplier_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    product_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    async with async_session() as session:
        conditions = []
        if keyword:
            kw = f"%{keyword}%"
            conditions.append(
                (Product.name.ilike(kw)) |
                (Product.code.ilike(kw))
            )
        if supplier_id:
            conditions.append(Product.supplier_id == supplier_id)
        if category_id:
            conditions.append(Product.category_id == category_id)
        if product_type:
            conditions.append(Product.product_type == product_type)

        query = select(Product)
        if conditions:
            query = query.where(and_(*conditions))

        count_result = await session.execute(
            select(func.count()).select_from(Product)
            .where(and_(*conditions)) if conditions
            else select(func.count()).select_from(Product)
        )
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(Product.code).offset(offset).limit(page_size)
        result = await session.execute(query)
        products = result.scalars().all()

        # 加载关联名称
        sup_result = await session.execute(select(Supplier))
        sup_map = {s.id: s for s in sup_result.scalars().all()}
        cat_result = await session.execute(select(FabricCategory))
        cat_map = {c.id: c for c in cat_result.scalars().all()}

        items = [
            ProductListItem(
                id=p.id, code=p.code or "", name=p.name or "",
                supplier_name=sup_map.get(p.supplier_id, type('',(),{'name':''})()).name if p.supplier_id else "",
                category_name=cat_map.get(p.category_id, type('',(),{'name':''})()).name if p.category_id else "",
                product_type=p.product_type or "",
                material=p.material or "",
                unit_price=float(p.unit_price or 0),
                stock=p.stock or 0,
                unit=p.unit or "米"
            )
            for p in products
        ]

        await session.commit()
        return ProductListResponse(success=True, total=total, page=page, page_size=page_size, items=items)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        p = result.scalar_one_or_none()
        if not p:
            return ProductResponse(success=False, error="产品不存在")

        sup_name = ""
        if p.supplier_id:
            sr = await session.execute(select(Supplier).where(Supplier.id == p.supplier_id))
            sup = sr.scalar_one_or_none()
            if sup: sup_name = sup.name

        cat_name = ""
        if p.category_id:
            cr = await session.execute(select(FabricCategory).where(FabricCategory.id == p.category_id))
            cat = cr.scalar_one_or_none()
            if cat: cat_name = cat.name

        return ProductResponse(success=True, data=ProductDetailData(
            id=p.id, code=p.code or "", name=p.name or "",
            supplier_id=p.supplier_id or 0, supplier_name=sup_name,
            category_id=p.category_id or 0, category_name=cat_name,
            product_type=p.product_type or "",
            classification=p.classification or "",
            model=p.model or "", material=p.material or "",
            width=p.width or 0, weight=p.weight or 0,
            unit_price=float(p.unit_price or 0),
            unit=p.unit or "米", stock=p.stock or 0
        ))


@router.post("", response_model=CommonResponse)
async def create_product(req: dict = Body(...)):
    async with async_session() as session:
        # 生成8位编号
        supplier_id = req.get("supplier_id")
        category_id = req.get("category_id")
        sup_code = "00"
        cat_code = "00"
        if supplier_id:
            sr = await session.execute(select(Supplier).where(Supplier.id == supplier_id))
            sup = sr.scalar_one_or_none()
            if sup: sup_code = sup.code or "00"
        if category_id:
            cr = await session.execute(select(FabricCategory).where(FabricCategory.id == category_id))
            cat = cr.scalar_one_or_none()
            if cat: cat_code = cat.code[-2:] if cat.code else "00"

        seq_result = await session.execute(
            select(func.count(Product.id))
            .where(Product.category_id == category_id)
        )
        seq = (seq_result.scalar() or 0) + 1
        code = f"{sup_code}{cat_code}{seq:04d}"

        product = Product(
            code=code,
            name=req.get("name", ""),
            supplier_id=supplier_id,
            category_id=category_id,
            product_type=req.get("product_type", "面料"),
            classification=req.get("classification", "定高"),
            model=req.get("model", ""),
            material=req.get("material", ""),
            width=req.get("width", 280),
            weight=req.get("weight", 0),
            unit_price=req.get("unit_price", 0),
            unit=req.get("unit", "米"),
            stock=req.get("stock", 0)
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return CommonResponse(success=True, data={"id": product.id, "code": product.code})
