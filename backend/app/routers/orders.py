from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Order, OrderItem, Product, Customer
from app.schemas import OrderCreate, OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    # Verify customer
    customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    total_amount = 0
    order_items_to_create = []

    # Verify stock and prepare items
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {item.product_id} not found")
        
        if product.quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Insufficient stock for product {product.name} (ID: {product.id}). Requested: {item.quantity}, Available: {product.quantity}"
            )

        # Reduce stock
        product.quantity -= item.quantity
        
        # Calculate amount
        unit_price = product.price
        total_amount += unit_price * item.quantity
        
        order_items_to_create.append(OrderItem(
            product_id=product.id,
            quantity=item.quantity,
            unit_price=unit_price
        ))

    # Create order
    db_order = Order(
        customer_id=order.customer_id,
        total_amount=total_amount
    )
    db.add(db_order)
    db.flush() # get order id

    for item in order_items_to_create:
        item.order_id = db_order.id
        db.add(item)

    try:
        db.commit()
        db.refresh(db_order)
        return db_order
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("", response_model=List[OrderResponse])
def get_orders(db: Session = Depends(get_db)):
    return db.query(Order).order_by(Order.id.desc()).all()

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Restore stock
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
        if product:
            product.quantity += item.quantity

    db.delete(order)
    db.commit()
    return None
