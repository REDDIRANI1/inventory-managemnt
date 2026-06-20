# Manual Testing Guide — Inventory & Order Management System

> [!IMPORTANT]
> **Prerequisites**: Make sure Docker containers are running.
> - Frontend: `http://127.0.0.1:3005`
> - Backend Swagger: `http://127.0.0.1:8000/docs`
> - Backend API: `http://127.0.0.1:8000`

---

## Phase 1: Backend API Tests (via Swagger UI or curl)

Open **http://127.0.0.1:8000/docs** in your browser for interactive testing.

---

### 1.1 Health Check

```bash
curl http://127.0.0.1:8000/health
```

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | `GET /health` | `200 OK` with `{"status": "healthy"}` |

---

### 1.2 Product Management (CRUD + Business Rules)

#### ✅ Happy Path

```bash
# Create Product 1
curl -s -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Laptop","sku":"LPT-001","price":999.99,"quantity":50,"low_stock_threshold":5}'

# Create Product 2
curl -s -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Mouse","sku":"MOU-001","price":29.99,"quantity":100,"low_stock_threshold":10}'

# Create Product 3 (low stock — only 3 units)
curl -s -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Keyboard","sku":"KEY-001","price":79.99,"quantity":3,"low_stock_threshold":5}'
```

| # | Test | Command | Expected |
|---|------|---------|----------|
| 2 | Create product | `POST /products` with valid data | `201 Created`, product returned with `id` |
| 3 | List all products | `GET /products` | `200 OK`, array of 3 products |
| 4 | Get single product | `GET /products/1` | `200 OK`, Laptop details |
| 5 | Update product | `PUT /products/1` with `{"name":"Gaming Laptop","price":1299.99}` | `200 OK`, updated fields reflected |
| 6 | Delete product | `DELETE /products/2` (Mouse) | `204 No Content` |
| 7 | Verify deletion | `GET /products/2` | `404 Not Found` |

#### ❌ Error Scenarios (Business Rules R1, R3, R8, R9)

```bash
# R1: Duplicate SKU
curl -s -w "\nHTTP %{http_code}" -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Another Laptop","sku":"LPT-001","price":500,"quantity":10}'

# R3: Negative quantity
curl -s -w "\nHTTP %{http_code}" -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Tablet","sku":"TAB-001","price":299.99,"quantity":-5}'

# R8: Missing required field (no name)
curl -s -w "\nHTTP %{http_code}" -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"sku":"X-001","price":10,"quantity":5}'

# R8: Invalid price (zero)
curl -s -w "\nHTTP %{http_code}" -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Free Item","sku":"FRE-001","price":0,"quantity":5}'

# R9: Get non-existent product
curl -s -w "\nHTTP %{http_code}" http://127.0.0.1:8000/products/9999
```

| # | Test | Expected |
|---|------|----------|
| 8 | Duplicate SKU | `409 Conflict` — "SKU already exists" |
| 9 | Negative quantity | `422 Unprocessable Entity` — validation error |
| 10 | Missing required field | `422 Unprocessable Entity` — field required |
| 11 | Zero price | `422 Unprocessable Entity` — must be > 0 |
| 12 | Non-existent product | `404 Not Found` |

---

### 1.3 Customer Management (CRUD + Business Rules)

#### ✅ Happy Path

```bash
# Create Customer 1
curl -s -X POST http://127.0.0.1:8000/customers \
  -H "Content-Type: application/json" \
  -d '{"full_name":"John Doe","email":"john@example.com","phone":"555-0101"}'

# Create Customer 2
curl -s -X POST http://127.0.0.1:8000/customers \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Jane Smith","email":"jane@example.com","phone":"555-0102"}'
```

| # | Test | Command | Expected |
|---|------|---------|----------|
| 13 | Create customer | `POST /customers` with valid data | `201 Created` |
| 14 | List customers | `GET /customers` | `200 OK`, array of 2 customers |
| 15 | Get single customer | `GET /customers/1` | `200 OK`, John Doe details |
| 16 | Delete customer (no orders) | `DELETE /customers/2` | `204 No Content` |

#### ❌ Error Scenarios (Business Rules R2, R8, R9)

