"""
金典软装ERP - 系统配置
支持环境变量加载和 .env 文件
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，从环境变量或 .env 文件加载"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── 项目信息 ──────────────────────────────────────────────
    APP_NAME: str = "金典软装ERP"
    APP_VERSION: str = "4.0.0"
    APP_DESCRIPTION: str = "金典软装销售管理系统 - 全链路数字化管理平台"
    DEBUG: bool = False

    # ── 路径 ──────────────────────────────────────────────────
    BASE_DIR: Path = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    DATA_DIR: Path = BASE_DIR / "data"

    # ── 数据库 ────────────────────────────────────────────────
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/jindian.db"
    DB_ECHO: bool = False  # SQL 日志（开发时开启）

    # ── JWT ────────────────────────────────────────────────────
    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 7200  # 开发阶段 300 天不过期

    # ── CORS ──────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:8000"

    # ── 门店信息 ──────────────────────────────────────────────
    STORE_NAME: str = "金典软装"
    STORE_PHONE: str = "0571-xxxx-xxxx"
    STORE_ADDRESS: str = "杭州古墩路欧亚达家居广场"

    # ── 日志 ──────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s"

    # ── 分页默认值 ────────────────────────────────────────────
    PAGE_DEFAULT_SIZE: int = 20
    PAGE_MAX_SIZE: int = 200

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()

# ── 确保数据目录存在 ──────────────────────────────────────────
os.makedirs(settings.DATA_DIR, exist_ok=True)
