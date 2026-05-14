"""
系统设置与字典模型
"""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base, TimestampMixin


class StoreConfig(Base, TimestampMixin):
    """门店配置"""

    __tablename__ = "store_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="配置键")
    value: Mapped[str] = mapped_column(Text, default="", comment="配置值")
    description: Mapped[str] = mapped_column(String(200), default="", comment="配置说明")


class DictType(Base, TimestampMixin):
    """字典类型定义"""

    __tablename__ = "dict_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dict_type: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="字典类型编码(如 order_type)")
    dict_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="字典类型名称(如 订单类型)")
    description: Mapped[str] = mapped_column(String(200), default="", comment="说明")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")


class DictItem(Base, TimestampMixin):
    """通用字典项（码表）"""

    __tablename__ = "dict_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dict_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="字典类型")
    dict_code: Mapped[str] = mapped_column(String(50), nullable=False, comment="字典编码")
    dict_label: Mapped[str] = mapped_column(String(100), nullable=False, comment="字典名称")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    remark: Mapped[str] = mapped_column(String(200), default="", comment="备注")
