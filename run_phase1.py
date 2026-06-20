import subprocess
import json
import re

BASE_URL = "http://127.0.0.1:8000"

results = {}

def run_curl(name, cmd_args, expected_status=None, check_fn=None):
    # We append -w "\nHTTP %{http_code}" to the curl command to get the status code
    # If the user's command already has it or uses custom args, we handle it carefully.
    
    # Reconstruct the command
    full_cmd = ["curl", "-s"]
    # Check if we should add status code writing
    has_write_out = False
    for arg in cmd_args:
        if "-w" in arg:
            has_write_out = True
    
    if not has_write_out:
        full_cmd.extend(["-w", "\\nHTTP %{http_code}"])
    
    full_cmd.extend(cmd_args)
    
    print(f"Running: {' '.join(full_cmd)}")
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    
    output = res.stdout.strip()
    
    # Parse status code and body
    status_code = None
    body = output
    
    # Try to extract HTTP code at the end
    lines = output.split('\n')
    if lines:
        last_line = lines[-1].strip()
        if last_line.startswith("HTTP "):
            status_code = int(last_line.split(" ")[1])
            body = "\n".join(lines[:-1]).strip()
        elif re.match(r"^\d+$", last_line):
            status_code = int(last_line)
            body = "\n".join(lines[:-1]).strip()
            
    # Fallback if no status code was extracted
    if status_code is None:
        # Just run with -o /dev/null -w "%{http_code}" to get code
        code_cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}"]
        # remove status writing args if any
        clean_args = []
        skip_next = False
        for arg in cmd_args:
            if skip_next:
                skip_next = False
                continue
            if arg == "-w":
                skip_next = True
                continue
            clean_args.append(arg)
        code_cmd.extend(clean_args)
        code_res = subprocess.run(code_cmd, capture_output=True, text=True)
        try:
            status_code = int(code_res.stdout.strip())
        except:
            status_code = 0
            
    print(f"Status: {status_code}")
    print(f"Body: {body}\n")
    
    passed = True
    if expected_status is not None:
        if status_code != expected_status:
            passed = False
            
    if check_fn is not None:
        if not check_fn(status_code, body):
            passed = False
            
    status_str = "PASS" if passed else "FAIL"
    results[name] = {
        "status_code": status_code,
        "body": body,
        "status": status_str
    }
    return passed, status_code, body

print("=== STARTING PHASE 1: API TESTS ===")

# Test 1: Health check
run_curl("1. Health check", ["http://127.0.0.1:8000/health"], expected_status=200)

# Create products for happy path
# We need to run the POST commands before we run tests 2-7
run_curl("Create Product 1", [
    "-X", "POST", f"{BASE_URL}/products",
    "-H", "Content-Type: application/json",
    "-d", '{"name":"Laptop","sku":"LPT-001","price":999.99,"quantity":50,"low_stock_threshold":5}'
], expected_status=201)

run_curl("Create Product 2", [
    "-X", "POST", f"{BASE_URL}/products",
    "-H", "Content-Type: application/json",
    "-d", '{"name":"Mouse","sku":"MOU-001","price":29.99,"quantity":100,"low_stock_threshold":10}'
], expected_status=201)

run_curl("Create Product 3", [
    "-X", "POST", f"{BASE_URL}/products",
    "-H", "Content-Type: application/json",
    "-d", '{"name":"Keyboard","sku":"KEY-001","price":79.99,"quantity":3,"low_stock_threshold":5}'
], expected_status=201)

# Now, map to the official test cases in the guide:
# Test 2: Create product (we already created it, but let's record it or map "Create Product 1" to it)
results["2. Create product"] = results["Create Product 1"]

# Test 3: List all products
run_curl("3. List all products", [f"{BASE_URL}/products"], expected_status=200,
         check_fn=lambda s, b: len(json.loads(b)) >= 3)

# Test 4: Get single product
run_curl("4. Get single product", [f"{BASE_URL}/products/1"], expected_status=200,
         check_fn=lambda s, b: json.loads(b).get("sku") == "LPT-001")

