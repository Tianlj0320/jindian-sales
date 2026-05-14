"""
全局中间件
"""

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.response import ApiResponse


def register_middlewares(app: FastAPI) -> None:
    """注册所有中间件"""
    _add_cors_middleware(app)
    _add_exception_handler(app)
    _add_request_logging(app)


def _add_cors_middleware(app: FastAPI) -> None:
    """CORS 中间件"""
    from fastapi.middleware.cors import CORSMiddleware

    origins = settings.origins_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else ["*"],
        allow_credentials=bool(origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _add_exception_handler(app: FastAPI) -> None:
    """统一异常处理"""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiResponse(success=False, error=exc.message).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # 生产环境隐藏细节
        detail = "服务器内部错误" if not settings.DEBUG else str(exc)
        return JSONResponse(
            status_code=500,
            content=ApiResponse(success=False, error=detail).model_dump(),
        )


def _add_request_logging(app: FastAPI) -> None:
    """请求日志中间件"""

    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable) -> Response:
        import time
        from app.core.logging import logger

        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        logger.info(
            "%s %s → %s (%.0fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration * 1000,
        )
        return response
