"""
客户相关 Pydantic 模型
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    """创建客户"""
    name: str = Field(..., description="客户姓名")
    phone: str = Field(..., description="联系电话")
    type: str = Field(default="retail", description="客户类型")
    source: str = Field(default="", description="客户来源")
    address: str = Field(default="", description="地址")
    community: str = Field(default="", description="小区")
    level: str = Field(default="C", description="客户等级")
    remark: str | None = None


class CustomerUpdate(BaseModel):
    """更新客户"""
    name: str | None = None
    phone: str | None = None
    type: str | None = None
    source: str | None = None
    address: str | None = None
    community: str | None = None
    level: str | None = None
    salesperson_id: int | None = None
    next_followup_date: date | None = None
    tags: list[str] | None = None
    remark: str | None = None


class FollowupCreate(BaseModel):
    """创建跟进记录"""
    type: str = Field(default="", description="跟进方式")
    content: str = Field(..., description="跟进内容")
    result: str = Field(default="", description="跟进结果")
    next_date: str | None = Field(None, description="下次跟进日期")


class FollowupUpdate(BaseModel):
    """更新跟进记录"""
    type: str | None = None
    content: str | None = None
    result: str | None = None
    next_date: str | None = None


class CustomerResponse(BaseModel):
    """客户响应"""
    id: int
    name: str
    phone: str
    type: str
    source: str
    level: str
    address: str
    community: str
    salesperson_name: str
    total_orders: int
    total_amount: float
    debt: float
    next_followup_date: str | None
    last_contact_at: str | None
    tags: list
    remark: str | None
    created_at: str
