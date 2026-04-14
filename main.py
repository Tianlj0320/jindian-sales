# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import os

from app.database import init_db
from app.api import track, installer, sms, orders, customers, products, employees, dashboard, purchase, warehouse, finance, reports

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(
    title="金典软装销售系统 API",
    version="2.2.0",
    description="V2.2 客户进度查询 + 安装工手机端 API"
)

# CORS：允许所有来源（本地开发）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(track.router)
app.include_router(installer.router)
app.include_router(sms.router)
app.include_router(orders.router)
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(employees.router)
app.include_router(dashboard.router)
app.include_router(purchase.router)
app.include_router(warehouse.router)
app.include_router(finance.router)
app.include_router(reports.router)


@app.on_event("startup")
async def startup():
    """启动时初始化数据库"""
    await init_db()


@app.get("/")
async def root():
    """API 根路径，重定向到文档"""
    return {
        "name": "金典软装销售系统 API",
        "version": "2.2.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


# 挂载静态文件（前端页面）
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
