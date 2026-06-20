# 📦 Inventory & Order Management System — Execution Plan

> **Assessment**: Ethara AI — Software Engineer
> **Goal**: Build a *simplified* full-stack Inventory & Order Management System, fully containerized, and deployed online with public URLs.
> **Guiding principle**: Build exactly what the spec asks — clean, correct, and complete. No over-engineering.

---

## 1. Scope (from the assessment)

### ✅ In scope
- **Products** — full CRUD (name, SKU, price, quantity in stock)
- **Customers** — create / list / get / delete (full name, email, phone)
- **Orders** — create / list / get / cancel-delete (customer ref, product items, quantity, total)
- **Inventory tracking** — stock lives on the product; auto-reduced on order; low-stock detection
- **Dashboard** — total products, total customers, total orders, low-stock products
- **Docker** — 3 services (frontend, backend, postgres) via docker-compose
- **Deployment** — backend on Render/Railway/Fly.io, frontend on Vercel/Netlify

### ❌ Explicitly NOT in scope (do not build)
Authentication / JWT / RBAC, Redis, suppliers, warehouses, categories, separate
purchase vs. sales orders, audit logs, multi-warehouse inventory, optimistic locking,
file uploads. *(These were in the old plan and are not required by the assignment.)*

---

## 2. Tech Stack (right-sized)

| Layer | Choice | Why |
|---|---|---|
| **Backend** | Python 3.12 + **FastAPI** + Pydantic v2 | Spec-allowed, auto Swagger docs, fast |
| **ORM** | SQLAlchemy 2.0 | Mature; `create_all()` on startup (no Alembic needed for this scope) |
| **Database** | PostgreSQL 16 (alpine) | Required by spec |
| **Frontend** | **React (JavaScript)** + Vite | Spec requires React (JavaScript), Vite for fast static build |
| **Data fetching / state** | TanStack React Query + axios | Satisfies "proper state management" cleanly |
| **UI** | Tailwind CSS | Fast, responsive, professional |
| **Forms / UX** | react-hook-form + react-hot-toast | Form validation + clear error/success messages |
| **Routing** | react-router-dom | Pages for Dashboard/Products/Customers/Orders |
| **Container** | Docker + docker-compose (3 services) | Required by spec |

> **Frontend ↔ Backend**: Frontend calls the backend via `VITE_API_URL` (build-time env var).
> Local: `http://localhost:8000`. Prod: the public Render/Railway URL. Backend enables **CORS**.
> No nginx reverse-proxy needed since frontend and backend deploy to separate hosts.

---

## 3. Repo Structure (monorepo)

```
inventory-management/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, router includes, create_all on startup
│   │   ├── config.py          # Pydantic settings (env vars)
│   │   ├── database.py        # engine + SessionLocal + get_db dependency
│   │   ├── models.py          # SQLAlchemy: Product, Customer, Order, OrderItem
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── seed.py            # optional demo data (idempotent)
│   │   └── routers/
│   │       ├── products.py
│   │       ├── customers.py
│   │       ├── orders.py
│   │       └── dashboard.py
│   ├── tests/                 # pytest: business rules (stock, uniqueness, totals)
│   ├── requirements.txt
│   ├── Dockerfile             # production-ready, slim base, non-root user
│   └── .dockerignore
├── frontend/
│   ├── src/
│   │   ├── api/               # axios client + endpoint functions
│   │   ├── components/        # Layout, Table, Modal, FormFields, StatCard
│   │   ├── pages/             # Dashboard, Products, Customers, Orders, OrderDetail
│   │   ├── App.jsx, main.jsx
│   ├── package.json
│   ├── Dockerfile             # multi-stage: vite build → nginx static serve
│   ├── nginx.conf             # SPA fallback (try_files → index.html)
│   └── .dockerignore
├── docker-compose.yml         # frontend + backend + postgres
├── .env.example
├── .gitignore
└── README.md
```

---

## 4. Data Model (4 tables)

```diagram
╭───────────╮        ╭──────────────╮        ╭───────────╮
│ customers │1──────∞│    orders    │∞──────1│ customers │
╰───────────╯        ╰──────┬───────╯        ╰───────────╯
                            │1
                            │
                            ∞
                     ╭──────────────╮        ╭───────────╮
                     │ order_items  │∞──────1│ products  │
                     ╰──────────────╯        ╰───────────╯
```

**products**: `id` PK, `name`, `sku` UNIQUE NOT NULL, `price` NUMERIC(12,2) CHECK > 0,
`quantity` INT NOT NULL DEFAULT 0 CHECK >= 0, `low_stock_threshold` INT DEFAULT 10,
`created_at`, `updated_at`.

