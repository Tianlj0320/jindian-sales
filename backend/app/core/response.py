"""
统一 API 响应格式
所有 API 端点必须使用此模块的响应函数
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一响应模型"""

    success: bool = True
    data: Any = None
    error: str | None = None
    message: str | None = None


class PaginatedResponse(BaseModel):
    """分页响应"""

    success: bool = True
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: list[Any] = []


def success(data: Any = None, message: str | None = None) -> ApiResponse:
    """成功响应"""
    return ApiResponse(success=True, data=data, message=message)


def error(message: str, error_code: str | None = None) -> ApiResponse:
    """错误响应"""
    return ApiResponse(success=False, error=message, message=error_code)


def paginated(
    items: list[Any],
    total: int,
    page: int,
    page_size: int,
) -> PaginatedResponse:
    """分页响应"""
    return PaginatedResponse(
        success=True,
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )
