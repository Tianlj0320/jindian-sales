"""员工登录认证 API"""
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from jose import jwt
from app.core.config import SECRET_KEY, ALGORITHM
from app.database import async_session
from app.models import Employee
from sqlalchemy import select

router = APIRouter(prefix="/api/auth", tags=["认证"])
EXPIRE_HOURS = 72

class LoginRequest(BaseModel):
    phone: str
    password: str = ""


class LoginResponse(BaseModel):
    success: bool
    token: str = ""
    user_id: int = None
    name: str = ""
    role: str = "staff"
    error: str = None


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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None


LOGIN_FAIL_COUNTER: dict[str, list] = {}  # phone -> [timestamp, ...]
LOGIN_LOCK_DURATION = 300  # 5分钟内失败3次则封禁
MAX_LOGIN_FAILS = 3


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """员工登录：手机号+密码"""
    now = datetime.utcnow()

    # 暴力破解防护：检查失败次数
    fails = LOGIN_FAIL_COUNTER.get(req.phone, [])
    fails = [t for t in fails if (now - t).total_seconds() < LOGIN_LOCK_DURATION]
    if len(fails) >= MAX_LOGIN_FAILS:
        remaining = LOGIN_LOCK_DURATION - int((now - fails[0]).total_seconds())
        return LoginResponse(success=False, error=f"登录失败次数过多，请{remaining}秒后重试")

    async with async_session() as session:
        result = await session.execute(select(Employee).where(Employee.phone == req.phone))
        emp = result.scalar_one_or_none()

    if not emp:
        return LoginResponse(success=False, error="手机号未注册")

    # 验证密码
    if not req.password:
        return LoginResponse(success=False, error="请输入密码")

    # 有 password_hash 则用 bcrypt 验证，否则拒绝
    if emp.password_hash:
        import bcrypt
        if not bcrypt.checkpw(req.password.encode("utf-8"), emp.password_hash.encode("utf-8")):
            LOGIN_FAIL_COUNTER[req.phone] = fails + [now]
            return LoginResponse(success=False, error="密码错误")
    else:
        return LoginResponse(success=False, error="该账号未设置密码，请联系管理员")

    # 验证通过，清除失败记录
    LOGIN_FAIL_COUNTER.pop(req.phone, None)

    token = create_token(emp.id, emp.name, emp.position or "staff")
    role = "admin" if emp.position in ["老板", "经理"] else "staff"
    return LoginResponse(
        success=True,
        token=token,
        user_id=emp.id,
        name=emp.name,
        role=role,
    )


@router.get("/me")
async def get_me(authorization: str = Header(None)):
    """验证Token并返回当前用户信息"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization[7:]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token无效")
    return {"user_id": int(payload["sub"]), "name": payload["name"], "role": payload["role"]}
