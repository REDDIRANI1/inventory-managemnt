import decimal
from app.database import SessionLocal, engine, Base
from app.models import Product, Customer, Order, OrderItem

def seed_db():
    db = SessionLocal()
    # Check if database is already seeded
    if db.query(Product).first() is not None:
        print("Database already has data. Skipping seed.")
        db.close()
        return

    print("Seeding database with sample data...")
    # Add products
    products = [
        Product(name="Ergonomic Chair", sku="CHR-001", price=decimal.Decimal("299.99"), quantity=45, low_stock_threshold=5),
        Product(name="Mechanical Keyboard", sku="KEY-001", price=decimal.Decimal("129.50"), quantity=80, low_stock_threshold=10),
        Product(name="UltraWide Monitor", sku="MON-001", price=decimal.Decimal("499.99"), quantity=4, low_stock_threshold=5), # Low stock
        Product(name="Wireless Mouse", sku="MS-001", price=decimal.Decimal("49.99"), quantity=150, low_stock_threshold=15),
        Product(name="USB-C Hub", sku="HUB-001", price=decimal.Decimal("79.99"), quantity=2, low_stock_threshold=5) # Low stock
    ]
    for p in products:
        db.add(p)
    db.commit()

    # Add customers
    customers = [
        Customer(full_name="Alice Johnson", email="alice@example.com", phone="+1-555-0199"),
        Customer(full_name="Bob Smith", email="bob@example.com", phone="+1-555-0142"),
        Customer(full_name="Charlie Brown", email="charlie@example.com", phone="+1-555-0177")
    ]
    for c in customers:
        db.add(c)
    db.commit()

    # Add some sample orders
    db_products = {p.sku: p for p in db.query(Product).all()}
    db_customers = {c.email: c for c in db.query(Customer).all()}

    # Alice's order
    order1 = Order(customer_id=db_customers["alice@example.com"].id, total_amount=decimal.Decimal("429.49"))
    db.add(order1)
    db.commit()
    
    item1 = OrderItem(order_id=order1.id, product_id=db_products["CHR-001"].id, quantity=1, unit_price=db_products["CHR-001"].price)
    item2 = OrderItem(order_id=order1.id, product_id=db_products["KEY-001"].id, quantity=1, unit_price=db_products["KEY-001"].price)
    db.add_all([item1, item2])
    
    # Bob's order
    order2 = Order(customer_id=db_customers["bob@example.com"].id, total_amount=decimal.Decimal("999.98"))
    db.add(order2)
    db.commit()
    
    item3 = OrderItem(order_id=order2.id, product_id=db_products["MON-001"].id, quantity=2, unit_price=db_products["MON-001"].price)
    db.add(item3)

    # Charlie's order
    order3 = Order(customer_id=db_customers["charlie@example.com"].id, total_amount=decimal.Decimal("229.48"))
    db.add(order3)
    db.commit()
    
    item4 = OrderItem(order_id=order3.id, product_id=db_products["KEY-001"].id, quantity=1, unit_price=db_products["KEY-001"].price)
    item5 = OrderItem(order_id=order3.id, product_id=db_products["MS-001"].id, quantity=2, unit_price=db_products["MS-001"].price)
    db.add_all([item4, item5])

    db.commit()
    print("Database seeding completed.")
    db.close()

if __name__ == "__main__":
    seed_db()
