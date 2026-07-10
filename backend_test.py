#!/usr/bin/env python3
"""
Comprehensive Backend API Test Suite for 3D Druck Service
Tests all endpoints according to the review request specifications
"""

import requests
import json
import base64
import math

# Base URL from environment
BASE_URL = "https://order-prints-6.preview.emergentagent.com/api"

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin123!"

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_pass(test_name):
    print(f"✅ PASS: {test_name}")
    test_results["passed"].append(test_name)

def log_fail(test_name, reason):
    print(f"❌ FAIL: {test_name}")
    print(f"   Reason: {reason}")
    test_results["failed"].append(f"{test_name}: {reason}")

def log_warning(test_name, reason):
    print(f"⚠️  WARNING: {test_name}")
    print(f"   Reason: {reason}")
    test_results["warnings"].append(f"{test_name}: {reason}")

def calculate_expected_price(size=100, quantity=1, priority="Normal", grams=25, hours=2):
    """Calculate expected price according to the formula"""
    qty = max(1, quantity)
    s = size / 100
    
    # Material scales with volume (^2.2), time scales linearly
    total_grams = grams * (s ** 2.2) * qty
    total_hours = hours * s * qty
    
    material = total_grams * 0.03
    time = total_hours * 2.0
    wear = 1.5 * qty
    subtotal = material + time + wear
    total = subtotal * 1.20  # 20% profit
    
    if priority == "Eilig":
        total *= 1.25  # 25% rush fee
    
    return round(total, 2)

print("=" * 80)
print("3D DRUCK SERVICE - BACKEND API TEST SUITE")
print("=" * 80)
print(f"Base URL: {BASE_URL}")
print(f"Admin: {ADMIN_USERNAME}")
print("=" * 80)

# Global variables to store test data
created_order_id = None
customer_code = None
order_number = None
admin_token = None
created_order_price_normal = None
created_order_id_eilig = None
customer_code_eilig = None
order_a_id = None
order_a_code = None
order_b_id = None
order_b_code = None

# ============================================================================
# TEST 1: POST /api/orders - Create Order (Normal Priority)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 1: POST /api/orders - Create Order (Normal Priority)")
print("=" * 80)

