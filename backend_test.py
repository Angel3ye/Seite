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
