# app/api/installer.py
import urllib.parse
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from jose import JWTError, jwt
from sqlalchemy import and_, func, select

from app.core.config import ALGORITHM, SECRET_KEY, TOKEN_EXPIRE_DAYS
from app.core.response import success_response
from app.database import async_session
from app.models import InstallerAccount, InstallTask, Order
from app.schemas import (
    CompleteRequest,
    CompleteResponse,
    CompleteResponseData,
    HistoryRecord,
    HistoryResponse,
    HistoryResponseData,
    InstallerInfo,
    LoginRequest,
    LoginResponse,
    LoginResponseData,
    TaskItem,
    TasksResponse,
    TasksResponseData,
)

router = APIRouter(prefix="/api/installer", tags=["安装工"])


def mask_phone(phone: str) -> str:
    """脱敏手机号"""
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]


def create_token(installer_id: int) -> tuple[str, int]:
    """生成JWT token，返回(token, expires_in秒)"""
    expires_delta = timedelta(days=TOKEN_EXPIRE_DAYS)
    expire = datetime.utcnow() + expires_delta
    expires_in = int(expires_delta.total_seconds())
    payload = {"sub": str(installer_id), "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, expires_in


async def get_current_installer(authorization: str = Header(...)) -> InstallerAccount:
    """验证 Token，返回当前安装工账号"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="无效的认证格式")

    token = authorization[7:]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        installer_id = int(payload.get("sub", 0))
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Token无效或已过期")

    async with async_session() as session:
        result = await session.execute(
            select(InstallerAccount).where(InstallerAccount.id == installer_id)
        )
        installer = result.scalar_one_or_none()
        if not installer or installer.status != "active":
            raise HTTPException(status_code=401, detail="账号异常或已禁用")
        return installer


def build_navigate_url(address: str) -> str:
    """生成高德地图导航链接"""
    encoded = urllib.parse.quote(address)
    return f"https://uri.amap.com/search?keyword={encoded}&src=jd-rz&callnative=1"


# ─── 登录 ────────────────────────────────────────────────────────────────────


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """
    安装工登录
    Demo模式：验证码固定为 888888
    """
    DEMO_CODE = "888888"

    if req.code != DEMO_CODE:
        return LoginResponse(success=False, error="验证码不正确，请重新获取")

    async with async_session() as session:
        # 查找安装工账号
        result = await session.execute(
            select(InstallerAccount).where(InstallerAccount.phone == req.phone)
        )
        installer = result.scalar_one_or_none()

        if not installer:
            # Demo模式：自动创建新账号
            installer = InstallerAccount(
                name=f"安装师傅{req.phone[-4:]}", phone=req.phone, status="active"
            )
            session.add(installer)
            await session.commit()
            await session.refresh(installer)

        if installer.status != "active":
            return LoginResponse(success=False, error="账号已被禁用，请联系管理员")

        token, expires_in = create_token(installer.id)
        await session.commit()

        return LoginResponse(
            success=True,
            data=LoginResponseData(
                token=token,
                expires_in=expires_in,
                installer=InstallerInfo(
                    id=installer.id, name=installer.name, phone_masked=mask_phone(installer.phone)
                ),
            ),
        )


# ─── 安装工列表（供管理员分配使用）───────────────────────────────────────


@router.get("/list")
async def list_installers():
    """获取所有启用的安装工列表（管理员分配用）"""
    async with async_session() as session:
        result = await session.execute(
            select(InstallerAccount)
            .where(InstallerAccount.status == "active")
            .order_by(InstallerAccount.id)
        )
        installers = result.scalars().all()
        return success_response(
            data={"items": [{"id": i.id, "name": i.name, "phone": i.phone} for i in installers]},
        )


# ─── 今日任务 ────────────────────────────────────────────────────────────────


@router.get("/tasks", response_model=TasksResponse)
async def get_tasks(
    date_str: str = Query(default=None, description="查询日期，如 2026-04-20"),
    installer: InstallerAccount = Depends(get_current_installer),
):
    """获取安装工指定日期的安装任务列表"""
    query_date = date_str or str(date.today())

    async with async_session() as session:
        # 查任务
        result = await session.execute(
            select(InstallTask)
            .where(
                and_(
                    InstallTask.installer_id == installer.id,
                    func.date(InstallTask.install_date) == query_date,
                    InstallTask.status.in_(["pending", "ongoing"]),
                )
            )
            .order_by(InstallTask.install_time_slot)
        )
        tasks = result.scalars().all()

        # 统计今日完成数
        completed_result = await session.execute(
            select(func.count(InstallTask.id)).where(
                and_(
                    InstallTask.installer_id == installer.id,
                    func.date(InstallTask.install_date) == query_date,
                    InstallTask.status == "completed",
                )
            )
        )
        today_completed = completed_result.scalar() or 0

        task_items = []
        for t in tasks:
            task_items.append(
                TaskItem(
                    id=t.id,
                    order_no=t.order_no or f"ORDER-{t.order_id}",
                    customer_name=t.customer_name,
                    customer_phone_masked=mask_phone(t.customer_phone or ""),
                    raw_customer_phone=t.customer_phone,  # App端专用
                    address=t.address or "",
                    content=t.order_content,
                    time_slot=t.install_time_slot,
                    priority=t.priority or "normal",
                    status=t.status,
                    navigate_url=build_navigate_url(t.address) if t.address else None,
                )
            )

        await session.commit()

        return TasksResponse(
            success=True,
            data=TasksResponseData(
                installer_name=installer.name,
                date=query_date,
                today_completed=today_completed,
                today_pending=len(task_items),
                tasks=task_items,
            ),
        )


# ─── 确认完成 ────────────────────────────────────────────────────────────────


@router.post("/tasks/{task_id}/complete", response_model=CompleteResponse)
async def complete_task(
    task_id: int, req: CompleteRequest, installer: InstallerAccount = Depends(get_current_installer)
):
    """安装工确认安装完成"""
    async with async_session() as session:
        # 查任务
        result = await session.execute(
            select(InstallTask).where(
                and_(InstallTask.id == task_id, InstallTask.installer_id == installer.id)
            )
        )
        task = result.scalar_one_or_none()

        if not task:
            return CompleteResponse(success=False, error="任务不存在或无权操作")

        if task.status == "completed":
            return CompleteResponse(success=False, error="该任务已完成，无需重复提交")

        # 更新任务状态
        task.status = "completed"
        task.completed_at = datetime.now()
        task.completion_remark = req.remark or ""

        # 更新 InstallationOrder 状态（主数据源）
        from app.models import InstallationOrder
        io_result = await session.execute(
            select(InstallationOrder).where(InstallationOrder.order_id == task.order_id)
        )
        io = io_result.scalar_one_or_none()
        new_order_status = "installed"
        if io:
            io.status = "已验收"
            io.confirmed_at = datetime.now()
            # InstallationOrder 确认时会同步更新 Order 状态（见 installation_orders.py confirm 逻辑）
        else:
            # 兜底：如果没有 InstallationOrder 才直接更新 Order
            r_order = await session.execute(select(Order).where(Order.id == task.order_id))
            o = r_order.scalar_one_or_none()
            if o:
                o.status_key = new_order_status

        await session.commit()

        return CompleteResponse(
            success=True,
            data=CompleteResponseData(
                task_id=task.id,
                order_status_key=new_order_status,
                completed_at=str(task.completed_at),
            ),
        )


# ─── 历史记录 ────────────────────────────────────────────────────────────────


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    installer: InstallerAccount = Depends(get_current_installer),
):
    """获取安装工历史安装记录"""
    offset = (page - 1) * page_size
    today_month_start = date.today().replace(day=1)

    async with async_session() as session:
        # 本月统计
        completed_count_result = await session.execute(
            select(func.count(InstallTask.id)).where(
                and_(
                    InstallTask.installer_id == installer.id,
                    func.date(InstallTask.install_date) >= today_month_start,
                    InstallTask.status == "completed",
                )
            )
        )
        monthly_completed = completed_count_result.scalar() or 0

        pending_count_result = await session.execute(
            select(func.count(InstallTask.id)).where(
                and_(
                    InstallTask.installer_id == installer.id,
                    InstallTask.install_date >= today_month_start,
                    InstallTask.status.in_(["pending", "ongoing"]),
                )
            )
        )
        monthly_pending = pending_count_result.scalar() or 0

        # 历史记录
        history_result = await session.execute(
            select(InstallTask)
            .where(
                and_(InstallTask.installer_id == installer.id, InstallTask.status == "completed")
            )
            .order_by(InstallTask.completed_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        records = history_result.scalars().all()

        # 总数
        total_result = await session.execute(
            select(func.count(InstallTask.id)).where(
                and_(InstallTask.installer_id == installer.id, InstallTask.status == "completed")
            )
        )
        total = total_result.scalar() or 0

        record_items = [
            HistoryRecord(
                id=r.id,
                order_no=r.order_no or f"ORDER-{r.order_id}",
                customer_name=r.customer_name,
                address=r.address or "",
                content=r.order_content,
                completed_at=str(r.completed_at) if r.completed_at else "",
                remark=r.completion_remark,
            )
            for r in records
        ]

        await session.commit()

        return HistoryResponse(
            success=True,
            data=HistoryResponseData(
                monthly_completed=monthly_completed,
                monthly_pending=monthly_pending,
                total=total,
                page=page,
                page_size=page_size,
                records=record_items,
            ),
        )
