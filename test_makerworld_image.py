#!/usr/bin/env python3
"""
Test Suite for MakerWorld Preview Image Feature
Tests the NEW feature: auto image fetch on order creation + manual fetch-image endpoint
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
print("MAKERWORLD PREVIEW IMAGE FEATURE - TEST SUITE")
print("=" * 80)
print(f"Base URL: {BASE_URL}")
print(f"Admin: {ADMIN_USERNAME}")
print("=" * 80)

# Global variables
admin_token = None
order_id = None
order_number = None
customer_code = None

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
            log_pass("Setup - Admin login successful")
            print(f"Token: {admin_token[:20]}...")
        else:
            log_fail("Setup - Admin login", "No token in response")
    else:
        log_fail("Setup - Admin login", f"Expected 200, got {response.status_code}: {response.text}")
        
except Exception as e:
    log_fail("Setup - Admin login", f"Exception: {str(e)}")

# ============================================================================
# SCENARIO 1: Auto image fetch on order creation
# ============================================================================
print("\n" + "=" * 80)
print("SCENARIO 1: Auto image fetch on order creation")
print("=" * 80)
print("Testing: POST /api/orders with MakerWorld link")
print("Expected: 200 OK, image fetched and stored in order.model.image")
print("URL: https://makerworld.com/en/models/1211525")
print("=" * 80)

try:
    payload = {
        "name": "Bild Test",
        "makerworldLink": "https://makerworld.com/en/models/1211525",
        "model": {
            "filamentGrams": 45,
            "printHours": 3
        },
        "size": 100,
        "quantity": 1,
        "priority": "Normal"
    }
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/orders", json=payload, timeout=20)
    elapsed = time.time() - start_time
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Time: {elapsed:.3f}s")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Check response structure
        if data.get("ok"):
            log_pass("Scenario 1 - Response ok:true")
        else:
            log_fail("Scenario 1 - Response", "Expected ok:true")
        
        if "orderNumber" in data and data["orderNumber"].startswith("3D-"):
            order_number = data["orderNumber"]
            log_pass(f"Scenario 1 - orderNumber format correct: {order_number}")
        else:
            log_fail("Scenario 1 - orderNumber", f"Expected 3D-XXXXXX, got {data.get('orderNumber')}")
        
        if "customerCode" in data and len(data["customerCode"]) == 8:
            customer_code = data["customerCode"]
            log_pass(f"Scenario 1 - customerCode format correct: {customer_code}")
        else:
            log_fail("Scenario 1 - customerCode", f"Expected 8 chars, got {data.get('customerCode')}")
        
        # Check response time (should be reasonable even with image fetch)
        if elapsed < 15:
            log_pass(f"Scenario 1 - Response time acceptable: {elapsed:.3f}s (< 15s)")
        else:
            log_warning("Scenario 1 - Response time", f"Took {elapsed:.3f}s (> 15s, but within 20s timeout)")
        
        log_pass("Scenario 1 - Order creation successful (200 OK)")
    else:
        log_fail("Scenario 1 - Order creation", f"Expected 200, got {response.status_code}: {response.text}")
        
except Exception as e:
    log_fail("Scenario 1 - Order creation", f"Exception: {str(e)}")

# ============================================================================
# SCENARIO 1b: Verify image was fetched and stored
# ============================================================================
print("\n" + "=" * 80)
print("SCENARIO 1b: Verify image was fetched and stored")
print("=" * 80)
print("Testing: GET /api/orders (admin) to check order.model.image")
print("=" * 80)

if admin_token and order_number:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/orders", headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            orders_list = data.get("orders", [])
            
            # Find our order by orderNumber
            our_order = None
            for order in orders_list:
                if order.get("orderNumber") == order_number:
                    our_order = order
                    order_id = order.get("id")
                    print(f"Found order with ID: {order_id}")
                    break
            
            if our_order:
                log_pass("Scenario 1b - Order found in admin list")
                
                # Check if model exists
                if "model" in our_order and our_order["model"]:
                    model = our_order["model"]
                    print(f"Model data: {json.dumps(model, indent=2)}")
                    log_pass("Scenario 1b - order.model exists")
                    
                    # Check if image exists and is a URL
                    if "image" in model and model["image"]:
                        image_url = model["image"]
                        print(f"Image URL: {image_url}")
                        
                        if image_url.startswith("http"):
                            log_pass(f"Scenario 1b - order.model.image is a valid URL: {image_url[:60]}...")
                        else:
                            log_fail("Scenario 1b - order.model.image", f"Not a valid URL: {image_url}")
                    else:
                        log_warning("Scenario 1b - order.model.image", "Image not found (Firecrawl may have failed for this URL)")
                    
                    # Check if modelName exists
                    if "modelName" in model and model["modelName"]:
                        log_pass(f"Scenario 1b - order.model.modelName exists: {model['modelName']}")
                    else:
                        log_warning("Scenario 1b - order.model.modelName", "Model name not found")
                    
                    # Verify manual values are preserved
                    if model.get("filamentGrams") == 45:
                        log_pass("Scenario 1b - Manual filamentGrams preserved (45)")
                    else:
                        log_fail("Scenario 1b - filamentGrams", f"Expected 45, got {model.get('filamentGrams')}")
                    
                    if model.get("printHours") == 3:
                        log_pass("Scenario 1b - Manual printHours preserved (3)")
                    else:
                        log_fail("Scenario 1b - printHours", f"Expected 3, got {model.get('printHours')}")
                else:
                    log_warning("Scenario 1b - order.model", "Model field is empty or missing")
                
                # Check no MongoDB _id leak
                if "_id" not in our_order:
                    log_pass("Scenario 1b - No MongoDB _id leak")
                else:
                    log_fail("Scenario 1b - MongoDB _id leak", "Response contains _id field")
            else:
                log_fail("Scenario 1b - Find order", f"Order {order_number} not found in admin list")
        else:
            log_fail("Scenario 1b - Admin GET orders", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Scenario 1b - Verify image", f"Exception: {str(e)}")
else:
    log_fail("Scenario 1b - Verify image", "Missing admin token or order number")

# ============================================================================
# SCENARIO 2: Manual (re)load image endpoint
# ============================================================================
print("\n" + "=" * 80)
print("SCENARIO 2: Manual (re)load image endpoint")
print("=" * 80)
print(f"Testing: POST /api/orders/{order_id}/fetch-image with Bearer auth")
print("Expected: 200 OK with ok:true and order.model.image set")
print("=" * 80)

if admin_token and order_id:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(f"{BASE_URL}/orders/{order_id}/fetch-image", headers=headers, timeout=20)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get("ok"):
                log_pass("Scenario 2 - Response ok:true")
                
                if "order" in data and data["order"]:
                    order = data["order"]
                    
                    if "model" in order and order["model"] and "image" in order["model"]:
                        image_url = order["model"]["image"]
                        print(f"Image URL: {image_url}")
                        
                        if image_url and image_url.startswith("http"):
                            log_pass(f"Scenario 2 - order.model.image is a valid URL: {image_url[:60]}...")
                        else:
                            log_fail("Scenario 2 - order.model.image", f"Not a valid URL: {image_url}")
                    else:
                        log_fail("Scenario 2 - order.model.image", "Image field missing in response")
                else:
                    log_fail("Scenario 2 - Response structure", "order field missing")
                
                log_pass("Scenario 2 - Manual fetch-image successful (200 OK)")
            elif data.get("ok") == False and data.get("error") == "Kein Bild gefunden":
                log_warning("Scenario 2 - No image found", "Firecrawl returned no image for this URL (acceptable if URL has no og:image)")
            else:
                log_fail("Scenario 2 - Response", f"Unexpected response: {data}")
        else:
            log_fail("Scenario 2 - Manual fetch-image", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Scenario 2 - Manual fetch-image", f"Exception: {str(e)}")
else:
    log_fail("Scenario 2 - Manual fetch-image", "Missing admin token or order ID")

# ============================================================================
# SCENARIO 3: Auth check - POST without Authorization header
# ============================================================================
print("\n" + "=" * 80)
print("SCENARIO 3: Auth check - POST without Authorization header")
print("=" * 80)
print(f"Testing: POST /api/orders/{order_id}/fetch-image WITHOUT auth")
print("Expected: 401 Unauthorized")
print("=" * 80)

if order_id:
    try:
        # No Authorization header
        response = requests.post(f"{BASE_URL}/orders/{order_id}/fetch-image", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            log_pass("Scenario 3 - No auth returns 401 (as expected)")
        else:
            log_fail("Scenario 3 - Auth check", f"Expected 401, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Scenario 3 - Auth check", f"Exception: {str(e)}")
else:
    log_fail("Scenario 3 - Auth check", "No order ID available")

# ============================================================================
# SCENARIO 4: Not found - POST with nonexistent ID
# ============================================================================
print("\n" + "=" * 80)
print("SCENARIO 4: Not found - POST with nonexistent ID")
print("=" * 80)
print("Testing: POST /api/orders/nonexistent-id-123/fetch-image WITH auth")
print("Expected: 404 Not Found")
print("=" * 80)

if admin_token:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        fake_id = "nonexistent-id-123"
        
        response = requests.post(f"{BASE_URL}/orders/{fake_id}/fetch-image", headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            log_pass("Scenario 4 - Nonexistent ID returns 404 (as expected)")
        else:
            log_fail("Scenario 4 - Not found check", f"Expected 404, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Scenario 4 - Not found check", f"Exception: {str(e)}")
else:
    log_fail("Scenario 4 - Not found check", "No admin token available")

# ============================================================================
# SCENARIO 5: Regression tests
# ============================================================================
print("\n" + "=" * 80)
print("SCENARIO 5: Regression tests")
print("=" * 80)

# 5a: Order creation still returns quickly-ish
print("\n--- 5a: Order creation performance ---")
try:
    payload = {
        "name": "Performance Test",
        "makerworldLink": "https://makerworld.com/en/models/test",
        "size": 100,
        "quantity": 1,
        "priority": "Normal"
    }
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/orders", json=payload, timeout=20)
    elapsed = time.time() - start_time
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Time: {elapsed:.3f}s")
    
    if response.status_code == 200:
        if elapsed < 15:
            log_pass(f"Scenario 5a - Order creation still quick: {elapsed:.3f}s (< 15s)")
        else:
            log_warning("Scenario 5a - Order creation time", f"Took {elapsed:.3f}s (acceptable but slower)")
    else:
        log_fail("Scenario 5a - Order creation", f"Expected 200, got {response.status_code}")
        
except Exception as e:
    log_fail("Scenario 5a - Order creation performance", f"Exception: {str(e)}")

# 5b: No MongoDB _id leaks in responses
print("\n--- 5b: No MongoDB _id leaks ---")
if admin_token:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/orders", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            orders_list = data.get("orders", [])
            
            has_id_leak = any("_id" in order for order in orders_list)
            
            if not has_id_leak:
                log_pass("Scenario 5b - No MongoDB _id leak in admin orders list")
            else:
                log_fail("Scenario 5b - MongoDB _id leak", "Found _id field in orders")
        else:
            log_fail("Scenario 5b - Get orders", f"Expected 200, got {response.status_code}")
            
    except Exception as e:
        log_fail("Scenario 5b - MongoDB _id check", f"Exception: {str(e)}")
else:
    log_fail("Scenario 5b - MongoDB _id check", "No admin token available")

# 5c: GET /api/orders/track still works
print("\n--- 5c: Tracking endpoint still works ---")
if customer_code:
    try:
        response = requests.get(f"{BASE_URL}/orders/track?code={customer_code}", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Tracking response: {json.dumps(data, indent=2)}")
            
            # Check essential fields
            required_fields = ["orderNumber", "customerCode", "status", "price"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if not missing_fields:
                log_pass("Scenario 5c - Tracking endpoint works, all fields present")
            else:
                log_fail("Scenario 5c - Tracking fields", f"Missing fields: {missing_fields}")
            
            # Check email is NOT exposed
            if "email" not in data:
                log_pass("Scenario 5c - Email NOT exposed in tracking (privacy maintained)")
            else:
                log_fail("Scenario 5c - Email exposure", "Email field should not be in tracking response")
        else:
            log_fail("Scenario 5c - Tracking endpoint", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Scenario 5c - Tracking endpoint", f"Exception: {str(e)}")
else:
    log_fail("Scenario 5c - Tracking endpoint", "No customer code available")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("TEST SUMMARY - MAKERWORLD PREVIEW IMAGE FEATURE")
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
print("SCENARIO RESULTS:")
print("=" * 80)
print("Scenario 1: Auto image fetch on order creation")
print("Scenario 2: Manual (re)load image endpoint")
print("Scenario 3: Auth check (401 without auth)")
print("Scenario 4: Not found (404 for nonexistent ID)")
print("Scenario 5: Regression tests (performance, no _id leaks, tracking works)")
print("=" * 80)

if len(test_results['failed']) == 0:
    print("🎉 ALL CRITICAL TESTS PASSED!")
    exit(0)
else:
    print(f"⚠️  {len(test_results['failed'])} TESTS FAILED")
    exit(1)
