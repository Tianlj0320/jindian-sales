# app/core/config.py
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'sales.db')}")

# JWT 密钥（强制环境变量配置）
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET environment variable must be set")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 15

# 门店配置
STORE_NAME = "金典软装"
STORE_PHONE = "0571-xxxx-xxxx"
