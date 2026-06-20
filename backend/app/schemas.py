from pydantic import BaseModel, ConfigDict, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

# --- Products ---
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1)
    sku: str = Field(..., min_length=1)
    price: Decimal = Field(..., gt=0)
    quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=10, ge=0)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    sku: Optional[str] = Field(None, min_length=1)
    price: Optional[Decimal] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# --- Customers ---
class CustomerBase(BaseModel):
    full_name: str = Field(..., min_length=1)
    email: EmailStr
    phone: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Orders ---
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int
    unit_price: Decimal
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)

class OrderBase(BaseModel):
    customer_id: int

class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(..., min_length=1)

class OrderResponse(OrderBase):
    id: int
    total_amount: Decimal
    created_at: datetime
    items: List[OrderItemResponse] = []
    customer: Optional[CustomerResponse] = None

    model_config = ConfigDict(from_attributes=True)

# --- Dashboard ---
class ProductLowStockResponse(BaseModel):
    id: int
    name: str
    sku: str
    quantity: int
    low_stock_threshold: int

    model_config = ConfigDict(from_attributes=True)

class DashboardSummaryResponse(BaseModel):
    total_products: int
    total_customers: int
    total_orders: int
    low_stock_products: List[ProductLowStockResponse]
