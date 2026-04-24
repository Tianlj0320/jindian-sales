# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import init_db
from app.middleware import AuthMiddleware
from app.api import track, installer, sms, orders, customers, products, employees, dashboard, purchase, warehouse, finance, reports, auth, print_api
from app.api import purchase_orders, production_feedback, installation_orders

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(
    title="金典软装销售系统 API",
    version="3.0.0",
    description="V3.0 窗帘行业特性：采购拆分 + 生产反馈 + 安装单"
)

# CORS
# ⚠️ 生产环境：allow_origins 必须改为明确域名列表，禁止 "*" + credentials 同时使用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth 中间件（保护所有 /api/ 路径，公开路径除外）
app.add_middleware(AuthMiddleware)

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
app.include_router(auth.router)
app.include_router(print_api.router)
app.include_router(purchase_orders.router)
app.include_router(production_feedback.router)
app.include_router(installation_orders.router)


@app.on_event("startup")
async def startup():
    await init_db()


from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
