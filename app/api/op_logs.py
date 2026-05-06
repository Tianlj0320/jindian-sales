# app/api/op_logs.py
# 操作日志 API（V4.0 审计追踪）
from datetime import datetime
from fastapi import APIRouter, Query
from sqlalchemy import and_, desc, func, select, String

from app.core.response import success_response, error_response
from app.database import async_session
from app.models import OperationalLog

router = APIRouter(prefix="/api/op-logs", tags=["V4.0 操作日志"])


@router.get("", response_model=dict)
async def list_op_logs(
    action: str | None = Query(None, description="操作类型：CREATE/UPDATE/DELETE"),
    resource: str | None = Query(None, description="资源类型：order/customer/purchase 等"),
    operator_id: int | None = Query(None, alias="operator_id", description="操作人ID"),
    date_from: str | None = Query(None, alias="date_from", description="开始日期 YYYY-MM-DD"),
    date_to: str | None = Query(None, alias="date_to", description="结束日期 YYYY-MM-DD"),
    keyword: str | None = Query(None, description="搜索操作人/资源ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """
    GET /api/op-logs - 操作日志列表（支持多维度筛选，分页）
    用于审计追踪，权限：仅管理员
    """
    async with async_session() as session:
        conditions = []
        if action:
            conditions.append(OperationalLog.action == action)
        if resource:
            conditions.append(OperationalLog.resource == resource)
        if operator_id:
            conditions.append(OperationalLog.operator_id == operator_id)
        if date_from:
            conditions.append(OperationalLog.created_at >= datetime.strptime(date_from, "%Y-%m-%d"))
        if date_to:
            conditions.append(OperationalLog.created_at <= datetime.strptime(date_to + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        if keyword:
            kw = f"%{keyword}%"
            conditions.append(
                (OperationalLog.operator_name.ilike(kw)) |
                (func.cast(OperationalLog.resource_id, String).like(kw))
            )

        where_clause = and_(*conditions) if conditions else True

        r = await session.execute(
            select(func.count(OperationalLog.id)).where(where_clause)
        )
        total = r.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(OperationalLog)
            .where(where_clause)
            .order_by(OperationalLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(query)
        logs = result.scalars().all()

        return success_response(
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [
                    {
                        "id": log.id,
                        "action": log.action or "",
                        "resource": log.resource or "",
                        "resource_id": log.resource_id,
                        "operator_id": log.operator_id,
                        "operator_name": log.operator_name or "",
                        "before_state": log.before_state or "",
                        "after_state": log.after_state or "",
                        "ip_address": log.ip_address or "",
                        "created_at": str(log.created_at)[:19] if log.created_at else "",
                    }
                    for log in logs
                ],
            }
        )


# V4.0 统计摘要（按操作类型和资源分组）
@router.get("/summary", response_model=dict)
async def op_log_summary(
    date_from: str | None = Query(None, alias="date_from", description="开始日期 YYYY-MM-DD"),
    date_to: str | None = Query(None, alias="date_to", description="结束日期 YYYY-MM-DD"),
):
    """
    GET /api/op-logs/summary - 操作统计摘要
    返回各 action 和 resource 的操作次数
    """
    async with async_session() as session:
        conditions = []
        if date_from:
            conditions.append(OperationalLog.created_at >= datetime.strptime(date_from, "%Y-%m-%d"))
        if date_to:
            conditions.append(OperationalLog.created_at <= datetime.strptime(date_to + " 23:59:59", "%Y-%m-%d %H:%M:%S"))

        where_clause = and_(*conditions) if conditions else True

        r = await session.execute(
            select(
                OperationalLog.action,
                OperationalLog.resource,
                func.count(OperationalLog.id).label("count"),
            )
            .where(where_clause)
            .group_by(OperationalLog.action, OperationalLog.resource)
            .order_by(desc("count"))
        )
        rows = r.all()

        # 按 action 汇总
        action_summary = {}
        for row in rows:
            act = row.action or "UNKNOWN"
            if act not in action_summary:
                action_summary[act] = 0
            action_summary[act] += row.count

        return success_response(
            data={
                "by_action": [{"action": k, "count": v} for k, v in sorted(action_summary.items(), key=lambda x: -x[1])],
                "by_resource": [
                    {"action": row.action, "resource": row.resource, "count": row.count}
                    for row in rows
                ],
            }
        )