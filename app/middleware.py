# app/middleware.py
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import ALGORITHM, SECRET_KEY

ALLOWED_PATHS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
}


def is_public_path(path: str) -> bool:
    if path.startswith("/static/"):
        return True
    if path in ALLOWED_PATHS:
        return True
    # 公开 API
    if path == "/api/auth/login":
        return True
    if path == "/api/auth/send-code":
        return True
    if path == "/api/dicts":
        return True
    if path.startswith("/api/track"):
        return True  # 客户查进度，无需登录
    if path.startswith("/api/installer"):
        return True  # 安装工独立认证
    if path.startswith("/api/sms"):
        return True  # 短信发送公开
    return False


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 公开路径直接过
        if is_public_path(path):
            return await call_next(request)

        # API 路径需要 token
        if path.startswith("/api/"):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401, content={"success": False, "error": "请先登录"}
                )
            token = auth_header[7:]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                request.state.user_id = int(payload.get("sub", 0))
                request.state.user_name = payload.get("name", "")
                request.state.user_role = payload.get("role", "staff")
            except JWTError:
                return JSONResponse(
                    status_code=401, content={"success": False, "error": "登录已过期，请重新登录"}
                )

        return await call_next(request)
