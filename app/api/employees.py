# app/api/employees.py

from fastapi import APIRouter, Body, Query
from sqlalchemy import func, select

from app.database import async_session
from app.models import Employee
from app.schemas import CommonResponse, EmployeeListItem, EmployeeListResponse

router = APIRouter(prefix="/api/employees", tags=["员工管理"])


@router.get("", response_model=EmployeeListResponse)
async def list_employees(
    position: str | None = Query(None, description="职务筛选"),
    is_installer: bool | None = Query(None),
):
    async with async_session() as session:
        query = select(Employee)
        if position:
            query = query.where(Employee.position == position)
        if is_installer is not None:
            query = query.where(Employee.is_installer == is_installer)

        result = await session.execute(query.order_by(Employee.code))
        employees = result.scalars().all()

        items = [
            EmployeeListItem(
                id=e.id,
                code=e.code or "",
                name=e.name or "",
                gender=e.gender or "男",
                phone=e.phone or "",
                position=e.position or "",
                department=e.department or "",
                max_discount=float(e.max_discount or 1.0),
                round_limit=e.round_limit or 0,
                is_installer=e.is_installer or False,
                status=e.status or "启用",
            )
            for e in employees
        ]

        await session.commit()
        return EmployeeListResponse(success=True, total=len(items), items=items)


@router.post("", response_model=CommonResponse)
async def create_employee(req: dict = Body(...)):
    async with async_session() as session:
        seq_result = await session.execute(select(func.count(Employee.id)))
        seq = (seq_result.scalar() or 0) + 1
        code = f"E{seq:03d}"

        employee = Employee(
            code=code,
            name=req.get("name", ""),
            gender=req.get("gender", "男"),
            phone=req.get("phone", ""),
            position=req.get("position", "导购"),
            department=req.get("department", ""),
            max_discount=req.get("max_discount", 1.0),
            round_limit=req.get("round_limit", 0),
            is_installer=req.get("is_installer", False),
            status="启用",
        )
        session.add(employee)
        await session.commit()
        await session.refresh(employee)
        return CommonResponse(success=True, data={"id": employee.id, "code": employee.code})


@router.put("/{employee_id}", response_model=CommonResponse)
async def update_employee(employee_id: int, req: dict = Body(...)):
    async with async_session() as session:
        result = await session.execute(select(Employee).where(Employee.id == employee_id))
        e = result.scalar_one_or_none()
        if not e:
            return CommonResponse(success=False, error="员工不存在")

        for field in [
            "name",
            "gender",
            "phone",
            "position",
            "department",
            "max_discount",
            "round_limit",
            "is_installer",
            "status",
        ]:
            if field in req:
                setattr(e, field, req[field])

        await session.commit()
        return CommonResponse(success=True, data={"id": employee_id})


@router.delete("/{employee_id}", response_model=CommonResponse)
async def delete_employee(employee_id: int):
    async with async_session() as session:
        result = await session.execute(select(Employee).where(Employee.id == employee_id))
        e = result.scalar_one_or_none()
        if not e:
            return CommonResponse(success=False, error="员工不存在")
        await session.delete(e)
        await session.commit()
        return CommonResponse(success=True, message="删除成功")
