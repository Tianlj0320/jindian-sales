"""
生产反馈 Pydantic 模型
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProductionFeedbackCreate(BaseModel):
    """创建生产反馈"""
    order_id: int = Field(..., description="订单ID")
    order_no: str = Field(default="")
    feedback_type: str = Field(default="quality", description="类型: quality/defect/shortage")
    description: str = Field(default="", description="问题描述")
    photos: list[str] = Field(default_factory=list, description="图片URL列表")


class ProductionFeedbackUpdate(BaseModel):
    """更新生产反馈"""
    feedback_type: str | None = None
    description: str | None = None
    photos: list[str] | None = None
    status: str | None = None
    resolver: str | None = None
    resolution: str | None = None


class ProductionFeedbackResponse(BaseModel):
    id: int
    feedback_no: str
    order_id: int | None
    order_no: str
    purchase_order_id: int | None
    feedback_type: str
    description: str
    photos: list = []
    status: str
    resolver: str
    resolution: str
    resolved_at: datetime | None
    created_at: datetime | None