```bash
# R2: Duplicate email
curl -s -w "\nHTTP %{http_code}" -X POST http://127.0.0.1:8000/customers \
  -H "Content-Type: application/json" \
  -d '{"full_name":"John Clone","email":"john@example.com","phone":"555-9999"}'

# R8: Invalid email format
curl -s -w "\nHTTP %{http_code}" -X POST http://127.0.0.1:8000/customers \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Bad Email","email":"not-an-email","phone":"555-0000"}'

# R8: Missing name
curl -s -w "\nHTTP %{http_code}" -X POST http://127.0.0.1:8000/customers \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com"}'

# R9: Non-existent customer
curl -s -w "\nHTTP %{http_code}" http://127.0.0.1:8000/customers/9999
```

| # | Test | Expected |
|---|------|----------|
| 17 | Duplicate email | `409 Conflict` — "Email already exists" |
| 18 | Invalid email format | `422 Unprocessable Entity` |
| 19 | Missing name | `422 Unprocessable Entity` |
| 20 | Non-existent customer | `404 Not Found` |

---

### 1.4 Order Management (The Critical Path)

> [!IMPORTANT]
> Before running these, re-create test data if you deleted products/customers above. You need at least 1 product and 1 customer.

#### ✅ Happy Path — Create Order + Stock Reduction (R5, R6)

```bash
# First, note current stock of product 1
curl -s http://127.0.0.1:8000/products/1 | python3 -m json.tool | grep quantity

# Create an order for 2 units of product 1
curl -s -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id":1,"items":[{"product_id":1,"quantity":2}]}'

# Check stock AFTER order — should be reduced by 2
curl -s http://127.0.0.1:8000/products/1 | python3 -m json.tool | grep quantity
```

| # | Test | Expected |
|---|------|----------|
| 21 | Create order | `201 Created`, response includes `total_amount` calculated by backend |
| 22 | **R5**: Stock reduced | Product quantity decreased by ordered amount |
| 23 | **R6**: Total auto-calculated | `total_amount` = unit_price × quantity (e.g., `999.99 × 2 = 1999.98`) |
| 24 | List orders | `GET /orders` → `200 OK`, array with the new order |
| 25 | Get order detail | `GET /orders/1` → `200 OK`, includes items array with `unit_price` |

#### ✅ Multi-Item Order

```bash
# Re-create Mouse product if deleted
curl -s -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Mouse","sku":"MOU-002","price":29.99,"quantity":100,"low_stock_threshold":10}'

# Create multi-item order
curl -s -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id":1,"items":[{"product_id":1,"quantity":1},{"product_id":3,"quantity":2}]}'
```

| # | Test | Expected |
|---|------|----------|
| 26 | Multi-item order | `201 Created`, total = (price1 × 1) + (price3 × 2) |
| 27 | Both products' stock reduced | Check each product individually |

#### ✅ Delete Order — Stock Restoration (R7)

```bash
# Note stock BEFORE delete
curl -s http://127.0.0.1:8000/products/1 | python3 -m json.tool | grep quantity

# Delete the order
curl -s -X DELETE http://127.0.0.1:8000/orders/1

# Check stock AFTER delete — should be restored
curl -s http://127.0.0.1:8000/products/1 | python3 -m json.tool | grep quantity
```

| # | Test | Expected |
|---|------|----------|
| 28 | Delete order | `204 No Content` |
| 29 | **R7**: Stock restored | Product quantities go back up by the ordered amounts |

#### ❌ Error Scenarios (R4, R8, R9)

```bash
# R4: Order more than available stock
curl -s -w "\nHTTP %{http_code}" -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id":1,"items":[{"product_id":3,"quantity":99999}]}'

# R9: Order with non-existent customer
curl -s -w "\nHTTP %{http_code}" -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id":9999,"items":[{"product_id":1,"quantity":1}]}'

# R9: Order with non-existent product
curl -s -w "\nHTTP %{http_code}" -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id":1,"items":[{"product_id":9999,"quantity":1}]}'

# R8: Order with zero quantity
curl -s -w "\nHTTP %{http_code}" -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id":1,"items":[{"product_id":1,"quantity":0}]}'

# R8: Order with empty items list
curl -s -w "\nHTTP %{http_code}" -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id":1,"items":[]}'
```

| # | Test | Expected |
|---|------|----------|
| 30 | **R4**: Insufficient stock | `400 Bad Request` — "Insufficient stock" |
| 31 | Non-existent customer | `404 Not Found` |
| 32 | Non-existent product | `404 Not Found` |
| 33 | Zero quantity item | `422 Unprocessable Entity` |
| 34 | Empty items array | `422 Unprocessable Entity` |

