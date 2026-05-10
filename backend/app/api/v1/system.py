"""
系统管理 API（字典、配置、操作日志）
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.exceptions import NotFoundError
from app.core.response import paginated, success
from app.domain.log import OperationalLog
from app.domain.system import DictItem, DictType

router = APIRouter(prefix="/api/v1/system", tags=["系统管理"])


# ══════════════════════════════════════════════════════════════
# 字典管理
# ══════════════════════════════════════════════════════════════


@router.get("/dict/{dict_type}")
async def get_dict(session: SessionDep, current_user: CurrentUserDep, dict_type: str):
    """获取字典数据（按类型，供业务使用）"""
    result = await session.execute(
        select(DictItem)
        .where(DictItem.dict_type == dict_type, DictItem.is_active == True)
        .order_by(DictItem.sort_order, DictItem.id)
    )
    items = result.scalars().all()

    return success(data=[
        {
            "code": item.dict_code,
            "label": item.dict_label,
            "remark": item.remark,
        }
        for item in items
    ])


@router.get("/dicts/types")
async def get_dict_types(session: SessionDep, current_user: CurrentUserDep):
    """获取所有字典类型列表"""
    result = await session.execute(
        select(DictItem.dict_type)
        .distinct()
        .where(DictItem.is_active == True)
        .order_by(DictItem.dict_type)
    )
    types = [r[0] for r in result.all()]
    return success(data=types)


@router.get("/dicts")
async def list_dict_items(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    dict_type: str | None = Query(None, description="字典类型筛选"),
    keyword: str | None = Query(None, description="搜索编码/名称"),
):
    """字典项列表（分页）"""
    conditions = []
    if dict_type:
        conditions.append(DictItem.dict_type == dict_type)
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(or_(DictItem.dict_code.ilike(kw), DictItem.dict_label.ilike(kw)))

    where = and_(*conditions) if conditions else True
    total = (await session.execute(select(func.count()).select_from(DictItem).where(where))).scalar() or 0
    result = await session.execute(
        select(DictItem).where(where).order_by(DictItem.dict_type, DictItem.sort_order)
        .offset(page.offset).limit(page.page_size)
    )
    items = result.scalars().all()

    return paginated(
        items=[
            {
                "id": d.id,
                "dict_type": d.dict_type,
                "dict_code": d.dict_code,
                "dict_label": d.dict_label,
                "sort_order": d.sort_order,
                "is_active": d.is_active,
                "remark": d.remark,
            }
            for d in items
        ],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/dicts")
async def create_dict_item(session: SessionDep, current_user: CurrentUserDep, req: DictItemCreate):
    """创建字典项"""
    item = DictItem(
        dict_type=req.dict_type,
        dict_code=req.dict_code,
        dict_label=req.dict_label,
        sort_order=req.sort_order,
        remark=req.remark or "",
    )
    session.add(item)
    await session.flush()
    return success(data={"id": item.id}, message="字典项创建成功")


@router.put("/dicts/{item_id}")
async def update_dict_item(session: SessionDep, current_user: CurrentUserDep, item_id: int, req: DictItemUpdate):
    """更新字典项"""
    result = await session.execute(select(DictItem).where(DictItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("字典项不存在")

    if req.dict_code is not None:
        item.dict_code = req.dict_code
    if req.dict_label is not None:
        item.dict_label = req.dict_label
    if req.sort_order is not None:
        item.sort_order = req.sort_order
    if req.is_active is not None:
        item.is_active = req.is_active
    if req.remark is not None:
        item.remark = req.remark

    await session.flush()
    return success(message="字典项更新成功")


@router.delete("/dicts/{item_id}")
async def delete_dict_item(session: SessionDep, current_user: CurrentUserDep, item_id: int):
    """删除字典项"""
    result = await session.execute(select(DictItem).where(DictItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("字典项不存在")
    item.is_active = False
    await session.flush()
    return success(message="字典项已删除")


# ══════════════════════════════════════════════════════════════
# 字典类型管理
# ══════════════════════════════════════════════════════════════


@router.get("/dict-types")
async def list_dict_types(session: SessionDep, current_user: CurrentUserDep):
    """获取所有字典类型"""
    result = await session.execute(
        select(DictType).where(DictType.is_active == True).order_by(DictType.sort_order, DictType.id)
    )
    types = result.scalars().all()
    return success(data=[
        {
            "id": t.id,
            "dict_type": t.dict_type,
            "dict_name": t.dict_name,
            "description": t.description,
            "sort_order": t.sort_order,
        }
        for t in types
    ])


@router.post("/dict-types")
async def create_dict_type(session: SessionDep, current_user: CurrentUserDep, req: DictTypeCreate):
    """创建字典类型"""
    existing = await session.execute(select(DictType).where(DictType.dict_type == req.dict_type))
    if existing.scalar_one_or_none():
        from app.core.exceptions import BusinessError
        raise BusinessError(f"字典类型「{req.dict_type}」已存在")

    dt = DictType(dict_type=req.dict_type, dict_name=req.dict_name, description=req.description or "", sort_order=req.sort_order)
    session.add(dt)
    await session.flush()
    return success(data={"id": dt.id}, message=f"字典类型「{req.dict_name}」创建成功")


@router.put("/dict-types/{type_id}")
async def update_dict_type(session: SessionDep, current_user: CurrentUserDep, type_id: int, req: DictTypeUpdate):
    """更新字典类型"""
    result = await session.execute(select(DictType).where(DictType.id == type_id))
    dt = result.scalar_one_or_none()
    if not dt:
        raise NotFoundError("字典类型不存在")

    if req.dict_name is not None:
        dt.dict_name = req.dict_name
    if req.description is not None:
        dt.description = req.description
    if req.sort_order is not None:
        dt.sort_order = req.sort_order
    if req.is_active is not None:
        dt.is_active = req.is_active
    await session.flush()
    return success(message="字典类型更新成功")


@router.delete("/dict-types/{type_id}")
async def delete_dict_type(session: SessionDep, current_user: CurrentUserDep, type_id: int):
    """删除字典类型（同时禁用该类型下所有字典项）"""
    result = await session.execute(select(DictType).where(DictType.id == type_id))
    dt = result.scalar_one_or_none()
    if not dt:
        raise NotFoundError("字典类型不存在")

    # 禁用该类型下所有项
    items = await session.execute(
        select(DictItem).where(DictItem.dict_type == dt.dict_type)
    )
    for item in items.scalars().all():
        item.is_active = False

    dt.is_active = False
    await session.flush()
    return success(message=f"字典类型「{dt.dict_name}」已删除")


# ══════════════════════════════════════════════════════════════
# 店铺信息（基于 store_info 字典类型的独立表单 API）
# ══════════════════════════════════════════════════════════════


@router.get("/store-info")
async def get_store_info(session: SessionDep, current_user: CurrentUserDep):
    """获取店铺配置（读取 store_info 字典类型的所有项）"""
    result = await session.execute(
        select(DictItem)
        .where(DictItem.dict_type == "store_info", DictItem.is_active == True)
        .order_by(DictItem.sort_order)
    )
    items = {}
    for item in result.scalars().all():
        items[item.dict_code] = {
            "id": item.id,
            "label": item.dict_label,
            "remark": item.remark,
        }
    return success(data=items)


@router.put("/store-info")
async def update_store_info(session: SessionDep, current_user: CurrentUserDep, req: StoreInfoUpdate):
    """批量更新店铺配置"""
    for code, value in req.items.items():
        if not value:
            continue
        result = await session.execute(
            select(DictItem).where(
                DictItem.dict_type == "store_info",
                DictItem.dict_code == code,
                DictItem.is_active == True,
            )
        )
        item = result.scalar_one_or_none()
        if item:
            item.dict_label = value
    await session.flush()
    return success(message="店铺信息已更新")


# ══════════════════════════════════════════════════════════════
# 操作日志
# ══════════════════════════════════════════════════════════════


@router.get("/logs")
async def list_operation_logs(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    resource: str | None = Query(None, description="资源类型"),
    action: str | None = Query(None, description="操作类型"),
    keyword: str | None = Query(None, description="搜索操作人"),
):
    """操作日志列表"""
    conditions = []
    if resource:
        conditions.append(OperationalLog.resource == resource)
    if action:
        conditions.append(OperationalLog.action == action)
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(OperationalLog.operator_name.ilike(kw))

    where = and_(*conditions) if conditions else True
    total = (await session.execute(select(func.count()).select_from(OperationalLog).where(where))).scalar() or 0
    result = await session.execute(
        select(OperationalLog).where(where).order_by(OperationalLog.id.desc())
        .offset(page.offset).limit(page.page_size)
    )
    logs = result.scalars().all()

    return paginated(
        items=[
            {
                "id": log.id,
                "operator_id": log.operator_id,
                "operator_name": log.operator_name,
                "action": log.action,
                "resource": log.resource,
                "resource_id": log.resource_id,
                "detail": log.detail,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


# ── 临时 Pydantic 模型（避免循环依赖） ──────────────────────────


from pydantic import BaseModel, Field


class DictItemCreate(BaseModel):
    dict_type: str = Field(..., description="字典类型")
    dict_code: str = Field(..., description="字典编码")
    dict_label: str = Field(..., description="字典名称")
    sort_order: int = Field(default=0)
    remark: str | None = None


class DictItemUpdate(BaseModel):
    dict_code: str | None = None
    dict_label: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    remark: str | None = None


class DictTypeCreate(BaseModel):
    dict_type: str = Field(..., description="字典类型编码")
    dict_name: str = Field(..., description="字典类型名称")
    description: str = Field(default="")
    sort_order: int = Field(default=0)


class DictTypeUpdate(BaseModel):
    dict_name: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class StoreInfoUpdate(BaseModel):
    items: dict[str, str]
