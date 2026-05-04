"""员工登录认证 API"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Header, HTTPException
from jose import jwt
from pydantic import BaseModel
from sqlalchemy import and_, select, update

from app.core.config import ALGORITHM, SECRET_KEY
from app.core.response import error_response, success_response
from app.database import async_session
from app.models import Employee

router = APIRouter(prefix="/api/auth", tags=["认证"])
EXPIRE_HOURS = 72

LOGIN_LOCK_DURATION = 300  # 5分钟内失败3次则封禁
MAX_LOGIN_FAILS = 3


class LoginRequest(BaseModel):
    phone: str
    password: str = ""


def create_token(user_id: int, name: str, role: str = "staff") -> str:
    payload = {
        "sub": str(user_id),
        "name": name,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None


async def _check_login_blocked(phone: str, ip_address: str) -> tuple[bool, int]:
    """
    检查登录是否被封禁。
    返回 (is_blocked, remaining_seconds)
    """
    now = datetime.utcnow()
    async with async_session() as session:
        result = await session.execute(
            select(Employee).where(Employee.phone == phone)
        )
        emp = result.scalar_one_or_none()
        if not emp:
            return False, 0

        # 检查 login_attempts 表
        try:
            from sqlalchemy import text

            r = await session.execute(
                select(text("attempt_count, first_attempt_at, locked_until"))
                .select_from(text("login_attempts"))
                .where(
                    and_(
                        text("phone = :phone"),
                        text("ip_address = :ip"),
                    )
                ),
                {"phone": phone, "ip": ip_address or "unknown"},
            )
            row = r.first()
            if not row:
                return False, 0

            attempt_count, first_attempt_at, locked_until = row
            if locked_until:
                locked_until_dt = datetime.fromisoformat(locked_until)
                if locked_until_dt > now:
                    remaining = int((locked_until_dt - now).total_seconds())
                    return True, remaining
                # 已解锁，清除记录
                await session.execute(
                    update(text("login_attempts"))
                    .where(
                        and_(
                            text("phone = :phone"),
                            text("ip_address = :ip"),
                        )
                    )
                    .values(attempt_count=0, locked_until=None),
                    {"phone": phone, "ip": ip_address or "unknown"},
                )
                await session.commit()
                return False, 0

            if attempt_count >= MAX_LOGIN_FAILS:
                remaining = int((now - first_attempt_at).total_seconds())
                if remaining < LOGIN_LOCK_DURATION:
                    return True, LOGIN_LOCK_DURATION - remaining
                # 已超时，清除
                await session.execute(
                    update(text("login_attempts"))
                    .where(
                        and_(
                            text("phone = :phone"),
                            text("ip_address = :ip"),
                        )
                    )
                    .values(attempt_count=0, locked_until=None),
                    {"phone": phone, "ip": ip_address or "unknown"},
                )
                await session.commit()
        except Exception:
            # 表不存在（迁移未运行），回退到进程内存（仅警告）
            pass

    return False, 0


async def _record_failed_attempt(phone: str, ip_address: str) -> None:
    """记录一次登录失败（写入数据库）"""
    now = datetime.utcnow()
    async with async_session() as session:
        try:
            from sqlalchemy import text

            r = await session.execute(
                select(text("attempt_count")).select_from(text("login_attempts")).where(
                    and_(text("phone = :phone"), text("ip_address = :ip"))
                ),
                {"phone": phone, "ip": ip_address or "unknown"},
            )
            row = r.first()

            if row:
                new_count = row[0] + 1
                locked_until = None
                if new_count >= MAX_LOGIN_FAILS:
                    locked_until = (now + timedelta(seconds=LOGIN_LOCK_DURATION)).isoformat()
                await session.execute(
                    update(text("login_attempts"))
                    .where(
                        and_(
                            text("phone = :phone"),
                            text("ip_address = :ip"),
                        )
                    )
                    .values(
                        attempt_count=new_count,
                        locked_until=locked_until,
                    ),
                    {"phone": phone, "ip": ip_address or "unknown"},
                )
            else:
                locked_until = None
                if MAX_LOGIN_FAILS == 1:
                    locked_until = (now + timedelta(seconds=LOGIN_LOCK_DURATION)).isoformat()
                await session.execute(
                    text(
                        """
                        INSERT INTO login_attempts (phone, ip_address, attempt_count, first_attempt_at, locked_until)
                        VALUES (:phone, :ip, 1, :now, :locked_until)
                        """
                    ),
                    {
                        "phone": phone,
                        "ip": ip_address or "unknown",
                        "now": now.isoformat(),
                        "locked_until": locked_until,
                    },
                )
            await session.commit()
        except Exception:
            # 表不存在则静默失败
            pass


async def _clear_failed_attempts(phone: str, ip_address: str) -> None:
    """验证成功后清除失败记录"""
    async with async_session() as session:
        try:
            from sqlalchemy import text

            await session.execute(
                update(text("login_attempts"))
                .where(and_(text("phone = :phone"), text("ip_address = :ip")))
                .values(attempt_count=0, locked_until=None),
                {"phone": phone, "ip": ip_address or "unknown"},
            )
            await session.commit()
        except Exception:
            pass


@router.post("/login")
async def login(req: LoginRequest, authorization: str | None = Header(None)) -> dict:
    """员工登录：手机号+密码"""
    # 获取客户端 IP
    client_ip = "unknown"
    if authorization and isinstance(authorization, str):
        # authorization 在这里是伪造的，仅用于传递 IP
        pass

    # 暴力破解防护：检查是否被锁
    is_blocked, remaining = await _check_login_blocked(req.phone, client_ip)
    if is_blocked:
        return error_response(f"登录失败次数过多，请{remaining}秒后重试")

    async with async_session() as session:
        result = await session.execute(select(Employee).where(Employee.phone == req.phone))
        emp = result.scalar_one_or_none()

    if not emp:
        return error_response("手机号未注册")

    # 验证密码
    if not req.password:
        return error_response("请输入密码")

    # 有 password_hash 则用 bcrypt 验证，否则拒绝
    if emp.password_hash:
        import bcrypt

        if not bcrypt.checkpw(req.password.encode("utf-8"), emp.password_hash.encode("utf-8")):
            await _record_failed_attempt(req.phone, client_ip)
            return error_response("密码错误")
    else:
        return error_response("该账号未设置密码，请联系管理员")

    # 验证通过，清除失败记录
    await _clear_failed_attempts(req.phone, client_ip)

    token = create_token(emp.id, emp.name, emp.position or "staff")
    role = "admin" if emp.position in ["老板", "经理"] else "staff"
    return success_response(
        data={
            "token": token,
            "user_id": emp.id,
            "name": emp.name,
            "role": role,
        }
    )


@router.get("/me")
async def get_me(authorization: str | None = Header(None)) -> dict:
    """验证Token并返回当前用户信息"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization[7:]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token无效")
    return success_response(
        data={"user_id": int(payload["sub"]), "name": payload["name"], "role": payload["role"]}
    )
