# 金典软装销售系统 V2.2 — 本地开发环境

> 面向：金典软装管理团队
> 版本：V2.2 Demo（客户进度查询 + 安装工手机端）
> 日期：2026-04-14

---

## 🚀 快速启动

### 第一步：启动后端服务

```bash
cd /home/tianlj0320/sales-system-dev

# 如果还没装依赖
./venv/bin/pip install -r requirements.txt

# 启动服务
./venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

服务地址：`http://localhost:8000`
API 文档：`http://localhost:8000/docs`

---

## 📱 访问页面

| 页面 | 地址 | 说明 |
|------|------|------|
| 管理端 | `index.html`（双击直接打开）| 电脑端管理（需配合后端）|
| 客户查进度 | `http://localhost:8000/static/track.html` | 手机扫码查订单进度 |
| 安装工端 | `http://localhost:8000/static/installer.html` | 手机端安装任务操作 |

---

## 🔑 演示账号

| 角色 | 手机号 | 验证码 | 说明 |
|------|--------|--------|------|
| 客户查询 | `20260411002` | `3333` | 扫码查王五订单 |
| 安装工 | `13800001111` | `888888` | 张师傅账号 |

---

## 📊 演示数据

| 数据 | 内容 |
|------|------|
| 订单 | 5张（编号 20260409002 ~ 20260413001）|
| 客户 | 5位（张三/李四/王五/赵六/孙七）|
| 安装工 | 2位（张师傅/王师傅）|
| 产品 | 5款（婴儿绒雪尼尔/亚麻纱/杜亚轨道等）|

---

## 📁 项目结构

```
sales-system-dev/
├── main.py              # FastAPI 后端入口
├── requirements.txt     # Python 依赖
├── sales.db            # SQLite 数据库
├── seed_data.py       # 初始化演示数据
├── README.md          # 本文件
├── app/
│   ├── models.py      # 数据库模型（11张表）
│   ├── schemas.py     # Pydantic 模型
│   ├── database.py    # 数据库连接
│   ├── core/
│   │   └── config.py  # 配置
│   └── api/
│       ├── track.py       # 客户查进度 API
│       ├── installer.py   # 安装工 API
│       └── sms.py         # 短信验证码 API
└── static/
    ├── installer.html  # 安装工手机端页面
    └── track.html     # 客户查进度页面
```

---

## 🔌 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `GET /health` | GET | 健康检查 |
| `GET /api/track` | GET | 客户扫码查进度 |
| `POST /api/sms/send` | POST | 发送验证码（Demo固定888888）|
| `POST /api/installer/login` | POST | 安装工登录 |
| `GET /api/installer/tasks` | GET | 今日/指定日期安装任务 |
| `POST /api/installer/tasks/{id}/complete` | POST | 确认安装完成 |
| `GET /api/installer/history` | GET | 历史安装记录 |

详细接口文档：`http://localhost:8000/docs`

---

## 📝 常用操作

### 重新初始化数据库（清空数据）
```bash
cd /home/tianlj0320/sales-system-dev
./venv/bin/python seed_data.py
```

### 查看当前有哪些安装任务
```bash
curl -s -X POST http://localhost:8000/api/installer/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800001111","code":"888888"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('Token:', d['data']['token'])"
```

---

## ⚠️ 注意事项

1. **后端必须先启动**，前端页面才能正常加载数据
2. 手机端访问时，确保手机和电脑在同一局域网（WSL 端口 8000）
3. 演示验证码固定为 `888888`，不需要真实发短信
4. 这是**本地开发环境**，正式上线需要部署到阿里云 ECS

---

## 🛠️ 技术栈

| 层 | 技术 |
|----|------|
| 后端 | FastAPI + SQLAlchemy + SQLite |
| 前端 | 原生 HTML/CSS/JS（无框架依赖）|
| 认证 | JWT Token |
| 手机适配 | 响应式 CSS + 移动端优先 |