try:
    payload = {
        "name": "Maria Schmidt",
        "makerworldLink": "https://makerworld.com/de/models/12345",
        "color": "Blau",
        "material": "PLA",
        "size": 100,
        "quantity": 2,
        "priority": "Normal",
        "notes": "Bitte sorgfältig drucken"
    }
    
    response = requests.post(f"{BASE_URL}/orders", json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Validate response structure
        if "orderNumber" in data and data["orderNumber"].startswith("3D-"):
            log_pass("Order creation - orderNumber format (3D-XXXXXX)")
            order_number = data["orderNumber"]
        else:
            log_fail("Order creation - orderNumber format", f"Expected 3D-XXXXXX, got {data.get('orderNumber')}")
        
        if "customerCode" in data and len(data["customerCode"]) == 8:
            log_pass("Order creation - customerCode format (8 chars)")
            customer_code = data["customerCode"]
        else:
            log_fail("Order creation - customerCode format", f"Expected 8 chars, got {data.get('customerCode')}")
        
        if "price" in data and "total" in data["price"] and data["price"]["total"] > 0:
            log_pass("Order creation - price.total > 0")
            created_order_price_normal = data["price"]["total"]
            
            # Validate price calculation
            expected_price = calculate_expected_price(size=100, quantity=2, priority="Normal")
            actual_price = data["price"]["total"]
            
            # Allow 1% tolerance for rounding
            if abs(actual_price - expected_price) / expected_price < 0.01:
                log_pass(f"Order creation - price calculation (expected ~{expected_price}, got {actual_price})")
            else:
                log_fail("Order creation - price calculation", f"Expected ~{expected_price}, got {actual_price}")
        else:
            log_fail("Order creation - price.total", f"Missing or invalid: {data.get('price')}")
        
        log_pass("Order creation - Normal priority (200 OK)")
    else:
        log_fail("Order creation - Normal priority", f"Expected 200, got {response.status_code}: {response.text}")
        
except Exception as e:
    log_fail("Order creation - Normal priority", f"Exception: {str(e)}")

# ============================================================================
# TEST 2: POST /api/orders - Create Order (Eilig Priority)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 2: POST /api/orders - Create Order (Eilig Priority)")
print("=" * 80)

try:
    payload = {
        "name": "Thomas Müller",
        "makerworldLink": "https://makerworld.com/de/models/67890",
        "color": "Rot",
        "material": "PETG",
        "size": 100,
        "quantity": 2,
        "priority": "Eilig",
        "notes": "Dringend benötigt"
    }
    
    response = requests.post(f"{BASE_URL}/orders", json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        customer_code_eilig = data.get("customerCode")
        
        if "price" in data and "total" in data["price"]:
            price_eilig = data["price"]["total"]
            
            # Validate Eilig price is ~25% higher than Normal
            expected_price_eilig = calculate_expected_price(size=100, quantity=2, priority="Eilig")
            expected_price_normal = calculate_expected_price(size=100, quantity=2, priority="Normal")
            
            print(f"Price Eilig: {price_eilig}")
            print(f"Expected Eilig: {expected_price_eilig}")
            print(f"Expected Normal: {expected_price_normal}")
            
            # Check if Eilig is approximately 25% more than Normal
            if abs(price_eilig - expected_price_eilig) / expected_price_eilig < 0.01:
                log_pass(f"Order creation - Eilig price calculation (expected ~{expected_price_eilig}, got {price_eilig})")
                
                # Verify it's ~25% more than Normal
                ratio = price_eilig / expected_price_normal
                if 1.24 < ratio < 1.26:  # Allow small tolerance
                    log_pass(f"Order creation - Eilig surcharge (~25% more than Normal, ratio: {ratio:.3f})")
                else:
                    log_fail("Order creation - Eilig surcharge", f"Expected ~1.25x Normal, got {ratio:.3f}x")
            else:
                log_fail("Order creation - Eilig price", f"Expected ~{expected_price_eilig}, got {price_eilig}")
        
        log_pass("Order creation - Eilig priority (200 OK)")
    else:
        log_fail("Order creation - Eilig priority", f"Expected 200, got {response.status_code}: {response.text}")
        
except Exception as e:
    log_fail("Order creation - Eilig priority", f"Exception: {str(e)}")

# ============================================================================
# TEST 3: POST /api/orders - Validation (Missing name)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 3: POST /api/orders - Validation (Missing name)")
print("=" * 80)

try:
    payload = {
        "makerworldLink": "https://makerworld.com/de/models/12345",
        "color": "Grün"
    }
    
    response = requests.post(f"{BASE_URL}/orders", json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        log_pass("Order validation - Missing name returns 400")
    else:
        log_fail("Order validation - Missing name", f"Expected 400, got {response.status_code}")
        
except Exception as e:
    log_fail("Order validation - Missing name", f"Exception: {str(e)}")

# ============================================================================
# TEST 4: POST /api/orders - Validation (Missing makerworldLink)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 4: POST /api/orders - Validation (Missing makerworldLink)")
print("=" * 80)

try:
    payload = {
        "name": "Test User",
        "color": "Gelb"
    }
    
    response = requests.post(f"{BASE_URL}/orders", json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        log_pass("Order validation - Missing makerworldLink returns 400")
    else:
        log_fail("Order validation - Missing makerworldLink", f"Expected 400, got {response.status_code}")
        
except Exception as e:
    log_fail("Order validation - Missing makerworldLink", f"Exception: {str(e)}")

# ============================================================================
# TEST 5: GET /api/orders/track - Valid customerCode
# ============================================================================
print("\n" + "=" * 80)
print("TEST 5: GET /api/orders/track - Valid customerCode")
print("=" * 80)

if customer_code:
    try:
        response = requests.get(f"{BASE_URL}/orders/track?code={customer_code}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get("status") == "Eingegangen":
                log_pass("Order tracking - status is 'Eingegangen'")
            else:
                log_fail("Order tracking - status", f"Expected 'Eingegangen', got {data.get('status')}")
            
            if data.get("orderNumber") == order_number:
                log_pass("Order tracking - orderNumber matches")
            else:
                log_fail("Order tracking - orderNumber", f"Expected {order_number}, got {data.get('orderNumber')}")
            
            if "price" in data and "total" in data["price"]:
                log_pass("Order tracking - price information present")
            else:
                log_fail("Order tracking - price", "Missing price information")
            
            # Store order ID for later tests
            if "id" in data:
                created_order_id = data["id"]
                print(f"Stored order ID: {created_order_id}")
            
            log_pass("Order tracking - Valid code (200 OK)")
        else:
            log_fail("Order tracking - Valid code", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Order tracking - Valid code", f"Exception: {str(e)}")
else:
    log_fail("Order tracking - Valid code", "No customer code available from order creation")

# ============================================================================
# TEST 6: GET /api/orders/track - Invalid customerCode
# ============================================================================
print("\n" + "=" * 80)
print("TEST 6: GET /api/orders/track - Invalid customerCode")
print("=" * 80)

try:
    response = requests.get(f"{BASE_URL}/orders/track?code=INVALID1", timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 404:
        log_pass("Order tracking - Invalid code returns 404")
    else:
        log_fail("Order tracking - Invalid code", f"Expected 404, got {response.status_code}")
        
except Exception as e:
    log_fail("Order tracking - Invalid code", f"Exception: {str(e)}")

# ============================================================================
# TEST 7: POST /api/admin/login - Correct credentials
# ============================================================================
print("\n" + "=" * 80)
print("TEST 7: POST /api/admin/login - Correct credentials")
print("=" * 80)

try:
    payload = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/admin/login", json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if "token" in data and data["token"]:
            admin_token = data["token"]
            log_pass("Admin login - token received")
            print(f"Token: {admin_token}")
        else:
            log_fail("Admin login - token", "No token in response")
        
        log_pass("Admin login - Correct credentials (200 OK)")
    else:
        log_fail("Admin login - Correct credentials", f"Expected 200, got {response.status_code}: {response.text}")
        
except Exception as e:
    log_fail("Admin login - Correct credentials", f"Exception: {str(e)}")

# ============================================================================
# TEST 8: POST /api/admin/login - Incorrect credentials
# ============================================================================
print("\n" + "=" * 80)
print("TEST 8: POST /api/admin/login - Incorrect credentials")
print("=" * 80)

try:
    payload = {
        "username": "admin",
        "password": "WrongPassword"
    }
    
    response = requests.post(f"{BASE_URL}/admin/login", json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 401:
        log_pass("Admin login - Incorrect credentials returns 401")
    else:
        log_fail("Admin login - Incorrect credentials", f"Expected 401, got {response.status_code}")
        
except Exception as e:
    log_fail("Admin login - Incorrect credentials", f"Exception: {str(e)}")

# ============================================================================
# TEST 9: GET /api/orders - Without Authorization
# ============================================================================
print("\n" + "=" * 80)
print("TEST 9: GET /api/orders - Without Authorization")
print("=" * 80)

try:
    response = requests.get(f"{BASE_URL}/orders", timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 401:
        log_pass("Admin list orders - No auth returns 401")
    else:
        log_fail("Admin list orders - No auth", f"Expected 401, got {response.status_code}")
        
except Exception as e:
    log_fail("Admin list orders - No auth", f"Exception: {str(e)}")

# ============================================================================
# TEST 10: GET /api/orders - With Authorization
# ============================================================================
print("\n" + "=" * 80)
print("TEST 10: GET /api/orders - With Authorization")
print("=" * 80)

if admin_token:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/orders", headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response contains {len(data.get('orders', []))} orders")
            
            if "orders" in data and isinstance(data["orders"], list):
                log_pass("Admin list orders - Returns orders array")
                
                # Check if our created order is in the list
                found = False
                for order in data["orders"]:
                    if order.get("customerCode") == customer_code:
                        found = True
                        created_order_id = order.get("id")
                        print(f"Found our order with ID: {created_order_id}")
                        
                        # Verify no _id field (only UUID id)
                        if "_id" in order:
                            log_fail("Admin list orders - MongoDB _id leak", "Response contains _id field")
                        else:
                            log_pass("Admin list orders - No MongoDB _id in response")
                        break
                
                if found:
                    log_pass("Admin list orders - Created order found in list")
                else:
                    log_warning("Admin list orders - Created order not found", "Order may not be in database")
            else:
                log_fail("Admin list orders - orders array", "Missing or invalid orders array")
            
            log_pass("Admin list orders - With auth (200 OK)")
        else:
            log_fail("Admin list orders - With auth", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Admin list orders - With auth", f"Exception: {str(e)}")
else:
    log_fail("Admin list orders - With auth", "No admin token available")

# ============================================================================
# TEST 11: PUT /api/orders/:id - Update status (With Auth)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 11: PUT /api/orders/:id - Update status (With Auth)")
print("=" * 80)

if admin_token and created_order_id:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {"status": "Druck läuft"}
        
        response = requests.put(f"{BASE_URL}/orders/{created_order_id}", json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get("ok"):
                log_pass("Admin update order - ok: true")
            
            if "order" in data:
                order = data["order"]
                if order.get("status") == "Druck läuft":
                    log_pass("Admin update order - status updated to 'Druck läuft'")
                else:
                    log_fail("Admin update order - status", f"Expected 'Druck läuft', got {order.get('status')}")
                
                if "statusHistory" in order and len(order["statusHistory"]) >= 2:
                    log_pass("Admin update order - statusHistory updated")
                else:
                    log_fail("Admin update order - statusHistory", "History not properly updated")
            
            log_pass("Admin update order - Status update (200 OK)")
        else:
            log_fail("Admin update order - Status update", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Admin update order - Status update", f"Exception: {str(e)}")
else:
    log_fail("Admin update order - Status update", "Missing admin token or order ID")

# ============================================================================
# TEST 12: GET /api/orders/track - Verify status update
# ============================================================================
print("\n" + "=" * 80)
print("TEST 12: GET /api/orders/track - Verify status update")
print("=" * 80)

if customer_code:
    try:
        response = requests.get(f"{BASE_URL}/orders/track?code={customer_code}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "Druck läuft":
                log_pass("Order tracking - Status updated to 'Druck läuft'")
            else:
                log_fail("Order tracking - Status update", f"Expected 'Druck läuft', got {data.get('status')}")
        else:
            log_fail("Order tracking - Verify status", f"Expected 200, got {response.status_code}")
            
    except Exception as e:
        log_fail("Order tracking - Verify status", f"Exception: {str(e)}")
else:
    log_fail("Order tracking - Verify status", "No customer code available")

# ============================================================================
# TEST 13: PUT /api/orders/:id - Update quantity (price recalculation)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 13: PUT /api/orders/:id - Update quantity (price recalculation)")
print("=" * 80)

if admin_token and created_order_id:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {"quantity": 4}
        
        response = requests.put(f"{BASE_URL}/orders/{created_order_id}", json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "order" in data and "price" in data["order"]:
                new_price = data["order"]["price"]["total"]
                print(f"New price after quantity update: {new_price}")
                
                # Price should increase when quantity increases from 2 to 4
                expected_new_price = calculate_expected_price(size=100, quantity=4, priority="Normal")
                
                if abs(new_price - expected_new_price) / expected_new_price < 0.01:
                    log_pass(f"Admin update order - Price recalculated (expected ~{expected_new_price}, got {new_price})")
                else:
                    log_fail("Admin update order - Price recalculation", f"Expected ~{expected_new_price}, got {new_price}")
            
            log_pass("Admin update order - Quantity update (200 OK)")
        else:
            log_fail("Admin update order - Quantity update", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Admin update order - Quantity update", f"Exception: {str(e)}")
else:
    log_fail("Admin update order - Quantity update", "Missing admin token or order ID")

# ============================================================================
# TEST 14: PUT /api/orders/:id - Add photos
# ============================================================================
print("\n" + "=" * 80)
print("TEST 14: PUT /api/orders/:id - Add photos")
print("=" * 80)

if admin_token and created_order_id:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Small base64 test image
        test_photo = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        payload = {"photos": [test_photo]}
        
        response = requests.put(f"{BASE_URL}/orders/{created_order_id}", json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "order" in data and "photos" in data["order"]:
                photos = data["order"]["photos"]
                if len(photos) > 0 and test_photo in photos:
                    log_pass("Admin update order - Photo added successfully")
                else:
                    log_fail("Admin update order - Photo", f"Photo not found in order. Got: {photos}")
            else:
                log_fail("Admin update order - Photo", "Photos field missing in response")
            
            log_pass("Admin update order - Add photos (200 OK)")
        else:
            log_fail("Admin update order - Add photos", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Admin update order - Add photos", f"Exception: {str(e)}")
else:
    log_fail("Admin update order - Add photos", "Missing admin token or order ID")

# ============================================================================
# TEST 15: PUT /api/orders/:id - Without Authorization
# ============================================================================
print("\n" + "=" * 80)
print("TEST 15: PUT /api/orders/:id - Without Authorization")
print("=" * 80)

if created_order_id:
    try:
        payload = {"status": "Fertig"}
        response = requests.put(f"{BASE_URL}/orders/{created_order_id}", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            log_pass("Admin update order - No auth returns 401")
        else:
            log_fail("Admin update order - No auth", f"Expected 401, got {response.status_code}")
            
    except Exception as e:
        log_fail("Admin update order - No auth", f"Exception: {str(e)}")
else:
    log_fail("Admin update order - No auth", "No order ID available")

# ============================================================================
# TEST 16: DELETE /api/orders/:id - Without Authorization
# ============================================================================
print("\n" + "=" * 80)
print("TEST 16: DELETE /api/orders/:id - Without Authorization")
print("=" * 80)

if created_order_id:
    try:
        response = requests.delete(f"{BASE_URL}/orders/{created_order_id}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            log_pass("Admin delete order - No auth returns 401")
        else:
            log_fail("Admin delete order - No auth", f"Expected 401, got {response.status_code}")
            
    except Exception as e:
        log_fail("Admin delete order - No auth", f"Exception: {str(e)}")
else:
    log_fail("Admin delete order - No auth", "No order ID available")

# ============================================================================
# TEST 17: DELETE /api/orders/:id - Non-existent ID
# ============================================================================
print("\n" + "=" * 80)
print("TEST 17: DELETE /api/orders/:id - Non-existent ID")
print("=" * 80)

if admin_token:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.delete(f"{BASE_URL}/orders/{fake_id}", headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            log_pass("Admin delete order - Non-existent ID returns 404")
        else:
            log_fail("Admin delete order - Non-existent ID", f"Expected 404, got {response.status_code}")
            
    except Exception as e:
        log_fail("Admin delete order - Non-existent ID", f"Exception: {str(e)}")
else:
    log_fail("Admin delete order - Non-existent ID", "No admin token available")

# ============================================================================
# TEST 18: DELETE /api/orders/:id - With Authorization
# ============================================================================
print("\n" + "=" * 80)
print("TEST 18: DELETE /api/orders/:id - With Authorization")
print("=" * 80)

if admin_token and created_order_id:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.delete(f"{BASE_URL}/orders/{created_order_id}", headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                log_pass("Admin delete order - With auth (200 OK)")
            else:
                log_fail("Admin delete order - Response", f"Expected ok:true, got {data}")
        else:
            log_fail("Admin delete order - With auth", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Admin delete order - With auth", f"Exception: {str(e)}")
else:
    log_fail("Admin delete order - With auth", "Missing admin token or order ID")

# ============================================================================
# TEST 19: GET /api/orders/track - After deletion
# ============================================================================
print("\n" + "=" * 80)
print("TEST 19: GET /api/orders/track - After deletion")
print("=" * 80)

if customer_code:
    try:
        response = requests.get(f"{BASE_URL}/orders/track?code={customer_code}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            log_pass("Order tracking - Deleted order returns 404")
        else:
            log_fail("Order tracking - Deleted order", f"Expected 404, got {response.status_code}")
            
    except Exception as e:
        log_fail("Order tracking - Deleted order", f"Exception: {str(e)}")
else:
    log_fail("Order tracking - Deleted order", "No customer code available")

# ============================================================================
# TEST 20: POST /api/makerworld-preview - Invalid URL
# ============================================================================
print("\n" + "=" * 80)
print("TEST 20: POST /api/makerworld-preview - Invalid URL")
print("=" * 80)

try:
    payload = {"url": "not-a-valid-url"}
    response = requests.post(f"{BASE_URL}/makerworld-preview", json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    # Should NOT return 500, should return 200 with ok:false or 400
    if response.status_code == 500:
        log_fail("MakerWorld preview - Invalid URL", "Returns 500 (should be 200 with ok:false or 400)")
    elif response.status_code == 200:
        data = response.json()
        if data.get("ok") == False:
            log_pass("MakerWorld preview - Invalid URL returns 200 with ok:false")
        else:
            log_warning("MakerWorld preview - Invalid URL", f"Returns 200 but ok is not false: {data}")
    elif response.status_code == 400:
        log_pass("MakerWorld preview - Invalid URL returns 400")
    else:
        log_warning("MakerWorld preview - Invalid URL", f"Unexpected status {response.status_code}")
        
except Exception as e:
    log_fail("MakerWorld preview - Invalid URL", f"Exception: {str(e)}")

# ============================================================================
# TEST 21: POST /api/makerworld-preview - Missing URL
# ============================================================================
print("\n" + "=" * 80)
print("TEST 21: POST /api/makerworld-preview - Missing URL")
print("=" * 80)

try:
    payload = {}
    response = requests.post(f"{BASE_URL}/makerworld-preview", json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        log_pass("MakerWorld preview - Missing URL returns 400")
    else:
        log_fail("MakerWorld preview - Missing URL", f"Expected 400, got {response.status_code}")
        
except Exception as e:
    log_fail("MakerWorld preview - Missing URL", f"Exception: {str(e)}")

# ============================================================================
# TEST 22: GET /api/colors - Default colors (no saved colors yet)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 22: GET /api/colors - Default colors (public endpoint)")
print("=" * 80)

try:
    response = requests.get(f"{BASE_URL}/colors", timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if "colors" in data and isinstance(data["colors"], list):
            colors = data["colors"]
            print(f"Number of colors: {len(colors)}")
            
            # Should return DEFAULT_COLORS (10 entries) if no colors saved yet
            if len(colors) == 10:
                log_pass("GET /api/colors - Returns 10 default colors")
            else:
                log_warning("GET /api/colors - Color count", f"Expected 10 default colors, got {len(colors)}")
            
            # Verify structure: each color should have name and hex
            if all(isinstance(c, dict) and "name" in c and "hex" in c for c in colors):
                log_pass("GET /api/colors - Color structure valid (name, hex)")
            else:
                log_fail("GET /api/colors - Color structure", "Missing name or hex fields")
            
            # Verify no MongoDB _id
            if not any("_id" in c for c in colors):
                log_pass("GET /api/colors - No MongoDB _id in response")
            else:
                log_fail("GET /api/colors - MongoDB _id leak", "Response contains _id field")
            
            log_pass("GET /api/colors - Public endpoint (200 OK)")
        else:
            log_fail("GET /api/colors - Response structure", "Missing or invalid colors array")
    else:
        log_fail("GET /api/colors - Public endpoint", f"Expected 200, got {response.status_code}: {response.text}")
        
except Exception as e:
    log_fail("GET /api/colors - Public endpoint", f"Exception: {str(e)}")

# ============================================================================
# TEST 23: PUT /api/settings/colors - Without Authorization
# ============================================================================
print("\n" + "=" * 80)
print("TEST 23: PUT /api/settings/colors - Without Authorization")
print("=" * 80)

try:
    payload = {
        "colors": [
            {"name": "Testrot", "hex": "#ff0000"}
        ]
    }
    response = requests.put(f"{BASE_URL}/settings/colors", json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 401:
        log_pass("PUT /api/settings/colors - No auth returns 401")
    else:
        log_fail("PUT /api/settings/colors - No auth", f"Expected 401, got {response.status_code}")
        
except Exception as e:
    log_fail("PUT /api/settings/colors - No auth", f"Exception: {str(e)}")

# ============================================================================
# TEST 24: PUT /api/settings/colors - With Authorization (filter empty names)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 24: PUT /api/settings/colors - With Authorization (filter empty names)")
print("=" * 80)

if admin_token:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {
            "colors": [
                {"name": "Testrot", "hex": "#ff0000"},
                {"name": "Testblau", "hex": "#0000ff"},
                {"name": "", "hex": "#123456"}  # This should be filtered out
            ]
        }
        
        response = requests.put(f"{BASE_URL}/settings/colors", json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get("ok"):
                log_pass("PUT /api/settings/colors - ok: true")
            else:
                log_fail("PUT /api/settings/colors - Response", "Expected ok:true")
            
            if "colors" in data and isinstance(data["colors"], list):
                colors = data["colors"]
                print(f"Saved colors count: {len(colors)}")
                
                # Should only have 2 colors (empty name filtered out)
                if len(colors) == 2:
                    log_pass("PUT /api/settings/colors - Empty names filtered (2 colors saved)")
                else:
                    log_fail("PUT /api/settings/colors - Filter empty names", f"Expected 2 colors, got {len(colors)}")
                
                # Verify the saved colors
                names = [c.get("name") for c in colors]
                if "Testrot" in names and "Testblau" in names:
                    log_pass("PUT /api/settings/colors - Correct colors saved (Testrot, Testblau)")
                else:
                    log_fail("PUT /api/settings/colors - Saved colors", f"Expected Testrot and Testblau, got {names}")
                
                # Verify no empty names
                if not any(c.get("name", "").strip() == "" for c in colors):
                    log_pass("PUT /api/settings/colors - No empty names in saved colors")
                else:
                    log_fail("PUT /api/settings/colors - Empty names", "Found empty name in saved colors")
                
                # Verify no MongoDB _id
                if not any("_id" in c for c in colors):
                    log_pass("PUT /api/settings/colors - No MongoDB _id in response")
                else:
                    log_fail("PUT /api/settings/colors - MongoDB _id leak", "Response contains _id field")
            else:
                log_fail("PUT /api/settings/colors - Response structure", "Missing or invalid colors array")
            
            log_pass("PUT /api/settings/colors - With auth (200 OK)")
        else:
            log_fail("PUT /api/settings/colors - With auth", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("PUT /api/settings/colors - With auth", f"Exception: {str(e)}")
else:
    log_fail("PUT /api/settings/colors - With auth", "No admin token available")

# ============================================================================
# TEST 25: GET /api/colors - Verify saved colors (not defaults)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 25: GET /api/colors - Verify saved colors (not defaults)")
print("=" * 80)

try:
    response = requests.get(f"{BASE_URL}/colors", timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if "colors" in data and isinstance(data["colors"], list):
            colors = data["colors"]
            print(f"Number of colors: {len(colors)}")
            
            # Should now return the 2 saved colors (not the 10 defaults)
            if len(colors) == 2:
                log_pass("GET /api/colors - Returns 2 saved colors (not defaults)")
            else:
                log_fail("GET /api/colors - Saved colors count", f"Expected 2 colors, got {len(colors)}")
            
            # Verify the colors are the ones we saved
            names = [c.get("name") for c in colors]
            if "Testrot" in names and "Testblau" in names:
                log_pass("GET /api/colors - Saved colors retrieved (Testrot, Testblau)")
            else:
                log_fail("GET /api/colors - Saved colors", f"Expected Testrot and Testblau, got {names}")
            
            log_pass("GET /api/colors - Saved colors verification (200 OK)")
        else:
            log_fail("GET /api/colors - Response structure", "Missing or invalid colors array")
    else:
        log_fail("GET /api/colors - Saved colors", f"Expected 200, got {response.status_code}: {response.text}")
        
except Exception as e:
    log_fail("GET /api/colors - Saved colors", f"Exception: {str(e)}")

# ============================================================================
# TEST 26: PUT /api/settings/colors - Update with different colors (idempotency)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 26: PUT /api/settings/colors - Update with different colors (idempotency)")
print("=" * 80)

if admin_token:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {
            "colors": [
                {"name": "Lila", "hex": "#9333ea"},
                {"name": "Türkis", "hex": "#14b8a6"},
                {"name": "Pink", "hex": "#ec4899"}
            ]
        }
        
        response = requests.put(f"{BASE_URL}/settings/colors", json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "colors" in data and len(data["colors"]) == 3:
                log_pass("PUT /api/settings/colors - Overwrites previous colors (3 new colors)")
                
                names = [c.get("name") for c in data["colors"]]
                if "Lila" in names and "Türkis" in names and "Pink" in names:
                    log_pass("PUT /api/settings/colors - New colors saved correctly")
                else:
                    log_fail("PUT /api/settings/colors - New colors", f"Expected Lila, Türkis, Pink, got {names}")
            else:
                log_fail("PUT /api/settings/colors - Overwrite", f"Expected 3 colors, got {len(data.get('colors', []))}")
            
            log_pass("PUT /api/settings/colors - Idempotency test (200 OK)")
        else:
            log_fail("PUT /api/settings/colors - Idempotency", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("PUT /api/settings/colors - Idempotency", f"Exception: {str(e)}")
else:
    log_fail("PUT /api/settings/colors - Idempotency", "No admin token available")

# ============================================================================
# NEW FEATURE TESTS - Queue Position and Customer Message
# ============================================================================

# ============================================================================
# TEST 27: Create Order A (for queue testing)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 27: Create Order A (for queue position testing)")
print("=" * 80)

try:
    import time
    payload = {
        "name": "Anna Weber",
        "makerworldLink": "https://makerworld.com/de/models/queue-test-a",
        "color": "Schwarz",
        "material": "PLA",
        "size": 100,
        "quantity": 1,
        "priority": "Normal"
    }
    
    response = requests.post(f"{BASE_URL}/orders", json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        order_a_code = data.get("customerCode")
        print(f"Order A created with code: {order_a_code}")
        log_pass("Queue test - Order A created successfully")
    else:
        log_fail("Queue test - Order A creation", f"Expected 200, got {response.status_code}: {response.text}")
        
    # Wait a moment to ensure different timestamps
    time.sleep(1)
        
except Exception as e:
    log_fail("Queue test - Order A creation", f"Exception: {str(e)}")

# ============================================================================
# TEST 28: Create Order B (for queue testing)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 28: Create Order B (for queue position testing)")
print("=" * 80)

try:
    payload = {
        "name": "Bernd Fischer",
        "makerworldLink": "https://makerworld.com/de/models/queue-test-b",
        "color": "Weiss",
        "material": "PETG",
        "size": 100,
        "quantity": 1,
        "priority": "Normal"
    }
    
    response = requests.post(f"{BASE_URL}/orders", json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        order_b_code = data.get("customerCode")
        print(f"Order B created with code: {order_b_code}")
        log_pass("Queue test - Order B created successfully")
    else:
        log_fail("Queue test - Order B creation", f"Expected 200, got {response.status_code}: {response.text}")
        
except Exception as e:
    log_fail("Queue test - Order B creation", f"Exception: {str(e)}")

# ============================================================================
# TEST 28b: Get Order IDs from admin endpoint
# ============================================================================
print("\n" + "=" * 80)
print("TEST 28b: Get Order IDs from admin endpoint")
print("=" * 80)

if admin_token and order_a_code and order_b_code:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/orders", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get("orders", [])
            
            for order in orders:
                if order.get("customerCode") == order_a_code:
                    order_a_id = order.get("id")
                    print(f"Found Order A ID: {order_a_id}")
                elif order.get("customerCode") == order_b_code:
                    order_b_id = order.get("id")
                    print(f"Found Order B ID: {order_b_id}")
            
            if order_a_id and order_b_id:
                log_pass("Queue test - Order IDs retrieved successfully")
            else:
                log_fail("Queue test - Order IDs", f"Could not find order IDs (A: {order_a_id}, B: {order_b_id})")
        else:
            log_fail("Queue test - Get order IDs", f"Expected 200, got {response.status_code}")
            
    except Exception as e:
        log_fail("Queue test - Get order IDs", f"Exception: {str(e)}")
else:
    log_fail("Queue test - Get order IDs", "Missing admin token or order codes")

# ============================================================================
# TEST 29: Track Order B - queueAhead should be >= 1
# ============================================================================
print("\n" + "=" * 80)
print("TEST 29: Track Order B - queueAhead should be >= 1 (Order A is ahead)")
print("=" * 80)

if order_b_code:
    try:
        response = requests.get(f"{BASE_URL}/orders/track?code={order_b_code}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if "queueAhead" in data:
                queue_ahead = data["queueAhead"]
                print(f"queueAhead: {queue_ahead}")
                
                if queue_ahead >= 1:
                    log_pass(f"Queue position - Order B has queueAhead={queue_ahead} (Order A is ahead)")
                else:
                    log_fail("Queue position - queueAhead", f"Expected >= 1, got {queue_ahead}")
            else:
                log_fail("Queue position - queueAhead field", "queueAhead field missing in response")
            
            if "customerMessage" in data:
                log_pass("Queue position - customerMessage field present")
            else:
                log_fail("Queue position - customerMessage field", "customerMessage field missing in response")
        else:
            log_fail("Queue position - Track Order B", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Queue position - Track Order B", f"Exception: {str(e)}")
else:
    log_fail("Queue position - Track Order B", "No order B code available")

# ============================================================================
# TEST 30: Update Order A status to Abgeschlossen
# ============================================================================
print("\n" + "=" * 80)
print("TEST 30: Update Order A status to 'Abgeschlossen' (admin)")
print("=" * 80)

if admin_token and order_a_id:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {"status": "Abgeschlossen"}
        
        response = requests.put(f"{BASE_URL}/orders/{order_a_id}", json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("order", {}).get("status") == "Abgeschlossen":
                log_pass("Queue test - Order A status updated to 'Abgeschlossen'")
            else:
                log_fail("Queue test - Order A status update", f"Status not updated correctly: {data}")
        else:
            log_fail("Queue test - Order A status update", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Queue test - Order A status update", f"Exception: {str(e)}")
else:
    log_fail("Queue test - Order A status update", "Missing admin token or order A ID")

# ============================================================================
# TEST 31: Track Order B again - queueAhead should decrease
# ============================================================================
print("\n" + "=" * 80)
print("TEST 31: Track Order B again - queueAhead should decrease (Order A is done)")
print("=" * 80)

if order_b_code:
    try:
        response = requests.get(f"{BASE_URL}/orders/track?code={order_b_code}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if "queueAhead" in data:
                queue_ahead = data["queueAhead"]
                print(f"queueAhead after Order A completed: {queue_ahead}")
                
                # Should be 0 or at least less than before (if there were other orders)
                if queue_ahead == 0:
                    log_pass(f"Queue position - Order B queueAhead=0 after Order A completed")
                else:
                    log_warning("Queue position - queueAhead after completion", f"Expected 0, got {queue_ahead} (may have other orders ahead)")
            else:
                log_fail("Queue position - queueAhead field", "queueAhead field missing in response")
        else:
            log_fail("Queue position - Track Order B after A completed", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Queue position - Track Order B after A completed", f"Exception: {str(e)}")
else:
    log_fail("Queue position - Track Order B after A completed", "No order B code available")

# ============================================================================
# TEST 32: Track Order A (done) - queueAhead should be 0
# ============================================================================
print("\n" + "=" * 80)
print("TEST 32: Track Order A (done) - queueAhead should be 0")
print("=" * 80)

if order_a_code:
    try:
        response = requests.get(f"{BASE_URL}/orders/track?code={order_a_code}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get("status") == "Abgeschlossen":
                if "queueAhead" in data:
                    queue_ahead = data["queueAhead"]
                    print(f"queueAhead for completed order: {queue_ahead}")
                    
                    if queue_ahead == 0:
                        log_pass("Queue position - Completed order has queueAhead=0")
                    else:
                        log_fail("Queue position - Completed order queueAhead", f"Expected 0, got {queue_ahead}")
                else:
                    log_fail("Queue position - queueAhead field", "queueAhead field missing in response")
            else:
                log_fail("Queue position - Order A status", f"Expected 'Abgeschlossen', got {data.get('status')}")
        else:
            log_fail("Queue position - Track Order A", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Queue position - Track Order A", f"Exception: {str(e)}")
else:
    log_fail("Queue position - Track Order A", "No order A code available")

# ============================================================================
# TEST 33: Update customerMessage - Without Authorization
# ============================================================================
print("\n" + "=" * 80)
print("TEST 33: Update customerMessage - Without Authorization")
print("=" * 80)

if order_b_id:
    try:
        payload = {"customerMessage": "Test message without auth"}
        response = requests.put(f"{BASE_URL}/orders/{order_b_id}", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            log_pass("Customer message - No auth returns 401")
        else:
            log_fail("Customer message - No auth", f"Expected 401, got {response.status_code}")
            
    except Exception as e:
        log_fail("Customer message - No auth", f"Exception: {str(e)}")
else:
    log_fail("Customer message - No auth", "No order B ID available")

# ============================================================================
# TEST 34: Update customerMessage - With Authorization
# ============================================================================
print("\n" + "=" * 80)
print("TEST 34: Update customerMessage - With Authorization")
print("=" * 80)

if admin_token and order_b_id:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        test_message = "Dein Druck ist fertig"
        payload = {"customerMessage": test_message}
        
        response = requests.put(f"{BASE_URL}/orders/{order_b_id}", json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get("ok"):
                log_pass("Customer message - Update successful (ok: true)")
            else:
                log_fail("Customer message - Update response", "Expected ok:true")
            
            if "order" in data and data["order"].get("customerMessage") == test_message:
                log_pass(f"Customer message - Message set correctly: '{test_message}'")
            else:
                log_fail("Customer message - Message in response", f"Expected '{test_message}', got {data.get('order', {}).get('customerMessage')}")
        else:
            log_fail("Customer message - Update with auth", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Customer message - Update with auth", f"Exception: {str(e)}")
else:
    log_fail("Customer message - Update with auth", "Missing admin token or order B ID")

# ============================================================================
# TEST 35: Track Order B - Verify customerMessage
# ============================================================================
print("\n" + "=" * 80)
print("TEST 35: Track Order B - Verify customerMessage in tracking")
print("=" * 80)

if order_b_code:
    try:
        response = requests.get(f"{BASE_URL}/orders/track?code={order_b_code}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if "customerMessage" in data:
                customer_message = data["customerMessage"]
                print(f"customerMessage: {customer_message}")
                
                if customer_message == "Dein Druck ist fertig":
                    log_pass("Customer message - Message retrieved correctly in tracking")
                else:
                    log_fail("Customer message - Message in tracking", f"Expected 'Dein Druck ist fertig', got '{customer_message}'")
            else:
                log_fail("Customer message - Field in tracking", "customerMessage field missing in response")
        else:
            log_fail("Customer message - Track with message", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Customer message - Track with message", f"Exception: {str(e)}")
else:
    log_fail("Customer message - Track with message", "No order B code available")

# ============================================================================
# TEST 36: Regression - Existing tracking fields still work
# ============================================================================
print("\n" + "=" * 80)
print("TEST 36: Regression - Existing tracking fields still work")
print("=" * 80)

if order_b_code:
    try:
        response = requests.get(f"{BASE_URL}/orders/track?code={order_b_code}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ["orderNumber", "customerCode", "name", "status", "price"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if not missing_fields:
                log_pass("Regression - All existing tracking fields present")
            else:
                log_fail("Regression - Missing fields", f"Missing: {missing_fields}")
            
            if data.get("orderNumber", "").startswith("3D-"):
                log_pass("Regression - orderNumber format still correct")
            else:
                log_fail("Regression - orderNumber format", f"Expected 3D-XXXXXX, got {data.get('orderNumber')}")
            
            if "_id" not in data:
                log_pass("Regression - No MongoDB _id leak")
            else:
                log_fail("Regression - MongoDB _id leak", "Response contains _id field")
        else:
            log_fail("Regression - Tracking", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Regression - Tracking", f"Exception: {str(e)}")
else:
    log_fail("Regression - Tracking", "No order B code available")

# ============================================================================
# TEST 37: Regression - Invalid code still returns 404
# ============================================================================
print("\n" + "=" * 80)
print("TEST 37: Regression - Invalid code still returns 404")
print("=" * 80)

try:
    response = requests.get(f"{BASE_URL}/orders/track?code=INVALID99", timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 404:
        log_pass("Regression - Invalid code returns 404")
    else:
        log_fail("Regression - Invalid code", f"Expected 404, got {response.status_code}")
        
except Exception as e:
    log_fail("Regression - Invalid code", f"Exception: {str(e)}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"✅ PASSED: {len(test_results['passed'])}")
print(f"❌ FAILED: {len(test_results['failed'])}")
print(f"⚠️  WARNINGS: {len(test_results['warnings'])}")
print("=" * 80)

if test_results['failed']:
    print("\nFailed Tests:")
    for fail in test_results['failed']:
        print(f"  ❌ {fail}")

if test_results['warnings']:
    print("\nWarnings:")
    for warn in test_results['warnings']:
        print(f"  ⚠️  {warn}")

print("\n" + "=" * 80)
if len(test_results['failed']) == 0:
    print("🎉 ALL CRITICAL TESTS PASSED!")
else:
    print(f"⚠️  {len(test_results['failed'])} TESTS FAILED")
print("=" * 80)