# Test 5: Update product
run_curl("5. Update product", [
    "-X", "PUT", f"{BASE_URL}/products/1",
    "-H", "Content-Type: application/json",
    "-d", '{"name":"Gaming Laptop","price":1299.99}'
], expected_status=200, check_fn=lambda s, b: json.loads(b).get("name") == "Gaming Laptop" and float(json.loads(b).get("price")) == 1299.99)

# Test 6: Delete product (Mouse, which is product 2)
run_curl("6. Delete product", ["-X", "DELETE", f"{BASE_URL}/products/2"], expected_status=204)

# Test 7: Verify deletion
run_curl("7. Verify deletion", [f"{BASE_URL}/products/2"], expected_status=404)

# Test 8: Duplicate SKU
run_curl("8. Duplicate SKU", [
    "-w", "\\nHTTP %{http_code}", "-X", "POST", f"{BASE_URL}/products",
    "-H", "Content-Type: application/json",
    "-d", '{"name":"Another Laptop","sku":"LPT-001","price":500,"quantity":10}'
], expected_status=409)

# Test 9: Negative quantity
run_curl("9. Negative quantity", [
    "-w", "\\nHTTP %{http_code}", "-X", "POST", f"{BASE_URL}/products",
    "-H", "Content-Type: application/json",
    "-d", '{"name":"Tablet","sku":"TAB-001","price":299.99,"quantity":-5}'
], expected_status=422)

# Test 10: Missing required field
run_curl("10. Missing required field", [
    "-w", "\\nHTTP %{http_code}", "-X", "POST", f"{BASE_URL}/products",
    "-H", "Content-Type: application/json",
    "-d", '{"sku":"X-001","price":10,"quantity":5}'
], expected_status=422)

# Test 11: Zero price
run_curl("11. Zero price", [
    "-w", "\\nHTTP %{http_code}", "-X", "POST", f"{BASE_URL}/products",
    "-H", "Content-Type: application/json",
    "-d", '{"name":"Free Item","sku":"FRE-001","price":0,"quantity":5}'
], expected_status=422)

# Test 12: Non-existent product
run_curl("12. Non-existent product", ["-w", "\\nHTTP %{http_code}", f"{BASE_URL}/products/9999"], expected_status=404)


# --- 1.3 Customer Management ---
# Create Customer 1
run_curl("Create Customer 1", [
    "-X", "POST", f"{BASE_URL}/customers",
    "-H", "Content-Type: application/json",
    "-d", '{"full_name":"John Doe","email":"john@example.com","phone":"555-0101"}'
], expected_status=201)

# Create Customer 2
run_curl("Create Customer 2", [
    "-X", "POST", f"{BASE_URL}/customers",
    "-H", "Content-Type: application/json",
    "-d", '{"full_name":"Jane Smith","email":"jane@example.com","phone":"555-0102"}'
], expected_status=201)

results["13. Create customer"] = results["Create Customer 1"]

# Test 14: List customers
run_curl("14. List customers", [f"{BASE_URL}/customers"], expected_status=200,
         check_fn=lambda s, b: len(json.loads(b)) >= 2)

# Test 15: Get single customer
run_curl("15. Get single customer", [f"{BASE_URL}/customers/1"], expected_status=200,
         check_fn=lambda s, b: json.loads(b).get("full_name") == "John Doe")

# Test 16: Delete customer (no orders)
run_curl("16. Delete customer (no orders)", ["-X", "DELETE", f"{BASE_URL}/customers/2"], expected_status=204)

# Test 17: Duplicate email
run_curl("17. Duplicate email", [
    "-w", "\\nHTTP %{http_code}", "-X", "POST", f"{BASE_URL}/customers",
    "-H", "Content-Type: application/json",
    "-d", '{"full_name":"John Clone","email":"john@example.com","phone":"555-9999"}'
], expected_status=409)

# Test 18: Invalid email format
run_curl("18. Invalid email format", [
    "-w", "\\nHTTP %{http_code}", "-X", "POST", f"{BASE_URL}/customers",
    "-H", "Content-Type: application/json",
    "-d", '{"full_name":"Bad Email","email":"not-an-email","phone":"555-0000"}'
], expected_status=422)

