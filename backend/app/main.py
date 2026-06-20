from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.config import settings
from app.routers import products, customers, orders, dashboard

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Inventory & Order Management System")

# Configure CORS
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(dashboard.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
