# 金典软装ERP V4.0 — 部署指南

---

## 1. 环境要求

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| Python | ≥ 3.12 | 推荐 3.12+ |
| Node.js | ≥ 18 | 前端构建 |
| npm | ≥ 9 | 前端包管理 |

---

## 2. 开发环境

### 2.1 后端启动

```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r backend/requirements.txt

# 初始化数据库
# 系统在首次启动时自动创建表和种子数据
cd backend
python main.py
```

### 2.2 前端启动

```bash
cd frontend
npm install
npm run dev
# 默认运行在 http://localhost:5173
```

### 2.3 开发配置

后端配置文件：`backend/app/core/config.py`

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| DATABASE_URL | sqlite+aiosqlite:///.../data/jindian.db | 数据库连接 |
| JWT_SECRET | dev-secret-change-in-production | JWT 签名密钥 |
| JWT_EXPIRE_HOURS | 72 | Token 过期时间 |
| ALLOWED_ORIGINS | http://localhost:5173,http://localhost:8000 | CORS 白名单 |
| LOG_LEVEL | INFO | 日志级别 |

可通过 `.env` 文件覆盖配置（放在 `backend/` 目录下）。

---

## 3. 生产环境

### 3.1 后端部署（Docker Compose 推荐）

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:password@db:5432/jindian
      - JWT_SECRET=<random-secret>
      - ALLOWED_ORIGINS=https://your-domain.com
      - LOG_LEVEL=INFO
    depends_on:
      - db
    volumes:
      - ./data:/app/backend/data

  db:
    image: postgres:16
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=jindian
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### 3.2 手动部署

```bash
# 1. 构建前端
cd frontend
npm install
npm run build
# 构建产物在 frontend/dist/

# 2. 安装后端依赖
cd ../backend
pip install -r requirements.txt

# 3. 配置生产环境变量（.env）
echo "DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/jindian" >> .env
echo "JWT_SECRET=<生成随机密钥>" >> .env
echo "ALLOWED_ORIGINS=https://your-domain.com" >> .env
echo "LOG_LEVEL=WARNING" >> .env

# 4. 启动服务
# 推荐使用 Supervisor 或 systemd 管理进程
pip install uvicorn[standard]
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3.3 Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API 文档
    location /docs {
        proxy_pass http://127.0.0.1:8000;
    }

    # 静态文件缓存
    location /assets/ {
        proxy_pass http://127.0.0.1:8000;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 4. 数据库迁移

### 4.1 SQLite → PostgreSQL 迁移

```bash
# 1. 导出 SQLite 数据
cd backend
python -c "
import sqlite3
import json

conn = sqlite3.connect('data/jindian.db')
# 使用 .dump 或逐表导出
cursor = conn.cursor()
cursor.execute('SELECT * FROM users')
rows = cursor.fetchall()
# ... 逐表导出为 JSON
"

# 2. 导入 PostgreSQL
# 使用 psql \copy 或 Python 脚本导入

# 3. 修改配置
# 更新 .env 中的 DATABASE_URL
```

### 4.2 自动迁移

系统启动时自动执行迁移（见 `main.py` startup 事件）：
- 为已有表添加新列（如 products.processing_type_id）
- 确保字典类型和数据存在

---

## 5. 维护操作

### 5.1 备份

```bash
# SQLite 备份
cp backend/data/jindian.db backend/data/jindian.db.backup.$(date +%Y%m%d)

# PostgreSQL 备份
pg_dump -U user jindian > jindian_backup_$(date +%Y%m%d).sql
```

### 5.2 日志

日志文件位置：`backend/logs/`（可配置）

日志级别调整：修改 `.env` 中的 `LOG_LEVEL` 为 `DEBUG`/`INFO`/`WARNING`/`ERROR`

### 5.3 种子数据重置

删除数据库文件后重启，系统会自动：
1. 创建所有表
2. 执行数据库迁移
3. 插入 28 种字典类型和 ~120 个字典项
4. 插入种子数据（用户、仓库、分类、供应商、角色）

---

## 6. 常见问题

### 6.1 数据库文件未创建

```bash
# 确保 data 目录存在
mkdir -p backend/data
# 检查权限
chmod 755 backend/data
```

### 6.2 前端页面空白

```bash
# 确认后端正确挂载了前端静态文件
# 访问 http://localhost:8000/health 应返回 {"status":"ok"}
# 如果前端 dist/ 目录不存在，先执行 npm run build
```

### 6.3 CORS 错误

```bash
# 确认 .env 中的 ALLOWED_ORIGINS 包含前端地址
ALLOWED_ORIGINS=http://localhost:5173,https://your-domain.com
```
