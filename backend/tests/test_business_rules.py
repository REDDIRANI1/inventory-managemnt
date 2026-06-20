import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_rule1_unique_product_sku():
    product_data = {"name": "Test Product", "sku": "SKU123", "price": 10.0, "quantity": 100}
    response1 = client.post("/products", json=product_data)
    assert response1.status_code == 201

    response2 = client.post("/products", json=product_data)
    assert response2.status_code == 409
    assert response2.json()["detail"] == "Product SKU already exists"

def test_rule2_unique_customer_email():
    customer_data = {"full_name": "Test Customer", "email": "test@example.com"}
    response1 = client.post("/customers", json=customer_data)
    assert response1.status_code == 201

    response2 = client.post("/customers", json=customer_data)
    assert response2.status_code == 409
    assert response2.json()["detail"] == "Customer email already exists"

def test_rule3_quantity_never_negative():
    product_data = {"name": "Test", "sku": "SKU-NEG", "price": 10.0, "quantity": -5}
    response = client.post("/products", json=product_data)
    assert response.status_code == 422 # Pydantic validation fails

def test_rule4_insufficient_stock_blocks_order():
    # Create customer
    c_res = client.post("/customers", json={"full_name": "C", "email": "c@example.com"})
    c_id = c_res.json()["id"]

    # Create product with 5 stock
    p_res = client.post("/products", json={"name": "P", "sku": "SKU1", "price": 10.0, "quantity": 5})
    p_id = p_res.json()["id"]

    # Order 10 (should fail)
    order_data = {
        "customer_id": c_id,
        "items": [{"product_id": p_id, "quantity": 10}]
    }
    o_res = client.post("/orders", json=order_data)
    assert o_res.status_code == 400
    assert "Insufficient stock" in o_res.json()["detail"]

    # Verify stock is still 5
    p_check = client.get(f"/products/{p_id}")
    assert p_check.json()["quantity"] == 5

def test_rule5_6_auto_stock_reduction_and_total_calculation():
    # Create customer
    c_res = client.post("/customers", json={"full_name": "C", "email": "c@example.com"})
    c_id = c_res.json()["id"]

    # Create product with 10 stock, price 15.0
    p_res = client.post("/products", json={"name": "P", "sku": "SKU1", "price": 15.0, "quantity": 10})
    p_id = p_res.json()["id"]

    # Create order of 2 items
    order_data = {
        "customer_id": c_id,
        "items": [{"product_id": p_id, "quantity": 2}]
    }
    o_res = client.post("/orders", json=order_data)
    assert o_res.status_code == 201
    
    # Rule 6: Total calculation
    # In SQLite, decimals might be returned as strings depending on sqlite dialect/sqlalchemy,
    # FastAPI test client parses them, but float comparison or string comparison might be needed.
    res_total = float(o_res.json()["total_amount"])
    assert res_total == 30.0

    # Rule 5: Stock reduction
    p_check = client.get(f"/products/{p_id}")
    assert p_check.json()["quantity"] == 8

def test_rule7_order_delete_restores_stock():
    # Create customer and product
    c_res = client.post("/customers", json={"full_name": "C", "email": "c@example.com"})
    c_id = c_res.json()["id"]

    p_res = client.post("/products", json={"name": "P", "sku": "SKU1", "price": 10.0, "quantity": 10})
    p_id = p_res.json()["id"]

    # Create order of 3 items
    o_res = client.post("/orders", json={"customer_id": c_id, "items": [{"product_id": p_id, "quantity": 3}]})
    o_id = o_res.json()["id"]

    # Stock should be 7
    assert client.get(f"/products/{p_id}").json()["quantity"] == 7

    # Delete order
    del_res = client.delete(f"/orders/{o_id}")
    assert del_res.status_code == 204

    # Stock should be restored to 10
    assert client.get(f"/products/{p_id}").json()["quantity"] == 10
