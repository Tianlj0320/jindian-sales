# app/api/customers.py
from fastapi import APIRouter, Query, Body
from app.database import async_session
from app.models import Customer
from app.schemas import CustomerListResponse, CustomerResponse, CustomerListItem, CustomerDetailData, CommonResponse
from sqlalchemy import select, func, and_
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/customers", tags=["客户管理"])


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    keyword: Optional[str] = Query(None, description="搜索：姓名/电话"),
    customer_type: Optional[str] = Query(None, description="客户类型"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    async with async_session() as session:
        conditions = [Customer.is_deleted == False]
        if keyword:
            kw = f"%{keyword}%"
            conditions.append(
                (Customer.name.ilike(kw)) |
                (Customer.phone.ilike(kw))
            )
        if customer_type:
            conditions.append(Customer.type == customer_type)

        query = select(Customer).where(and_(*conditions))
        if conditions:
            query = query.where(and_(*conditions))

        count_result = await session.execute(
            select(func.count()).select_from(Customer)
            .where(and_(*conditions)) if conditions
            else select(func.count()).select_from(Customer)
        )
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(Customer.created_at.desc()).offset(offset).limit(page_size)
        result = await session.execute(query)
        customers = result.scalars().all()

        items = [
            CustomerListItem(
                id=c.id, name=c.name or "", phone=c.phone or "",
                type=c.type or "", address=c.address or "",
                community=c.community or "", source=c.source or "",
                salesperson=c.salesperson or "",
                debt=float(c.debt or 0),
                created_at=str(c.created_at)[:10] if c.created_at else ""
            )
            for c in customers
        ]

        await session.commit()
        return CustomerListResponse(success=True, total=total, page=page, page_size=page_size, items=items)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        c = result.scalar_one_or_none()
        if not c:
            return CustomerResponse(success=False, error="客户不存在")

        return CustomerResponse(success=True, data=CustomerDetailData(
            id=c.id, name=c.name or "", phone=c.phone or "",
            type=c.type or "", address=c.address or "",
            community=c.community or "", source=c.source or "",
            salesperson=c.salesperson or "",
            debt=float(c.debt or 0),
            created_at=str(c.created_at)[:19] if c.created_at else ""
        ))


@router.post("", response_model=CommonResponse)
async def create_customer(req: dict = Body(...)):
    async with async_session() as session:
        # 生成客户编号
        today = datetime.now().strftime("%Y%m%d")
        seq_result = await session.execute(
            select(func.count(Customer.id))
            .where(Customer.name.ilike(f"%{today[:6]}%"))
        )
        seq = (seq_result.scalar() or 0) + 1
        code = f"CU{today}{seq:03d}"

        customer = Customer(
            name=req.get("name", ""),
            phone=req.get("phone", ""),
            type=req.get("type", "零售"),
            address=req.get("address", ""),
            community=req.get("community", ""),
            source=req.get("source", ""),
            salesperson=req.get("salesperson", ""),
            debt=0
        )
        session.add(customer)
        await session.commit()
        await session.refresh(customer)

        return CommonResponse(success=True, data={"id": customer.id, "code": code})


@router.put("/{customer_id}", response_model=CommonResponse)
async def update_customer(customer_id: int, req: dict = Body(...)):
    async with async_session() as session:
        result = await session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        c = result.scalar_one_or_none()
        if not c:
            return CommonResponse(success=False, error="客户不存在")

        for field in ["name", "phone", "type", "address", "community", "source", "salesperson"]:
            if field in req:
                setattr(c, field, req[field])

        await session.commit()
        return CommonResponse(success=True, data={"id": customer_id})


@router.delete("/{customer_id}", response_model=CommonResponse)
async def delete_customer(customer_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        c = result.scalar_one_or_none()
        if not c:
            return CommonResponse(success=False, error="客户不存在")

        # 软删除（不物理删除，保留数据）
        c.is_deleted = True
        await session.commit()
        return CommonResponse(success=True, data={"id": customer_id})
