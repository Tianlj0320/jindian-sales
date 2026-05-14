"""
统一 API 响应格式
所有 API 必须使用这里定义的响应函数
"""

from typing import Any

from pydantic import BaseModel


class CommonResponse(BaseModel):
    """通用响应格式"""

    success: bool
    data: Any | None = None
    error: str | None = None
    message: str | None = None


class ListResponse(BaseModel):
    """列表响应格式"""

    success: bool = True
    total: int = 0
    items: list[Any] = []


def success_response(data: Any = None, message: str | None = None) -> dict:
    """成功响应"""
    return CommonResponse(success=True, data=data, message=message).model_dump(exclude_none=True)


def error_response(error: str, message: str | None = None) -> dict:
    """错误响应"""
    return CommonResponse(success=False, error=error, message=message).model_dump(exclude_none=True)


def list_response(items: list[Any], total: int | None = None) -> dict:
    """列表响应"""
    if total is None:
        total = len(items)
    return ListResponse(success=True, total=total, items=items).model_dump()
