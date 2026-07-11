#!/usr/bin/env python3
"""
Backend API Test Suite for CHANGED Order/Pricing Flow
Tests the new flow where orders are created WITHOUT price,
and price is only calculated when admin sets grams/print-time.
"""

import requests
import json
import time

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

print("=" * 80)
print("3D DRUCK SERVICE - CHANGED ORDER/PRICING FLOW TEST")
print("=" * 80)
print(f"Base URL: {BASE_URL}")
print(f"Admin: {ADMIN_USERNAME}")
print("=" * 80)

# Global variables
admin_token = None
order_id = None
customer_code = None
order_number = None

# ============================================================================
# SETUP: Admin Login
# ============================================================================
print("\n" + "=" * 80)
print("SETUP: Admin Login")
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
        if "token" in data and data["token"]:
            admin_token = data["token"]
            log_pass("Admin login successful")
            print(f"Token: {admin_token[:20]}...")
        else:
            log_fail("Admin login", "No token in response")
    else:
        log_fail("Admin login", f"Expected 200, got {response.status_code}: {response.text}")
        
except Exception as e:
    log_fail("Admin login", f"Exception: {str(e)}")

# ============================================================================
# TEST 1: Create minimal order WITHOUT grams/hours -> price should be null
# ============================================================================
print("\n" + "=" * 80)
print("TEST 1: Create minimal order WITHOUT grams/hours")
print("Expected: 200, ok:true, orderNumber, customerCode, price=null")
print("=" * 80)

try:
    payload = {
        "name": "Preis Test",
        "email": "jannik-druck@gmx.de",
        "makerworldLink": "https://makerworld.com/en/models/1211525",
        "color": "Lila",
        "material": "PLA",
        "size": 100,
        "quantity": 1,
        "priority": "Normal"
    }
    
    response = requests.post(f"{BASE_URL}/orders", json=payload, timeout=15)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Check ok:true
        if data.get("ok") == True:
            log_pass("TEST 1 - Response has ok:true")
        else:
            log_fail("TEST 1 - ok field", f"Expected ok:true, got {data.get('ok')}")
        
        # Check orderNumber format
        if "orderNumber" in data and data["orderNumber"].startswith("3D-"):
            order_number = data["orderNumber"]
            log_pass(f"TEST 1 - orderNumber format correct: {order_number}")
        else:
            log_fail("TEST 1 - orderNumber", f"Expected 3D-XXXXXX, got {data.get('orderNumber')}")
        
        # Check customerCode format
        if "customerCode" in data and len(data["customerCode"]) == 8:
            customer_code = data["customerCode"]
            log_pass(f"TEST 1 - customerCode format correct: {customer_code}")
        else:
            log_fail("TEST 1 - customerCode", f"Expected 8 chars, got {data.get('customerCode')}")
        
        # CRITICAL: Check that price is null (not an object)
        if "price" in data:
            if data["price"] is None:
                log_pass("TEST 1 - price is null (as expected for new flow)")
            else:
                log_fail("TEST 1 - price should be null", f"Expected null, got {data['price']}")
        else:
            log_fail("TEST 1 - price field missing", "Response should contain price field (even if null)")
        
        # Response should NOT require grams/hours
        log_pass("TEST 1 - Order created without requiring grams/hours")
        
    else:
        log_fail("TEST 1 - Order creation", f"Expected 200, got {response.status_code}: {response.text}")
        
except Exception as e:
    log_fail("TEST 1 - Order creation", f"Exception: {str(e)}")

# ============================================================================
# TEST 1b: Admin GET /api/orders - Find order and verify price is null
# ============================================================================
print("\n" + "=" * 80)
print("TEST 1b: Admin GET /api/orders - Verify order.price is null")
print("=" * 80)