**customers**: `id` PK, `full_name`, `email` UNIQUE NOT NULL, `phone`, `created_at`.

**orders**: `id` PK, `customer_id` FK→customers (RESTRICT), `total_amount` NUMERIC(14,2),
`created_at`.  *(No status column — DELETE hard-deletes the order and restores stock.)*

**order_items**: `id` PK, `order_id` FK→orders (CASCADE), `product_id` FK→products (RESTRICT),
`quantity` INT CHECK > 0, `unit_price` NUMERIC(12,2)  *(price snapshot at order time)*.

---

## 5. API Endpoints

Paths match the spec exactly. All return proper HTTP status codes and JSON errors.

### Products
| Method | Path | Notes |
|---|---|---|
| POST | `/products` | 201; 409 if SKU duplicate; 422 on validation |
| GET | `/products` | 200; list all products |
| GET | `/products/{id}` | 200; 404 if not found |
| PUT | `/products/{id}` | 200; 404; 409 on SKU conflict |
| DELETE | `/products/{id}` | 204; 409 if referenced by orders |

### Customers
| Method | Path | Notes |
|---|---|---|
| POST | `/customers` | 201; 409 if email duplicate |
| GET | `/customers` | 200; list |
| GET | `/customers/{id}` | 200; 404 |
| DELETE | `/customers/{id}` | 204; 409 if has orders |

### Orders
| Method | Path | Notes |
|---|---|---|
| POST | `/orders` | 201; validates stock; reduces stock; computes total; 400 if insufficient stock; 404 if bad refs |
| GET | `/orders` | 200; list with customer name + item count |
| GET | `/orders/{id}` | 200; full detail with items; 404 |
| DELETE | `/orders/{id}` | 204; deletes order and **restores stock** |

### Dashboard & Health
| Method | Path | Returns |
|---|---|---|
| GET | `/dashboard/summary` | `{ total_products, total_customers, total_orders, low_stock_products: [...] }` |
| GET | `/health` | `{ status: "ok" }` (used by Docker + deploy health checks) |

**Error shape (consistent):** `{ "detail": "<message>" }` (FastAPI default) — keep it simple and standard.

---

## 6. Business Logic (the graded core)

Implement and **unit-test** every rule:

1. **Unique SKU** — DB unique constraint + pre-check → `409 Conflict` with clear message.
2. **Unique customer email** — DB unique constraint + pre-check → `409`.
3. **Quantity never negative** — CHECK constraint + validation; orders cannot push below 0.
4. **Insufficient stock blocks order** — for each item, verify `product.quantity >= requested`; else `400` listing the offending product(s). No partial order is written.
5. **Auto stock reduction** — on successful order, decrement `product.quantity` for each item, **inside one DB transaction** (all-or-nothing).
6. **Auto total calculation** — `total_amount = Σ(unit_price × quantity)`, computed by backend from current product prices; client-supplied totals are ignored.
7. **Order delete restores stock** — deleting an order returns its item quantities to inventory (transactional).
8. **Validation everywhere** — Pydantic schemas validate types, required fields, positive numbers, email format.
9. **Correct HTTP codes** — 200/201/204 success; 400/404/409/422 errors.

---

## 7. Frontend (React, JavaScript)