# Test 19: Missing name
run_curl("19. Missing name", [
    "-w", "\\nHTTP %{http_code}", "-X", "POST", f"{BASE_URL}/customers",
    "-H", "Content-Type: application/json",
    "-d", '{"email":"test@test.com"}'
], expected_status=422)

# Test 20: Non-existent customer
run_curl("20. Non-existent customer", ["-w", "\\nHTTP %{http_code}", f"{BASE_URL}/customers/9999"], expected_status=404)


# --- 1.4 Order Management ---
# Before running these, re-create test data if deleted products/customers above. 
# We need at least 1 product and 1 customer. Product 1 (Laptop) exists, Product 3 (Keyboard) exists. Customer 1 (John Doe) exists.
# We also need to check stock BEFORE order
_, _, prod1_before = run_curl("Stock BEFORE Order", [f"{BASE_URL}/products/1"])
qty_before = json.loads(prod1_before).get("quantity")

# Test 21: Create order
run_curl("21. Create order", [
    "-X", "POST", f"{BASE_URL}/orders",
    "-H", "Content-Type: application/json",
    "-d", '{"customer_id":1,"items":[{"product_id":1,"quantity":2}]}'
], expected_status=201)

# Test 22: Stock reduced
_, _, prod1_after = run_curl("Stock AFTER Order Check", [f"{BASE_URL}/products/1"])
qty_after = json.loads(prod1_after).get("quantity")
stock_reduced_passed = (qty_before - qty_after) == 2
results["22. Stock reduced"] = {
    "status_code": 200,
    "body": f"Before: {qty_before}, After: {qty_after}",
    "status": "PASS" if stock_reduced_passed else "FAIL"
}

# Test 23: Total auto-calculated
order1_body = json.loads(results["21. Create order"]["body"])
expected_total = 1299.99 * 2 # Laptop price was updated to 1299.99 in Test 5
total_calculated_passed = abs(float(order1_body.get("total_amount")) - expected_total) < 0.01
results["23. Total auto-calculated"] = {
    "status_code": 201,
    "body": f"Total Amount: {order1_body.get('total_amount')}, Expected: {expected_total}",
    "status": "PASS" if total_calculated_passed else "FAIL"
}

# Test 24: List orders
run_curl("24. List orders", [f"{BASE_URL}/orders"], expected_status=200,
         check_fn=lambda s, b: len(json.loads(b)) >= 1)

# Test 25: Get order detail
run_curl("25. Get order detail", [f"{BASE_URL}/orders/1"], expected_status=200,
         check_fn=lambda s, b: json.loads(b).get("customer_id") == 1)

# Re-create Mouse product if deleted
# Note: Mouse had id=2, but was deleted. Re-creating will likely give it id=4. Let's make sure.
_, _, mouse_res = run_curl("Re-create Mouse", [
    "-X", "POST", f"{BASE_URL}/products",
    "-H", "Content-Type: application/json",
    "-d", '{"name":"Mouse","sku":"MOU-002","price":29.99,"quantity":100,"low_stock_threshold":10}'
], expected_status=201)
mouse_id = json.loads(mouse_res).get("id")

# Get Keyboard (product 3) before quantity
_, _, key_before = run_curl("Keyboard Stock Before", [f"{BASE_URL}/products/3"])
key_qty_before = json.loads(key_before).get("quantity")
_, _, prod1_before_multi = run_curl("Product 1 Stock Before Multi", [f"{BASE_URL}/products/1"])
prod1_qty_before_multi = json.loads(prod1_before_multi).get("quantity")

# Test 26: Multi-item order
# Keyboard is product 3. Let's create an order for Product 1 (qty 1) and Keyboard (qty 2)
# Expected total: (1299.99 * 1) + (79.99 * 2) = 1299.99 + 159.98 = 1459.97
run_curl("26. Multi-item order", [
    "-X", "POST", f"{BASE_URL}/orders",
    "-H", "Content-Type: application/json",
    "-d", '{"customer_id":1,"items":[{"product_id":1,"quantity":1},{"product_id":3,"quantity":2}]}'
], expected_status=201)