if admin_token and customer_code:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/orders", headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get("orders", [])
            
            # Find our order
            found_order = None
            for order in orders:
                if order.get("customerCode") == customer_code:
                    found_order = order
                    order_id = order.get("id")
                    print(f"Found order with ID: {order_id}")
                    break
            
            if found_order:
                log_pass("TEST 1b - Order found in admin list")
                
                # CRITICAL: Verify price is null (not an object)
                if "price" in found_order:
                    if found_order["price"] is None:
                        log_pass("TEST 1b - order.price is null (not an object)")
                    else:
                        log_fail("TEST 1b - order.price should be null", f"Expected null, got {found_order['price']}")
                else:
                    log_fail("TEST 1b - price field missing", "Order should have price field (even if null)")
                
                # Check no MongoDB _id leak
                if "_id" not in found_order:
                    log_pass("TEST 1b - No MongoDB _id leak")
                else:
                    log_fail("TEST 1b - MongoDB _id leak", "Response contains _id field")
            else:
                log_fail("TEST 1b - Order not found", f"Could not find order with code {customer_code}")
        else:
            log_fail("TEST 1b - Admin list orders", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("TEST 1b - Admin list orders", f"Exception: {str(e)}")
else:
    log_fail("TEST 1b - Admin list orders", "Missing admin token or customer code")

# ============================================================================
# TEST 2: Track before pricing -> price should be null, email NOT exposed
# ============================================================================
print("\n" + "=" * 80)
print("TEST 2: Track before pricing")
print("Expected: 200, price=null, email NOT exposed")
print("=" * 80)

if customer_code:
    try:
        response = requests.get(f"{BASE_URL}/orders/track?code={customer_code}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check price is null
            if "price" in data:
                if data["price"] is None:
                    log_pass("TEST 2 - price is null before admin sets grams/time")
                else:
                    log_fail("TEST 2 - price should be null", f"Expected null, got {data['price']}")
            else:
                log_fail("TEST 2 - price field missing", "Tracking should include price field (even if null)")
            
            # CRITICAL: Email should NOT be exposed in tracking
            if "email" not in data:
                log_pass("TEST 2 - email NOT exposed in tracking (privacy maintained)")
            else:
                log_fail("TEST 2 - email exposed", f"Email should not be in tracking response, got: {data.get('email')}")
            
            # Check other fields are present
            required_fields = ["orderNumber", "customerCode", "status"]
            missing = [f for f in required_fields if f not in data]
            if not missing:
                log_pass("TEST 2 - All required tracking fields present")
            else:
                log_fail("TEST 2 - Missing fields", f"Missing: {missing}")
                
        else:
            log_fail("TEST 2 - Track before pricing", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("TEST 2 - Track before pricing", f"Exception: {str(e)}")
else:
    log_fail("TEST 2 - Track before pricing", "No customer code available")

# ============================================================================
# TEST 3: Admin sets grams/time -> price computed
# ============================================================================
print("\n" + "=" * 80)
print("TEST 3: Admin sets grams/time -> price computed")
print("Expected: 200, ok:true, order.price.total > 0")
print("=" * 80)

if admin_token and order_id:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {
            "model": {
                "filamentGrams": 45,
                "printHours": 3
            }
        }
        
        response = requests.put(f"{BASE_URL}/orders/{order_id}", json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check ok:true
            if data.get("ok") == True:
                log_pass("TEST 3 - Response has ok:true")
            else:
                log_fail("TEST 3 - ok field", f"Expected ok:true, got {data.get('ok')}")
            
            # CRITICAL: Check that price is now calculated (not null)
            if "order" in data:
                order = data["order"]
                
                if "price" in order and order["price"] is not None:
                    if isinstance(order["price"], dict) and "total" in order["price"]:
                        price_total = order["price"]["total"]
                        if isinstance(price_total, (int, float)) and price_total > 0:
                            log_pass(f"TEST 3 - order.price.total is numeric and > 0: {price_total}")
                        else:
                            log_fail("TEST 3 - price.total value", f"Expected numeric > 0, got {price_total}")
                    else:
                        log_fail("TEST 3 - price structure", f"Expected price object with total, got {order['price']}")
                else:
                    log_fail("TEST 3 - price should be calculated", f"Expected price object, got {order.get('price')}")
                
                # Verify model.image is preserved (if it existed)
                if "model" in order:
                    if "image" in order["model"]:
                        log_pass("TEST 3 - model.image preserved after setting grams")
                    else:
                        log_warning("TEST 3 - model.image", "No image in model (may not have been fetched)")
                    
                    # Verify grams and hours are set
                    if order["model"].get("filamentGrams") == 45:
                        log_pass("TEST 3 - model.filamentGrams set correctly")
                    else:
                        log_fail("TEST 3 - filamentGrams", f"Expected 45, got {order['model'].get('filamentGrams')}")
                    
                    if order["model"].get("printHours") == 3:
                        log_pass("TEST 3 - model.printHours set correctly")
                    else:
                        log_fail("TEST 3 - printHours", f"Expected 3, got {order['model'].get('printHours')}")
            else:
                log_fail("TEST 3 - Response structure", "Missing order in response")
                
        else:
            log_fail("TEST 3 - Admin set grams/time", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("TEST 3 - Admin set grams/time", f"Exception: {str(e)}")
else:
    log_fail("TEST 3 - Admin set grams/time", "Missing admin token or order ID")

# ============================================================================
# TEST 4: Track after pricing -> price.total is numeric
# ============================================================================
print("\n" + "=" * 80)
print("TEST 4: Track after pricing")
print("Expected: 200, price.total is numeric value from TEST 3")
print("=" * 80)

if customer_code:
    try:
        response = requests.get(f"{BASE_URL}/orders/track?code={customer_code}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check price is now set
            if "price" in data and data["price"] is not None:
                if isinstance(data["price"], dict) and "total" in data["price"]:
                    price_total = data["price"]["total"]
                    if isinstance(price_total, (int, float)) and price_total > 0:
                        log_pass(f"TEST 4 - price.total is numeric after admin set grams: {price_total}")
                    else:
                        log_fail("TEST 4 - price.total value", f"Expected numeric > 0, got {price_total}")
                else:
                    log_fail("TEST 4 - price structure", f"Expected price object with total, got {data['price']}")
            else:
                log_fail("TEST 4 - price should be set", f"Expected price object, got {data.get('price')}")
                
        else:
            log_fail("TEST 4 - Track after pricing", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("TEST 4 - Track after pricing", f"Exception: {str(e)}")
else:
    log_fail("TEST 4 - Track after pricing", "No customer code available")

# ============================================================================
# TEST 5: Eilig recalculation -> price ~25% higher
# ============================================================================
print("\n" + "=" * 80)
print("TEST 5: Eilig recalculation")
print("Expected: 200, price.total ~25% higher than Normal price")
print("=" * 80)

# First, get the current Normal price
normal_price = None
if customer_code:
    try:
        response = requests.get(f"{BASE_URL}/orders/track?code={customer_code}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("price") and "total" in data["price"]:
                normal_price = data["price"]["total"]
                print(f"Current Normal price: {normal_price}")
    except Exception as e:
        print(f"Could not get current price: {e}")

# Now update to Eilig
if admin_token and order_id and normal_price:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {"priority": "Eilig"}
        
        response = requests.put(f"{BASE_URL}/orders/{order_id}", json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if "order" in data and "price" in data["order"] and data["order"]["price"]:
                eilig_price = data["order"]["price"]["total"]
                print(f"Eilig price: {eilig_price}")
                
                # Calculate expected ratio (should be ~1.25)
                ratio = eilig_price / normal_price
                print(f"Price ratio (Eilig/Normal): {ratio:.3f}")
                
                # Allow 1% tolerance
                if 1.24 < ratio < 1.26:
                    log_pass(f"TEST 5 - Eilig price ~25% higher (ratio: {ratio:.3f})")
                else:
                    log_fail("TEST 5 - Eilig surcharge", f"Expected ratio ~1.25, got {ratio:.3f}")
            else:
                log_fail("TEST 5 - Response structure", "Missing price in response")
                
        else:
            log_fail("TEST 5 - Update to Eilig", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("TEST 5 - Update to Eilig", f"Exception: {str(e)}")
else:
    log_fail("TEST 5 - Update to Eilig", "Missing admin token, order ID, or normal price")

# ============================================================================
# TEST 6: Status to Abholbereit -> triggers pickup email (async)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 6: Status to Abholbereit")
print("Expected: 200, status updated (email sent async, should not block)")
print("=" * 80)

if admin_token and order_id:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {"status": "Abholbereit"}
        
        start_time = time.time()
        response = requests.put(f"{BASE_URL}/orders/{order_id}", json=payload, headers=headers, timeout=10)
        response_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response time: {response_time:.3f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check status updated
            if "order" in data and data["order"].get("status") == "Abholbereit":
                log_pass("TEST 6 - Status updated to 'Abholbereit'")
            else:
                log_fail("TEST 6 - Status update", f"Expected 'Abholbereit', got {data.get('order', {}).get('status')}")
            
            # Response should be quick (email is async)
            if response_time < 2.0:
                log_pass(f"TEST 6 - Response quick ({response_time:.3f}s, email is async)")
            else:
                log_warning("TEST 6 - Response time", f"Response took {response_time:.3f}s (should be < 2s if email is async)")
                
        else:
            log_fail("TEST 6 - Status to Abholbereit", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("TEST 6 - Status to Abholbereit", f"Exception: {str(e)}")
else:
    log_fail("TEST 6 - Status to Abholbereit", "Missing admin token or order ID")

# ============================================================================
# TEST 7: Validation - Missing makerworldLink
# ============================================================================
print("\n" + "=" * 80)
print("TEST 7: Validation - Missing makerworldLink")
print("Expected: 400")
print("=" * 80)

try:
    payload = {"name": "NoLink"}
    
    response = requests.post(f"{BASE_URL}/orders", json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        log_pass("TEST 7 - Missing makerworldLink returns 400")
    else:
        log_fail("TEST 7 - Validation", f"Expected 400, got {response.status_code}")
        
except Exception as e:
    log_fail("TEST 7 - Validation", f"Exception: {str(e)}")

# ============================================================================
# TEST 8: Validation - Missing name
# ============================================================================
print("\n" + "=" * 80)
print("TEST 8: Validation - Missing name")
print("Expected: 400")
print("=" * 80)

try:
    payload = {"makerworldLink": "https://x.com"}
    
    response = requests.post(f"{BASE_URL}/orders", json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        log_pass("TEST 8 - Missing name returns 400")
    else:
        log_fail("TEST 8 - Validation", f"Expected 400, got {response.status_code}")
        
except Exception as e:
    log_fail("TEST 8 - Validation", f"Exception: {str(e)}")

# ============================================================================
# TEST 9: Auth - PUT without Authorization
# ============================================================================
print("\n" + "=" * 80)
print("TEST 9: Auth - PUT without Authorization")
print("Expected: 401")
print("=" * 80)

if order_id:
    try:
        payload = {"status": "Fertig"}
        
        response = requests.put(f"{BASE_URL}/orders/{order_id}", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            log_pass("TEST 9 - PUT without Authorization returns 401")
        else:
            log_fail("TEST 9 - Auth check", f"Expected 401, got {response.status_code}")
            
    except Exception as e:
        log_fail("TEST 9 - Auth check", f"Exception: {str(e)}")
else:
    log_fail("TEST 9 - Auth check", "No order ID available")

# ============================================================================
# TEST 10: Regression - GET /api/email-status with admin auth
# ============================================================================
print("\n" + "=" * 80)
print("TEST 10: Regression - GET /api/email-status")
print("Expected: 200, ok:true")
print("=" * 80)

if admin_token:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/email-status", headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get("ok") == True:
                log_pass("TEST 10 - GET /api/email-status returns ok:true")
            else:
                log_warning("TEST 10 - email-status", f"Expected ok:true, got {data}")
        else:
            log_fail("TEST 10 - email-status", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("TEST 10 - email-status", f"Exception: {str(e)}")
else:
    log_fail("TEST 10 - email-status", "No admin token available")

# ============================================================================
# TEST 11: Regression - No MongoDB _id leaks in tracking
# ============================================================================
print("\n" + "=" * 80)
print("TEST 11: Regression - No MongoDB _id leaks")
print("=" * 80)

if customer_code:
    try:
        response = requests.get(f"{BASE_URL}/orders/track?code={customer_code}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "_id" not in data:
                log_pass("TEST 11 - No MongoDB _id in tracking response")
            else:
                log_fail("TEST 11 - MongoDB _id leak", "Response contains _id field")
                
        else:
            log_fail("TEST 11 - Tracking", f"Expected 200, got {response.status_code}")
            
    except Exception as e:
        log_fail("TEST 11 - Tracking", f"Exception: {str(e)}")
else:
    log_fail("TEST 11 - Tracking", "No customer code available")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("TEST SUMMARY - CHANGED ORDER/PRICING FLOW")
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
    print("🎉 ALL TESTS PASSED!")
    print("\nKey Findings:")
    print("  • Orders created WITHOUT price (price=null)")
    print("  • Price calculated when admin sets grams/printHours")
    print("  • Eilig priority adds ~25% surcharge")
    print("  • Email NOT exposed in tracking (privacy maintained)")
    print("  • Validation and auth working correctly")
    print("  • No MongoDB _id leaks")
else:
    print(f"⚠️  {len(test_results['failed'])} TESTS FAILED")
print("=" * 80)