**Pages**
- **Dashboard** — 4 stat cards (Total Products, Total Customers, Total Orders, Low-Stock count) + a low-stock products table.
- **Products** — table (Name, SKU, Price, Qty, low-stock badge) + Add/Edit modal + Delete confirm.
- **Customers** — table (Name, Email, Phone) + Add modal + Delete confirm.
- **Orders** — table (Order #, Customer, Items, Total, Date) + "Create Order" page/modal + Order detail view.
- **Create Order flow** — pick customer → add product line items (qty), live-preview running total (server is source of truth), submit; show clear error if stock insufficient.

**Cross-cutting UX (UI/UX requirements)**
- Responsive layout (sidebar/topbar collapses on mobile) via Tailwind.
- Form validation with inline errors (react-hook-form).
- Toast notifications for success/error (react-hot-toast).
- Loading + empty states on every list.
- Organized component structure; React Query for server state.

---

## 8. Docker (3 services — mandatory)

**docker-compose.yml**
```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes: [ pgdata:/var/lib/postgresql/data ]   # named volume (required)
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s; timeout: 5s; retries: 5

  backend:
    build: ./backend
    environment:
      DATABASE_URL: ${DATABASE_URL}
      CORS_ORIGINS: ${CORS_ORIGINS}
    depends_on: { db: { condition: service_healthy } }
    ports: ["8000:8000"]

  frontend:
    build:
      context: ./frontend
      args: { VITE_API_URL: ${VITE_API_URL} }   # baked at build time
    depends_on: [ backend ]
    ports: ["3000:80"]

volumes:
  pgdata:
```

**Requirements satisfied**: slim base images (`postgres:16-alpine`, `python:3.12-slim`,
`node:20-alpine`→`nginx:alpine`), production-ready backend Dockerfile (non-root user),
`.dockerignore` for both, env-var config (no hardcoded credentials), named volume for Postgres.

**Verify**: `cp .env.example .env && docker compose up --build` → frontend on `:3000`,
backend Swagger on `:8000/docs`, all CRUD + order flow work end-to-end.

---

## 9. Deployment (public URLs — required deliverable)

```diagram
╭────────────────────╮      HTTPS      ╭─────────────────────╮      ╭──────────────╮
│ Frontend (Vercel/  │ ───────────────▶│ Backend (Render/     │─────▶│ Postgres     │
│ Netlify) static SPA │  VITE_API_URL   │ Railway/Fly.io)      │      │ (managed)    │
╰────────────────────╯                 ╰─────────────────────╯      ╰──────────────╯
```

1. **Backend** → Render (or Railway/Fly.io): deploy from `backend/` Dockerfile, attach a managed
   PostgreSQL, set `DATABASE_URL` + `CORS_ORIGINS` (the frontend URL). Confirm `/health` + `/docs`.
2. **Frontend** → Vercel (or Netlify): build from `frontend/`, set `VITE_API_URL` = public backend URL.
3. **Push backend image to Docker Hub** → `docker build`, `docker tag`, `docker push` → record image link.
4. Verify the deployed frontend successfully performs CRUD + creates an order against the live backend.

---

## 10. Build Order (task breakdown)

| # | Task | Output |
|---|---|---|
| 1 | Scaffold repo: `backend/`, `frontend/`, `.gitignore`, `.env.example` | Skeleton |
| 2 | Backend: config, database, models (4 tables), `create_all` on startup, `/health` | App boots, tables created |
| 3 | Backend: Pydantic schemas | Request/response validation |
| 4 | Backend: Products router (CRUD + unique SKU) | Products API |
| 5 | Backend: Customers router (CRUD + unique email) | Customers API |
| 6 | Backend: Orders router (stock check, auto-reduce, auto-total, cancel→restore, all transactional) | Orders API |
| 7 | Backend: Dashboard router (summary + low stock) | Dashboard API |
| 8 | Backend: pytest for business rules (rules 1–7) | Green tests |
| 9 | Backend: Dockerfile + `.dockerignore` | Backend image |
| 10 | Frontend: Vite scaffold, Tailwind, router, axios client, React Query | App shell |
| 11 | Frontend: layout + reusable Table/Modal/StatCard/Form components | UI kit |
| 12 | Frontend: Products page (CRUD) | Page works |
| 13 | Frontend: Customers page (CRUD) | Page works |
| 14 | Frontend: Orders pages (list, create flow, detail) | Page works |
| 15 | Frontend: Dashboard page | Page works |
| 16 | Frontend: Dockerfile + nginx.conf + `.dockerignore` | Frontend image |
| 17 | Root: docker-compose, full `docker compose up` smoke test | One-command run |
| 18 | (Optional) seed demo data | Populated demo |
| 19 | Deploy backend (Render) + push Docker Hub image | Live backend + image link |
| 20 | Deploy frontend (Vercel) wired to live backend | Live frontend URL |
| 21 | README (overview, setup, env vars, API list, live URLs, credentials if any) | Submission-ready |

---

## 11. Definition of Done / Submission Checklist

- [ ] `docker compose up --build` runs all 3 services from a clean clone
- [ ] Products CRUD works; duplicate SKU rejected (409)
- [ ] Customers CRUD works; duplicate email rejected (409)
- [ ] Order creation reduces stock, computes total server-side, blocks on insufficient stock
- [ ] Order delete restores stock
- [ ] Dashboard shows totals + low-stock products
- [ ] Responsive UI, form validation, success/error toasts, loading/empty states
- [ ] No hardcoded credentials; all config via env vars; named Postgres volume
- [ ] Slim images; production backend Dockerfile (non-root)
- [ ] `pytest` passes for business rules
- [ ] Swagger docs at `/docs`
- [ ] **Deliverables ready**:
  - [ ] GitHub repo link (frontend + backend)
  - [ ] Docker Hub image link (backend)
  - [ ] Live frontend URL (Vercel/Netlify)
  - [ ] Live backend API URL (Render/Railway/Fly.io)
- [ ] README documents setup, env vars, API, and the 4 deliverable links

---

> ⚠️ **Commit rule**: use `./commit-as-rrr.sh "message"` for all commits (see `agents.md`).