---

### 1.5 Dashboard

```bash
curl -s http://127.0.0.1:8000/dashboard/summary | python3 -m json.tool
```

| # | Test | Expected |
|---|------|----------|
| 35 | Dashboard summary | `200 OK` with `total_products`, `total_customers`, `total_orders` counts |
| 36 | Low stock products | `low_stock_products` array includes Keyboard (qty 3, threshold 5) |

---

## Phase 2: Frontend UI Tests (Browser)

Open **http://127.0.0.1:3005** in your browser.

---

### 2.1 Navigation & Layout

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 37 | App loads | Open `http://127.0.0.1:3005` | Redirects to `/dashboard`, sidebar visible |
| 38 | Sidebar navigation | Click each nav link | URL changes, correct page loads |
| 39 | Active link highlighting | Click "Products" | Products link is highlighted in indigo |

---

### 2.2 Dashboard Page

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 40 | Stat cards render | Navigate to Dashboard | See 4 stat cards: Products, Customers, Orders, Low Stock |
| 41 | Counts are correct | Compare with API response | Numbers match `GET /dashboard/summary` |
| 42 | Low stock table | Scroll down | Table shows products where `quantity <= low_stock_threshold` |

---

### 2.3 Products Page

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 43 | Products list | Navigate to Products | See table with all products |
| 44 | Add product — happy path | Click "Add Product" → fill form → Save | Toast: "Product created successfully", table updates |
| 45 | Add product — validation | Click "Add Product" → leave name empty → Save | Red error text "Name is required" under field |
| 46 | Add product — duplicate SKU | Add a product with existing SKU | Toast: error message about SKU |
| 47 | Edit product | Click pencil icon → change name → Save | Toast: "Product updated", table reflects change |
| 48 | Delete product | Click trash icon → confirm | Toast: "Product deleted", row disappears |
| 49 | Stock badge color | Look at Stock column | Green badge if stock > threshold, Red badge if stock ≤ threshold |

---

### 2.4 Customers Page

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 50 | Customers list | Navigate to Customers | See table with all customers |
| 51 | Add customer — happy path | Click "Add Customer" → fill form → Save | Toast success, table updates |
| 52 | Add customer — validation | Leave email empty → Save | Red error under email field |
| 53 | Add customer — duplicate email | Use an existing email | Toast: error about duplicate email |
| 54 | Delete customer | Click trash → confirm | Toast success, row disappears |

---

### 2.5 Orders Page (Most Critical UI Flow)

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 55 | Orders list | Navigate to Orders | See table (may be empty initially) |
| 56 | Create order — select customer | Click "Create Order" → select customer from dropdown | Customer selected |
| 57 | Create order — add item | Select product from dropdown, set qty, click "Add" | Item appears in Order Summary below |
| 58 | Create order — preview total | Add multiple items | "Total (Preview)" updates correctly |
| 59 | Create order — remove item | Click X on an item row | Item removed, total recalculated |
| 60 | Create order — submit | Click "Submit Order" | Toast success, modal closes, table shows new order |
| 61 | **Verify stock reduced** | Go to Products page | Product quantities decreased by ordered amounts |
| 62 | Create order — insufficient stock | Try ordering more than available | Toast: "Insufficient stock" error |
| 63 | Create order — no customer selected | Don't select customer → Submit | Toast: "Please select a customer" |
| 64 | Create order — no items | Select customer but no items → Submit | Toast: "Please add at least one item" |
| 65 | View order detail | Click eye icon on an order | Modal shows order date, customer, items list, total amount |
| 66 | Delete order | Click trash icon → confirm | Toast success, order removed |
| 67 | **Verify stock restored** | Go to Products page | Product quantities restored after order deletion |

---

### 2.6 UI/UX Checks

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 68 | Responsive design | Resize browser to mobile width | Layout adapts (sidebar may collapse, table scrolls horizontally) |
| 69 | Modal overlay | Open any modal | Background darkened, modal centered |
| 70 | Modal close | Click X or Cancel | Modal closes cleanly |
| 71 | Loading states | Refresh any page | Brief "Loading..." text while data fetches |
| 72 | Empty states | Delete all products | "No products found. Add one to get started." message |
| 73 | Toast notifications | Perform any create/delete | Toast appears top-right, auto-dismisses |

