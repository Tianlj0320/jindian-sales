"""
通用 Pydantic 模型
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel):
    """统一响应"""
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


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=200, description="每页条数")


class IdResponse(BaseModel):
    """ID 响应"""
    id: int
