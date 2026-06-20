# Inventory & Order Management System

A production-ready full-stack Inventory and Order Management System, built as a technical assessment.

## Stack
- **Backend:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, PostgreSQL
- **Frontend:** React (JavaScript), Vite, Tailwind CSS, React Query
- **Infrastructure:** Docker, Docker Compose

## Prerequisites
- Docker and Docker Compose
- Git

## Quick Start (Local Setup)

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd inventory-management
   ```

2. Setup environment variables:
   ```bash
   cp .env.example .env
   ```

3. Run the application:
   ```bash
   docker-compose up --build
   ```

4. Access the services:
   - **Frontend UI:** `http://localhost:3000`
   - **Backend API Docs (Swagger):** `http://localhost:8000/docs`

## Environment Variables

| Variable | Description | Default (`.env.example`) |
|----------|-------------|---------|
| `POSTGRES_DB` | Database name | `inventory` |
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `postgres` |
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql://postgres:postgres@db:5432/inventory` |
| `CORS_ORIGINS` | Allowed origins for backend CORS | `http://localhost:3000` |
| `VITE_API_URL` | Backend API URL for frontend (build-time) | `http://localhost:8000` |

## API Endpoints

### Products
- `GET /products` - List all products
- `POST /products` - Create a product
- `GET /products/{id}` - Get product details
- `PUT /products/{id}` - Update a product
- `DELETE /products/{id}` - Delete a product

### Customers
- `GET /customers` - List all customers
- `POST /customers` - Create a customer
- `GET /customers/{id}` - Get customer details
- `DELETE /customers/{id}` - Delete a customer

### Orders
- `GET /orders` - List all orders
- `POST /orders` - Create an order (verifies stock, auto-computes total, updates inventory)
- `GET /orders/{id}` - Get order details
- `DELETE /orders/{id}` - Delete an order (restores inventory)

### Dashboard
- `GET /dashboard/summary` - Gets aggregate metrics (totals and low stock items)

### Health
- `GET /health` - Liveness probe

## Deployment Guide (Manual Steps)

To deploy this application to production, follow these steps:

### 1. Deploy PostgreSQL Database
Create a managed PostgreSQL database (e.g., Render, Supabase, Neon) and get the connection string.

### 2. Deploy Backend (e.g., Render)
1. Create a new Web Service on Render.
2. Select "Deploy an existing image from a registry" or use the GitHub repository and specify Docker as the runtime.
3. Set the following environment variables:
   - `DATABASE_URL`: Your production DB connection string
   - `CORS_ORIGINS`: Your planned frontend URL (e.g., `https://my-frontend.vercel.app`)
4. Deploy and verify the `/health` endpoint is responding.

### 3. Deploy Frontend (e.g., Vercel)
1. Import the repository into Vercel.
2. Set the "Root Directory" to `frontend`.
3. Set the following Environment Variable:
   - `VITE_API_URL`: The URL of your deployed backend (e.g., `https://my-backend.onrender.com`)
4. Deploy.

### 4. Push Backend Image to Docker Hub
1. Build the image: `docker build -t yourusername/inventory-backend ./backend`
2. Push to Docker Hub: `docker push yourusername/inventory-backend`
