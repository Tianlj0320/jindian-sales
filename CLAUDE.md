# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

金典软装ERP V4.0 — A curtain/fabric ERP system. Vue 3 + Element Plus frontend, FastAPI + SQLAlchemy 2.0 async backend, SQLite database.

## Commands

### Backend (D:/project/backend/)

```bash
# Run all tests
cd D:/project/backend && python -m pytest -v

# Run a single test file
cd D:/project/backend && python -m pytest tests/test_order_status.py -v

# Run a specific test class or method
cd D:/project/backend && python -m pytest tests/test_order_status.py::TestOrderStatusProgression -v

# Start backend dev server (port 8108)
cd D:/project/backend && python main.py

# Lint and format
cd D:/project/backend && ruff check app/
cd D:/project/backend && ruff format app/ --check
cd D:/project/backend && make check    # lint + format-check + typecheck + test

# Install deps
cd D:/project/backend && pip install -r requirements.txt -r requirements-test.txt
```

### Frontend (D:/project/frontend/)

```bash
# Run unit tests
cd D:/project/frontend && npm test

# Start dev server (port 5182, proxies /api -> localhost:8108)
cd D:/project/frontend && npm run dev

# Lint and format
cd D:/project/frontend && npm run lint
cd D:/project/frontend && npm run format:check
cd D:/project/frontend && make check  # lint + format-check + test

# Build for production
cd D:/project/frontend && npm run build
```

## Architecture

### Dual-Backend Legacy

The repo contains **two independent backends**:
- **Active**: `backend/` — FastAPI + SQLAlchemy 2.0 async + aiosqlite (port 8108). This is the current system.
- **Legacy**: `app/` — Old Flask app (port 8000). Do NOT modify. Only kept for reference.

Always work in `backend/`, never `app/`.

### Backend Structure (backend/)

```
backend/
├── main.py                  # FastAPI entry point, startup, migrations, route registration
├── app/
│   ├── api/v1/              # Route handlers (one file per module)
│   │   ├── auth.py          # Login, user management, permissions
│   │   ├── orders.py        # Order CRUD, status machine, rollback, supplementary orders
│   │   ├── finance.py       # Receivables, payables, expenses, summary
│   │   ├── deposits.py      # Customer deposit management
│   │   ├── after_sales.py   # After-sales service (state machine workflow)
│   │   ├── purchases.py     # Purchase orders, split, receive, QR codes
│   │   ├── warehouses.py    # Warehouse inventory, flows, storage locations
│   │   └── ...              # products, customers, installations, system, etc.
│   ├── core/                # Config, exceptions, middleware, security, response helpers
│   ├── domain/              # SQLAlchemy ORM models (one file per entity)
│   │   ├── base.py          # Base class, TimestampMixin, SoftDeleteMixin
│   │   ├── order.py         # Order + OrderItem models
│   │   ├── after_sale.py    # AfterSaleService model + state machine validation
│   │   ├── finance.py       # FinanceReceivable, FinancePayable, FinanceExpense
│   │   ├── deposit.py       # Deposit model
│   │   └── ...              # auth, customer, product, purchase, warehouse, etc.
│   ├── schemas/             # Pydantic V2 request/response models (mirrors domain/)
│   └── services/
│       └── status_engine.py # Order status state machine (12 statuses, transitions)
├── tests/                   # pytest tests (asyncio, in-memory SQLite, httpx client)
│   ├── conftest.py          # Fixtures: test DB, auth token, seed data
│   ├── test_order_status.py # Order status progression tests
│   ├── test_products.py     # Product CRUD tests
│   └── test_purchase_flow.py# Purchase split flow tests
└── data/                    # SQLite database files (gitignored)
```

### Frontend Structure (frontend/)

```
frontend/
├── src/
│   ├── main.js              # Vue app bootstrap, Pinia, Element Plus, icon registration
│   ├── App.vue              # Root component (<router-view>)
│   ├── api/index.js         # Axios instance with JWT interceptor + all API methods
│   ├── router/index.js      # Vue Router (hash history) with auth guard + permission check
│   ├── stores/auth.js       # Pinia store: token, user, permissions, login/logout
│   ├── utils/               # theme.js, print.js (processing order HTML generation)
│   ├── views/               # Page components by module
│   │   ├── layout/MainLayout.vue  # Sidebar + header + router-view
│   │   ├── orders/          # OrderList, OrderDetail, OrderForm
│   │   ├── finance/         # FinanceView (5 tabs), DepositPanel
│   │   ├── after_sales/     # AfterSaleList (state machine UI)
│   │   └── ...
│   └── __tests__/           # Vitest unit tests
├── public/themes/           # 7 CSS theme files + base.css
└── vite.config.js           # Port 5182, proxy /api -> localhost:8108
```

### Route → Permission Mapping

Defined in `router/index.js` (`ROUTE_PERM` object). Each path maps to a permission key. The auth guard in `router.beforeEach` checks `auth.hasPermission(needed)`.

Permission keys: `dashboard`, `orders`, `purchases`, `warehouse`, `production`, `installations`, `finance`, `reports`, `products`, `customers`, `system`, `admin`

### API Response Format

All endpoints return `ApiResponse`:
```python
{"success": true, "data": {...}, "error": null, "message": null}
# or paginated:
{"success": true, "items": [...], "total": N, "page": 1, "page_size": 20}
```

Use `from app.core.response import success, paginated, error` in route handlers.
Use `from app.core.exceptions import NotFoundError, BusinessError, UnauthorizedError` for errors.

### Database Migrations

Migrations run automatically on startup in `main.py`'s `startup` event. They use SQLite `ALTER TABLE` with column existence checks via `inspector.get_columns()`. Each migration is numbered (迁移1 through 迁移21 currently). Add new migrations at the end of the `run_migration()` function inside `startup`.

Seed data is ensured via `_ensure_dict_data()` (upserts dict types/items) and `_seed_data()` (runs only on empty DB).

### Key Patterns

- **Async SQLAlchemy 2.0**: `select(Model).where(...)`, `await session.execute()`, `result.scalar_one_or_none()`, `result.scalars().all()`
- **Dependency injection**: `SessionDep`, `CurrentUserDep`, `PageDep` from `app.api.deps`
- **State machines**: Order status engine in `services/status_engine.py` (12 statuses); after-sales state machine defined inline in `domain/after_sale.py` with `VALID_TRANSITIONS` dict
- **Process control**: After-sales with `order_hold=True` blocks order advancement; checked in `orders.py` advance/rollback endpoints
- **JWT auth**: Bearer token via `HTTPBearer`, decoded in `get_current_user` dependency
- **Automatic session commit**: `get_session()` commits on success, rolls back on exception
- **All API errors go through `AppException`** subclasses, caught by middleware and returned as `{"success": false, "error": "..."}`

### Important Notes

- The frontend Vite dev server proxies `/api` to `http://localhost:8108`. Backend runs on port 8108.
- When restarting the backend after model changes, the migration runs automatically on startup.
- The test suite uses an in-memory SQLite DB with `os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"` set in `conftest.py` **before** any app imports.
- Tests create a fresh database per module and seed admin user + basic data.
- `conftest.py` sets env vars BEFORE importing app modules — never import app modules at module level in test files.
