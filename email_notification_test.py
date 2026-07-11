#!/usr/bin/env python3
"""
Email Notification Feature Test Suite for 3D Druck Service
Tests the NEW email notification functionality according to review request
"""

import requests
import json
import time

# Base URL from environment
BASE_URL = "https://order-prints-6.preview.emergentagent.com/api"

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin123!"

# Test email (verified working by main agent)
TEST_EMAIL = "jannik-druck@gmx.de"

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
print("EMAIL NOTIFICATION FEATURE - TEST SUITE")
print("=" * 80)
print(f"Base URL: {BASE_URL}")
print(f"Test Email: {TEST_EMAIL}")
print("=" * 80)

# Global variables to store test data
admin_token = None
order_with_email_id = None
order_with_email_code = None
order_with_email_number = None
order_without_email_id = None
order_without_email_code = None
order_without_email_number = None

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
            print(f"✅ Admin token obtained")
        else:
            print(f"❌ No token in response")
    else:
        print(f"❌ Login failed: {response.status_code}")
        
except Exception as e:
    print(f"❌ Exception during login: {str(e)}")

# ============================================================================
# TEST 1: POST /api/orders WITH email - Verify quick response
# ============================================================================
print("\n" + "=" * 80)
print("TEST 1: POST /api/orders WITH email (jannik-druck@gmx.de)")
print("=" * 80)

try:
    payload = {
        "name": "Test Kunde",
        "email": TEST_EMAIL,
        "makerworldLink": "https://makerworld.com/de/models/123",
        "model": {
            "filamentGrams": 45,
            "printHours": 3
        },
        "size": 100,
        "quantity": 1,
        "priority": "Normal"
    }
    
    # Measure response time
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/orders", json=payload, timeout=10)
    response_time = time.time() - start_time
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Time: {response_time:.3f}s")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Verify ok: true
        if data.get("ok") == True:
            log_pass("Email order - ok: true")
        else:
            log_fail("Email order - ok field", f"Expected ok:true, got {data.get('ok')}")
        
        # Verify orderNumber format (3D-XXXXXX)
        if "orderNumber" in data and data["orderNumber"].startswith("3D-"):
            log_pass("Email order - orderNumber format (3D-XXXXXX)")
            order_with_email_number = data["orderNumber"]
        else:
            log_fail("Email order - orderNumber", f"Expected 3D-XXXXXX, got {data.get('orderNumber')}")
        
        # Verify customerCode (8 chars)
        if "customerCode" in data and len(data["customerCode"]) == 8:
            log_pass("Email order - customerCode (8 chars)")
            order_with_email_code = data["customerCode"]
        else:
            log_fail("Email order - customerCode", f"Expected 8 chars, got {data.get('customerCode')}")
        
        # Verify quick response (email is async, should not block)
        if response_time < 5.0:
            log_pass(f"Email order - Quick response ({response_time:.3f}s < 5s, email is async)")
        else:
            log_warning("Email order - Response time", f"Response took {response_time:.3f}s (may indicate blocking)")
        
        log_pass("Email order - POST with email (200 OK)")
    else:
        log_fail("Email order - POST with email", f"Expected 200, got {response.status_code}: {response.text}")
        
except Exception as e:
    log_fail("Email order - POST with email", f"Exception: {str(e)}")

# ============================================================================
# TEST 2: GET /api/orders (admin) - Verify email stored
# ============================================================================
print("\n" + "=" * 80)
print("TEST 2: GET /api/orders (admin) - Verify email stored")
print("=" * 80)

