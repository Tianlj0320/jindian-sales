"""员工登录认证 API"""
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from jose import jwt
from app.database import async_session
from app.models import Employee
from sqlalchemy import select

router = APIRouter(prefix="/api/auth", tags=["认证"])

SECRET_KEY = os.environ.get("JWT_SECRET", "jd软装-v2.2-secret-2026")
ALGORITHM = "HS256"
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


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """员工登录：手机号+密码（demo密码统一jd8888）"""
    async with async_session() as session:
        result = await session.execute(select(Employee).where(Employee.phone == req.phone))
        emp = result.scalar_one_or_none()

    if not emp:
        return LoginResponse(success=False, error="手机号未注册")

    # demo用明文密码验证
    if req.password and req.password != "jd8888":
        return LoginResponse(success=False, error="密码错误")

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
