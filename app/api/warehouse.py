# app/api/warehouse.py

from fastapi import APIRouter, Body, Header, Path, Query
from sqlalchemy import func, or_, select

from app.database import async_session
from app.models import Product, WarehouseRecord
from app.schemas import CommonResponse

router = APIRouter(prefix="/api/warehouse", tags=["仓库管理"])


@router.get("/records", response_model=dict)
async def list_records(
    record_type: str | None = Query(None, description="in/out"),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    async with async_session() as session:
        conditions = []
        if record_type:
            conditions.append(WarehouseRecord.record_type == record_type)
        if keyword:
            kw = f"%{keyword}%"
            conditions.append(WarehouseRecord.product_name.ilike(kw))

        query = select(WarehouseRecord)
        if conditions:
            query = query.where(*conditions)

        r = await session.execute(
            select(func.count()).select_from(WarehouseRecord).where(*conditions)
            if conditions
            else select(func.count()).select_from(WarehouseRecord)
        )
        total = r.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(WarehouseRecord.created_at.desc()).offset(offset).limit(page_size)
        result = await session.execute(query)
        records = result.scalars().all()

        await session.commit()
        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": r.id,
                    "record_type": r.record_type or "",
                    "product_id": r.product_id,
                    "product_name": r.product_name or "",
                    "qty": float(r.qty or 0),
                    "unit": r.unit or "米",
                    "remark": r.remark or "",
                    "operator": r.operator or "",
                    "created_at": str(r.created_at)[:19] if r.created_at else "",
                }
                for r in records
            ],
        }


@router.get("/stock", response_model=dict)
async def get_stock(keyword: str | None = Query(None)):
    async with async_session() as session:
        query = select(Product)
        if keyword:
            kw = f"%{keyword}%"
            query = query.where(or_(Product.name.ilike(kw), Product.code.ilike(kw)))

        result = await session.execute(query.order_by(Product.code))
        products = result.scalars().all()

        await session.commit()
        return {
            "success": True,
            "items": [
                {
                    "id": p.id,
                    "code": p.code or "",
                    "name": p.name or "",
                    "supplier_name": "",  # 简化
                    "unit_price": float(p.unit_price or 0),
                    "stock": float(p.stock or 0),
                    "unit": p.unit or "米",
                }
                for p in products
                if p.stock is not None and p.stock > 0
            ],
        }


@router.post("/in", response_model=CommonResponse)
async def stock_in(req: dict = Body(...)):
    async with async_session() as session:
        record = WarehouseRecord(
            record_type="in",
            product_id=req.get("product_id"),
            product_name=req.get("product_name", ""),
            qty=float(req.get("qty", 0)),
            unit=req.get("unit", "米"),
            remark=req.get("remark", ""),
            operator=req.get("operator", "系统"),
        )
        session.add(record)

        # 同时更新库存
        if req.get("product_id"):
            pr = await session.execute(select(Product).where(Product.id == req.get("product_id")))
            prod = pr.scalar_one_or_none()
            if prod:
                prod.stock = (prod.stock or 0) + float(req.get("qty", 0))

        await session.commit()
        return CommonResponse(success=True, data={"id": record.id})


@router.post("/out", response_model=CommonResponse)
async def stock_out(req: dict = Body(...)):
    async with async_session() as session:
        record = WarehouseRecord(
            record_type="out",
            product_id=req.get("product_id"),
            product_name=req.get("product_name", ""),
            qty=float(req.get("qty", 0)),
            unit=req.get("unit", "米"),
            remark=req.get("remark", ""),
            operator=req.get("operator", "系统"),
        )
        session.add(record)

        if req.get("product_id"):
            pr = await session.execute(select(Product).where(Product.id == req.get("product_id")))
            prod = pr.scalar_one_or_none()
            if prod:
                prod.stock = max(0, (prod.stock or 0) - float(req.get("qty", 0)))

        await session.commit()
        return CommonResponse(success=True, data={"id": record.id})


@router.delete("/records/{record_id}", response_model=CommonResponse)
async def delete_warehouse_record(
    record_id: int = Path(...),
    authorization: str = Header(None),
):
    """删除仓库记录"""
    async with async_session() as session:
        r = await session.execute(select(WarehouseRecord).where(WarehouseRecord.id == record_id))
        record = r.scalar_one_or_none()
        if not record:
            return CommonResponse(success=False, error="记录不存在")
        await session.delete(record)
        await session.commit()
        return CommonResponse(success=True)
