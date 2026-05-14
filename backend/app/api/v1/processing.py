"""
加工类型与辅料规则 API
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUserDep, SessionDep
from app.core.exceptions import NotFoundError
from app.core.response import success
from app.domain.processing import ProcessingType, ProcessingMaterialRule
from app.schemas.processing import (
    ProcessingTypeCreate,
    ProcessingTypeUpdate,
    ProcessingMaterialRuleCreate,
    ProcessingMaterialRuleUpdate,
)

router = APIRouter(prefix="/api/v1/processing", tags=["加工类型"])


@router.get("/types")
async def list_processing_types(session: SessionDep, current_user: CurrentUserDep):
    """加工类型列表（含辅料规则）"""
    result = await session.execute(
        select(ProcessingType)
        .options(selectinload(ProcessingType.rules))
        .order_by(ProcessingType.sort_order, ProcessingType.id)
    )
    types = result.scalars().all()

    return success(data=[
        {
            "id": t.id,
            "name": t.name,
            "code": t.code,
            "description": t.description,
            "sort_order": t.sort_order,
            "is_active": t.is_active,
            "rules": [
                {
                    "id": r.id,
                    "processing_type_id": r.processing_type_id,
                    "material_name": r.material_name,
                    "default_product_name": r.default_product_name,
                    "product_id": r.product_id,
                    "unit": r.unit,
                    "qty_formula": r.qty_formula,
                    "unit_price": float(r.unit_price),
                    "sort_order": r.sort_order,
                    "is_required": r.is_required,
                }
                for r in (t.rules or [])
            ],
        }
        for t in types
    ])


@router.get("/types/{type_id}")
async def get_processing_type(session: SessionDep, current_user: CurrentUserDep, type_id: int):
    """加工类型详情"""
    result = await session.execute(
        select(ProcessingType)
        .options(selectinload(ProcessingType.rules))
        .where(ProcessingType.id == type_id)
    )
    t = result.scalar_one_or_none()
    if not t:
        raise NotFoundError("加工类型不存在")

    return success(data={
        "id": t.id,
        "name": t.name,
        "code": t.code,
        "description": t.description,
        "sort_order": t.sort_order,
        "is_active": t.is_active,
        "rules": [
            {
                "id": r.id,
                "processing_type_id": r.processing_type_id,
                "material_name": r.material_name,
                "default_product_name": r.default_product_name,
                "product_id": r.product_id,
                "unit": r.unit,
                "qty_formula": r.qty_formula,
                "unit_price": float(r.unit_price),
                "sort_order": r.sort_order,
                "is_required": r.is_required,
            }
            for r in (t.rules or [])
        ],
    })


@router.post("/types")
async def create_processing_type(
    session: SessionDep, current_user: CurrentUserDep, req: ProcessingTypeCreate
):
    """创建加工类型（含辅料规则）"""
    pt = ProcessingType(
        name=req.name,
        code=req.code,
        description=req.description,
        sort_order=req.sort_order,
        is_active=req.is_active,
    )
    session.add(pt)
    await session.flush()

    # 创建辅料规则
    for rule_data in req.rules or []:
        rule = ProcessingMaterialRule(
            processing_type_id=pt.id,
            material_name=rule_data.material_name,
            default_product_name=rule_data.default_product_name,
            product_id=rule_data.product_id,
            unit=rule_data.unit,
            qty_formula=rule_data.qty_formula,
            unit_price=rule_data.unit_price,
            sort_order=rule_data.sort_order,
            is_required=rule_data.is_required,
        )
        session.add(rule)

    await session.flush()
    return success(data={"id": pt.id}, message="加工类型创建成功")


@router.put("/types/{type_id}")
async def update_processing_type(
    session: SessionDep, current_user: CurrentUserDep, type_id: int, req: ProcessingTypeUpdate
):
    """更新加工类型"""
    result = await session.execute(select(ProcessingType).where(ProcessingType.id == type_id))
    t = result.scalar_one_or_none()
    if not t:
        raise NotFoundError("加工类型不存在")

    update_data = req.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(t, field, value)

    await session.flush()
    return success(data={"id": type_id}, message="加工类型更新成功")


@router.delete("/types/{type_id}")
async def delete_processing_type(
    session: SessionDep, current_user: CurrentUserDep, type_id: int
):
    """删除加工类型"""
    result = await session.execute(select(ProcessingType).where(ProcessingType.id == type_id))
    t = result.scalar_one_or_none()
    if not t:
        raise NotFoundError("加工类型不存在")

    await session.delete(t)
    await session.flush()
    return success(message="加工类型已删除")


# ── 辅料规则管理 ──────────────────────────────────────────────


@router.post("/types/{type_id}/rules")
async def create_rule(
    session: SessionDep, current_user: CurrentUserDep, type_id: int,
    req: ProcessingMaterialRuleCreate,
):
    """添加辅料规则"""
    # 检查加工类型存在
    result = await session.execute(select(ProcessingType).where(ProcessingType.id == type_id))
    if not result.scalar_one_or_none():
        raise NotFoundError("加工类型不存在")

    rule = ProcessingMaterialRule(
        processing_type_id=type_id,
        material_name=req.material_name,
        default_product_name=req.default_product_name,
        product_id=req.product_id,
        unit=req.unit,
        qty_formula=req.qty_formula,
        unit_price=req.unit_price,
        sort_order=req.sort_order,
        is_required=req.is_required,
    )
    session.add(rule)
    await session.flush()
    return success(data={"id": rule.id}, message="辅料规则创建成功")


@router.put("/rules/{rule_id}")
async def update_rule(
    session: SessionDep, current_user: CurrentUserDep, rule_id: int,
    req: ProcessingMaterialRuleUpdate,
):
    """更新辅料规则"""
    result = await session.execute(select(ProcessingMaterialRule).where(ProcessingMaterialRule.id == rule_id))
    r = result.scalar_one_or_none()
    if not r:
        raise NotFoundError("辅料规则不存在")

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(r, field, value)
    await session.flush()
    return success(data={"id": rule_id}, message="辅料规则更新成功")


@router.delete("/rules/{rule_id}")
async def delete_rule(session: SessionDep, current_user: CurrentUserDep, rule_id: int):
    """删除辅料规则"""
    result = await session.execute(select(ProcessingMaterialRule).where(ProcessingMaterialRule.id == rule_id))
    r = result.scalar_one_or_none()
    if not r:
        raise NotFoundError("辅料规则不存在")
    await session.delete(r)
    await session.flush()
    return success(message="辅料规则已删除")