---

## Phase 3: Docker & Infrastructure Checks

| # | Test | Command/Steps | Expected |
|---|------|---------------|----------|
| 74 | All 3 services running | `docker-compose ps` | `db`, `backend`, `frontend` all "Up" |
| 75 | DB health check | `docker-compose ps` shows "healthy" for db | PostgreSQL responding |
| 76 | Backend logs clean | `docker-compose logs backend --tail=20` | No crash errors, shows uvicorn startup |
| 77 | Frontend serves correctly | `curl -s http://127.0.0.1:3005` | Returns HTML with `<div id="root">` |
| 78 | Swagger docs accessible | Open `http://127.0.0.1:8000/docs` | Full Swagger UI with all endpoints |
| 79 | Data persists across restart | `docker-compose restart` → check data | Products/customers/orders still there |
| 80 | No hardcoded credentials | `grep -r "password" docker-compose.yml` | Only `${POSTGRES_PASSWORD:-postgres}` (env var, not hardcoded) |

---

## Quick Full Smoke Test Script (Copy-Paste Ready)

Run this entire block to do a rapid end-to-end verification:

```bash
BASE=http://127.0.0.1:8000

echo "=== 1. Health ==="
curl -s $BASE/health | python3 -m json.tool

echo "=== 2. Create Product ==="
curl -s -X POST $BASE/products -H "Content-Type: application/json" \
  -d '{"name":"Test Widget","sku":"TST-'$RANDOM'","price":49.99,"quantity":20,"low_stock_threshold":5}' | python3 -m json.tool

echo "=== 3. Create Customer ==="
curl -s -X POST $BASE/customers -H "Content-Type: application/json" \
  -d '{"full_name":"Test User","email":"test'$RANDOM'@example.com","phone":"555-TEST"}' | python3 -m json.tool

echo "=== 4. Get product ID and customer ID ==="
PROD_ID=$(curl -s $BASE/products | python3 -c "import sys,json; print(json.load(sys.stdin)[-1]['id'])")
CUST_ID=$(curl -s $BASE/customers | python3 -c "import sys,json; print(json.load(sys.stdin)[-1]['id'])")
echo "Product ID: $PROD_ID, Customer ID: $CUST_ID"

echo "=== 5. Stock BEFORE order ==="
curl -s $BASE/products/$PROD_ID | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Stock: {d[\"quantity\"]}')"

echo "=== 6. Create Order (3 units) ==="
ORDER_ID=$(curl -s -X POST $BASE/orders -H "Content-Type: application/json" \
  -d "{\"customer_id\":$CUST_ID,\"items\":[{\"product_id\":$PROD_ID,\"quantity\":3}]}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['id']); import sys; sys.stderr.write(f'Total: {d[\"total_amount\"]}\n')")
echo "Order ID: $ORDER_ID"

echo "=== 7. Stock AFTER order (should be 17) ==="
curl -s $BASE/products/$PROD_ID | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Stock: {d[\"quantity\"]}')"

echo "=== 8. Delete Order ==="
curl -s -o /dev/null -w "HTTP %{http_code}" -X DELETE $BASE/orders/$ORDER_ID
echo ""

echo "=== 9. Stock AFTER delete (should be 20 again) ==="
curl -s $BASE/products/$PROD_ID | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Stock: {d[\"quantity\"]}')"

echo "=== 10. Dashboard ==="
curl -s $BASE/dashboard/summary | python3 -m json.tool

echo "=== ✅ ALL CHECKS COMPLETE ==="
```

---

## Summary Scorecard

| Category | Tests | Business Rules Covered |
|----------|-------|----------------------|
| Products API | #2–#12 | R1 (unique SKU), R3 (no negative qty), R8, R9 |
| Customers API | #13–#20 | R2 (unique email), R8, R9 |
| Orders API | #21–#34 | R4 (stock check), R5 (auto-reduce), R6 (auto-total), R7 (restore on delete), R8, R9 |
| Dashboard API | #35–#36 | Low stock detection |
| Frontend UI | #37–#73 | All CRUD flows, form validation, toasts, responsive |
| Docker/Infra | #74–#80 | Containerization, persistence, no hardcoded creds |

> [!TIP]
> Run the **Quick Smoke Test Script** first for a fast pass, then walk through the **Frontend UI Tests** manually in the browser to verify the full user experience.