if admin_token and order_with_email_code:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/orders", headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get("orders", [])
            print(f"Total orders: {len(orders)}")
            
            # Find our order by customerCode
            found_order = None
            for order in orders:
                if order.get("customerCode") == order_with_email_code:
                    found_order = order
                    order_with_email_id = order.get("id")
                    break
            
            if found_order:
                log_pass("Email storage - Order found in admin list")
                print(f"Order ID: {order_with_email_id}")
                
                # Verify email field exists and matches
                if "email" in found_order:
                    if found_order["email"] == TEST_EMAIL:
                        log_pass(f"Email storage - Email stored correctly ({TEST_EMAIL})")
                    else:
                        log_fail("Email storage - Email value", f"Expected {TEST_EMAIL}, got {found_order['email']}")
                else:
                    log_fail("Email storage - Email field", "Email field missing in order")
                
                # Verify no MongoDB _id leak
                if "_id" not in found_order:
                    log_pass("Email storage - No MongoDB _id leak")
                else:
                    log_fail("Email storage - MongoDB _id", "Response contains _id field")
            else:
                log_fail("Email storage - Order not found", f"Could not find order with code {order_with_email_code}")
        else:
            log_fail("Email storage - GET orders", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Email storage - GET orders", f"Exception: {str(e)}")
else:
    log_fail("Email storage - GET orders", "Missing admin token or order code")

# ============================================================================
# TEST 3: POST /api/orders WITHOUT email - Verify empty string
# ============================================================================
print("\n" + "=" * 80)
print("TEST 3: POST /api/orders WITHOUT email (omit email field)")
print("=" * 80)

try:
    payload = {
        "name": "Ohne Mail",
        "makerworldLink": "https://makerworld.com/de/models/999",
        "model": {
            "filamentGrams": 20,
            "printHours": 1
        },
        "size": 100,
        "quantity": 1,
        "priority": "Normal"
    }
    
    response = requests.post(f"{BASE_URL}/orders", json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get("ok") == True:
            log_pass("No email order - ok: true")
            order_without_email_code = data.get("customerCode")
            order_without_email_number = data.get("orderNumber")
        else:
            log_fail("No email order - ok field", f"Expected ok:true, got {data.get('ok')}")
        
        log_pass("No email order - POST without email (200 OK)")
    else:
        log_fail("No email order - POST without email", f"Expected 200, got {response.status_code}: {response.text}")
        
except Exception as e:
    log_fail("No email order - POST without email", f"Exception: {str(e)}")

# ============================================================================
# TEST 4: GET /api/orders (admin) - Verify email is empty string
# ============================================================================
print("\n" + "=" * 80)
print("TEST 4: GET /api/orders (admin) - Verify email is empty string for order without email")
print("=" * 80)

if admin_token and order_without_email_code:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/orders", headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get("orders", [])
            
            # Find our order by customerCode
            found_order = None
            for order in orders:
                if order.get("customerCode") == order_without_email_code:
                    found_order = order
                    order_without_email_id = order.get("id")
                    break
            
            if found_order:
                log_pass("No email storage - Order found in admin list")
                
                # Verify email field is empty string
                if "email" in found_order:
                    if found_order["email"] == "":
                        log_pass("No email storage - Email is empty string ('')")
                    else:
                        log_fail("No email storage - Email value", f"Expected empty string, got '{found_order['email']}'")
                else:
                    log_fail("No email storage - Email field", "Email field missing in order")
            else:
                log_fail("No email storage - Order not found", f"Could not find order with code {order_without_email_code}")
        else:
            log_fail("No email storage - GET orders", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("No email storage - GET orders", f"Exception: {str(e)}")
else:
    log_fail("No email storage - GET orders", "Missing admin token or order code")

# ============================================================================
# TEST 5: PUT /api/orders/:id status=Abholbereit - With auth
# ============================================================================
print("\n" + "=" * 80)
print("TEST 5: PUT /api/orders/:id status=Abholbereit (triggers pickup email)")
print("=" * 80)

if admin_token and order_with_email_id:
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {"status": "Abholbereit"}
        
        start_time = time.time()
        response = requests.put(f"{BASE_URL}/orders/{order_with_email_id}", json=payload, headers=headers, timeout=10)
        response_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response_time:.3f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get("ok") == True:
                log_pass("Status Abholbereit - ok: true")
            else:
                log_fail("Status Abholbereit - ok field", f"Expected ok:true, got {data.get('ok')}")
            
            if "order" in data and data["order"].get("status") == "Abholbereit":
                log_pass("Status Abholbereit - Status updated correctly")
            else:
                log_fail("Status Abholbereit - Status", f"Expected 'Abholbereit', got {data.get('order', {}).get('status')}")
            
            # Verify quick response (email is async)
            if response_time < 5.0:
                log_pass(f"Status Abholbereit - Quick response ({response_time:.3f}s < 5s, email is async)")
            else:
                log_warning("Status Abholbereit - Response time", f"Response took {response_time:.3f}s (may indicate blocking)")
            
            log_pass("Status Abholbereit - PUT with auth (200 OK)")
        else:
            log_fail("Status Abholbereit - PUT with auth", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Status Abholbereit - PUT with auth", f"Exception: {str(e)}")
else:
    log_fail("Status Abholbereit - PUT with auth", "Missing admin token or order ID")

# ============================================================================
# TEST 6: PUT /api/orders/:id - Without Authorization (401)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 6: PUT /api/orders/:id - Without Authorization (should return 401)")
print("=" * 80)

if order_with_email_id:
    try:
        payload = {"status": "Fertig"}
        response = requests.put(f"{BASE_URL}/orders/{order_with_email_id}", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            log_pass("Auth check - PUT without auth returns 401")
        else:
            log_fail("Auth check - PUT without auth", f"Expected 401, got {response.status_code}")
            
    except Exception as e:
        log_fail("Auth check - PUT without auth", f"Exception: {str(e)}")
else:
    log_fail("Auth check - PUT without auth", "No order ID available")

# ============================================================================
# TEST 7: GET /api/email-status - Without Authorization (401)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 7: GET /api/email-status - Without Authorization (should return 401)")
print("=" * 80)

try:
    response = requests.get(f"{BASE_URL}/email-status", timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 401:
        log_pass("Email status - No auth returns 401")
    else:
        log_fail("Email status - No auth", f"Expected 401, got {response.status_code}")
        
except Exception as e:
    log_fail("Email status - No auth", f"Exception: {str(e)}")

# ============================================================================
# TEST 8: GET /api/email-status - With Authorization (should return ok:true)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 8: GET /api/email-status - With Authorization (SMTP verify)")
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
                log_pass("Email status - SMTP connection verified (ok: true)")
            else:
                log_warning("Email status - SMTP verify", f"SMTP verification failed: {data}")
            
            log_pass("Email status - GET with auth (200 OK)")
        else:
            log_fail("Email status - GET with auth", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Email status - GET with auth", f"Exception: {str(e)}")
else:
    log_fail("Email status - GET with auth", "No admin token available")

# ============================================================================
# TEST 9: Regression - GET /api/orders/track should NOT expose email
# ============================================================================
print("\n" + "=" * 80)
print("TEST 9: Regression - GET /api/orders/track should NOT expose email field")
print("=" * 80)

if order_with_email_code:
    try:
        response = requests.get(f"{BASE_URL}/orders/track?code={order_with_email_code}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            # Verify email field is NOT in public tracking response
            if "email" not in data:
                log_pass("Regression - Email NOT exposed in public tracking")
            else:
                log_fail("Regression - Email exposure", f"Email field should not be in public tracking response, got: {data.get('email')}")
            
            # Verify other fields still work
            required_fields = ["orderNumber", "customerCode", "status", "queueAhead", "customerMessage"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if not missing_fields:
                log_pass("Regression - All required tracking fields present")
            else:
                log_fail("Regression - Missing fields", f"Missing: {missing_fields}")
            
            # Verify orderNumber matches
            if data.get("orderNumber") == order_with_email_number:
                log_pass("Regression - OrderNumber matches")
            else:
                log_fail("Regression - OrderNumber", f"Expected {order_with_email_number}, got {data.get('orderNumber')}")
            
            # Verify customerCode matches
            if data.get("customerCode") == order_with_email_code:
                log_pass("Regression - CustomerCode matches")
            else:
                log_fail("Regression - CustomerCode", f"Expected {order_with_email_code}, got {data.get('customerCode')}")
            
            # Verify status is Abholbereit (from previous test)
            if data.get("status") == "Abholbereit":
                log_pass("Regression - Status correctly shows 'Abholbereit'")
            else:
                log_warning("Regression - Status", f"Expected 'Abholbereit', got {data.get('status')}")
            
            log_pass("Regression - Public tracking (200 OK)")
        else:
            log_fail("Regression - Public tracking", f"Expected 200, got {response.status_code}: {response.text}")
            
    except Exception as e:
        log_fail("Regression - Public tracking", f"Exception: {str(e)}")
else:
    log_fail("Regression - Public tracking", "No order code available")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("EMAIL NOTIFICATION FEATURE - TEST SUMMARY")
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
    print("🎉 ALL EMAIL NOTIFICATION TESTS PASSED!")
    print("\nNOTE: Actual email delivery was already verified manually by main agent.")
    print("These tests verify the API behavior (storage, response times, auth, etc.)")
else:
    print(f"⚠️  {len(test_results['failed'])} TESTS FAILED")
print("=" * 80)