# Test 27: Both products' stock reduced
_, _, key_after = run_curl("Keyboard Stock After Check", [f"{BASE_URL}/products/3"])
key_qty_after = json.loads(key_after).get("quantity")
_, _, prod1_after_multi = run_curl("Product 1 Stock After Multi Check", [f"{BASE_URL}/products/1"])
prod1_qty_after_multi = json.loads(prod1_after_multi).get("quantity")
multi_stock_passed = (prod1_qty_before_multi - prod1_qty_after_multi == 1) and (key_qty_before - key_qty_after == 2)
results["27. Both products' stock reduced"] = {
    "status_code": 200,
    "body": f"P1 Before: {prod1_qty_before_multi}, After: {prod1_qty_after_multi}; P3 Before: {key_qty_before}, After: {key_qty_after}",
    "status": "PASS" if multi_stock_passed else "FAIL"
}

# Delete Order 1 - Stock Restoration
_, _, prod1_before_delete = run_curl("Product 1 Stock Before Delete", [f"{BASE_URL}/products/1"])
prod1_qty_before_delete = json.loads(prod1_before_delete).get("quantity")

# Test 28: Delete order
run_curl("28. Delete order", ["-X", "DELETE", f"{BASE_URL}/orders/1"], expected_status=204)

# Test 29: Stock restored
_, _, prod1_after_delete = run_curl("Product 1 Stock After Delete Check", [f"{BASE_URL}/products/1"])
prod1_qty_after_delete = json.loads(prod1_after_delete).get("quantity")
stock_restored_passed = (prod1_qty_after_delete - prod1_qty_before_delete) == 2 # Order 1 had 2 Laptops
results["29. Stock restored"] = {
    "status_code": 200,
    "body": f"Before Delete: {prod1_qty_before_delete}, After Delete: {prod1_qty_after_delete}",
    "status": "PASS" if stock_restored_passed else "FAIL"
}

# Test 30: Insufficient stock
run_curl("30. Insufficient stock", [
    "-w", "\\nHTTP %{http_code}", "-X", "POST", f"{BASE_URL}/orders",
    "-H", "Content-Type: application/json",
    "-d", '{"customer_id":1,"items":[{"product_id":3,"quantity":99999}]}'
], expected_status=400)

# Test 31: Non-existent customer
run_curl("31. Non-existent customer", [
    "-w", "\\nHTTP %{http_code}", "-X", "POST", f"{BASE_URL}/orders",
    "-H", "Content-Type: application/json",
    "-d", '{"customer_id":9999,"items":[{"product_id":1,"quantity":1}]}'
], expected_status=404)

# Test 32: Non-existent product
run_curl("32. Non-existent product", [
    "-w", "\\nHTTP %{http_code}", "-X", "POST", f"{BASE_URL}/orders",
    "-H", "Content-Type: application/json",
    "-d", '{"customer_id":1,"items":[{"product_id":9999,"quantity":1}]}'
], expected_status=404)

# Test 33: Zero quantity item
run_curl("33. Zero quantity item", [
    "-w", "\\nHTTP %{http_code}", "-X", "POST", f"{BASE_URL}/orders",
    "-H", "Content-Type: application/json",
    "-d", '{"customer_id":1,"items":[{"product_id":1,"quantity":0}]}'
], expected_status=422)

# Test 34: Empty items array
run_curl("34. Empty items array", [
    "-w", "\\nHTTP %{http_code}", "-X", "POST", f"{BASE_URL}/orders",
    "-H", "Content-Type: application/json",
    "-d", '{"customer_id":1,"items":[]}'
], expected_status=422)


# --- 1.5 Dashboard ---
# Test 35: Dashboard summary
run_curl("35. Dashboard summary", [f"{BASE_URL}/dashboard/summary"], expected_status=200)

# Test 36: Low stock products
run_curl("36. Low stock products", [f"{BASE_URL}/dashboard/summary"], expected_status=200,
         check_fn=lambda s, b: any(item.get("sku") == "KEY-001" for item in json.loads(b).get("low_stock_products", [])))


# Save outputs to JSON to load them in the reporting step
with open("/Users/salauddin/Projects/workspace/assessments/inventory-management/phase1_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("=== PHASE 1 COMPLETE ===")
