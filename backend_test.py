#!/usr/bin/env python3
"""
Backend API Test Suite - Vercel-Safe Email Regression
Tests that awaited email sending (with 12s timeout) doesn't break API responses.
"""
import requests
import time
import sys

# Base URL from environment
BASE_URL = "https://order-prints-6.preview.emergentagent.com/api"

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin123!"

# Test email (real GMX address for delivery verification)
TEST_EMAIL = "jannik-druck@gmx.de"

def log(msg):
    print(f"[TEST] {msg}")

def test_admin_login():
    """Get admin token for authenticated requests"""
    log("Testing admin login...")
    try:
        response = requests.post(
            f"{BASE_URL}/admin/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "token" in data, "Token not in response"
        log(f"✅ Admin login successful, token: {data['token'][:20]}...")
        return data["token"]
    except Exception as e:
        log(f"❌ Admin login failed: {e}")
        sys.exit(1)

def test_create_order_with_email(token):
    """
    TEST 1: POST /api/orders with email
    - Should return 200 ok:true with orderNumber+customerCode
    - Response time may be a few seconds (image fetch + awaited emails)
    - MUST complete under ~30s and return 200
    - price MUST be null
    """
    log("\n=== TEST 1: Create order WITH email (awaited confirmation + admin emails) ===")
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/orders",
            json={
                "name": "Vercel Mail Test",
                "email": TEST_EMAIL,
                "makerworldLink": "https://makerworld.com/en/models/1211525",
                "color": "Lila",
                "material": "PLA",
                "size": 100,
                "quantity": 1,
                "priority": "Normal"
            },
            timeout=35  # Allow up to 35s (image fetch + 2x 12s email timeouts)
        )
        elapsed = time.time() - start_time
        
        log(f"Response time: {elapsed:.3f}s")
        assert elapsed < 30, f"Response took too long: {elapsed:.3f}s (must be < 30s)"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("ok") is True, f"Expected ok:true, got {data}"
        assert "orderNumber" in data, "orderNumber not in response"
        assert "customerCode" in data, "customerCode not in response"
        assert data["orderNumber"].startswith("3D-"), f"Invalid orderNumber format: {data['orderNumber']}"
        assert len(data["customerCode"]) == 8, f"customerCode should be 8 chars, got {len(data['customerCode'])}"
        assert data.get("price") is None, f"Expected price=null, got {data.get('price')}"
        
        log(f"✅ Order created successfully in {elapsed:.3f}s")
        log(f"   orderNumber: {data['orderNumber']}")
        log(f"   customerCode: {data['customerCode']}")
        log(f"   price: {data.get('price')} (null as expected)")
        
        # Verify order in admin list
        log("Verifying order in admin list...")
        list_response = requests.get(
            f"{BASE_URL}/orders",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        assert list_response.status_code == 200, f"Expected 200, got {list_response.status_code}"
        orders = list_response.json().get("orders", [])
        order = next((o for o in orders if o["orderNumber"] == data["orderNumber"]), None)
        assert order is not None, f"Order {data['orderNumber']} not found in admin list"
        assert order["email"] == TEST_EMAIL, f"Email mismatch: {order['email']} != {TEST_EMAIL}"
        assert order["price"] is None, f"Expected price=null in DB, got {order['price']}"
        assert "_id" not in order, "MongoDB _id leaked in response"
        log(f"✅ Order verified in admin list, email stored correctly, price=null, no _id leak")
        
        return data["orderNumber"], data["customerCode"], order["id"]
        
    except Exception as e:
        log(f"❌ TEST 1 FAILED: {e}")
        raise

def test_create_order_without_email(token):
    """
    TEST 2: POST /api/orders WITHOUT email
    - Should return 200 ok:true (only admin-info email awaited)
    - Response time should be reasonable
    """
    log("\n=== TEST 2: Create order WITHOUT email (only admin email awaited) ===")
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/orders",
            json={
                "name": "NoMail",
                "makerworldLink": "https://makerworld.com/en/models/1211525"
            },
            timeout=35
        )
        elapsed = time.time() - start_time
        
        log(f"Response time: {elapsed:.3f}s")
        assert elapsed < 30, f"Response took too long: {elapsed:.3f}s (must be < 30s)"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("ok") is True, f"Expected ok:true, got {data}"
        assert "orderNumber" in data, "orderNumber not in response"
        assert "customerCode" in data, "customerCode not in response"
        
        log(f"✅ Order created successfully in {elapsed:.3f}s")
        log(f"   orderNumber: {data['orderNumber']}")
        log(f"   customerCode: {data['customerCode']}")
        
        # Verify email field is empty string
        log("Verifying email field in admin list...")
        list_response = requests.get(
            f"{BASE_URL}/orders",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        assert list_response.status_code == 200, f"Expected 200, got {list_response.status_code}"
        orders = list_response.json().get("orders", [])
        order = next((o for o in orders if o["orderNumber"] == data["orderNumber"]), None)
        assert order is not None, f"Order {data['orderNumber']} not found in admin list"
        assert order["email"] == "", f"Expected empty email, got {order['email']}"
        log(f"✅ Order verified, email field is empty string as expected")
        
        return data["orderNumber"], data["customerCode"], order["id"]
        
    except Exception as e:
        log(f"❌ TEST 2 FAILED: {e}")
        raise

def test_update_status_to_abholbereit(token, order_id):
    """
    TEST 3: Admin PUT /api/orders/<id> {"status":"Abholbereit"}
    - Should return 200 ok:true, status updated
    - Pickup email now awaited — response must still be 200
    - Response time should be reasonable (email awaited with 12s timeout)
    """
    log("\n=== TEST 3: Update status to Abholbereit (pickup email awaited) ===")
    try:
        start_time = time.time()
        response = requests.put(
            f"{BASE_URL}/orders/{order_id}",
            json={"status": "Abholbereit"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=20  # Allow up to 20s (12s email timeout + buffer)
        )
        elapsed = time.time() - start_time
        
        log(f"Response time: {elapsed:.3f}s")
        assert elapsed < 15, f"Response took too long: {elapsed:.3f}s (should be < 15s)"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("ok") is True, f"Expected ok:true, got {data}"
        assert "order" in data, "order not in response"
        assert data["order"]["status"] == "Abholbereit", f"Status not updated: {data['order']['status']}"
        assert "_id" not in data["order"], "MongoDB _id leaked in response"
        
        log(f"✅ Status updated successfully in {elapsed:.3f}s")
        log(f"   status: {data['order']['status']}")
        log(f"   no _id leak")
        
    except Exception as e:
        log(f"❌ TEST 3 FAILED: {e}")
        raise

def test_email_status(token):
    """
    TEST 4: GET /api/email-status with admin auth
    - Should return ok:true
    """
    log("\n=== TEST 4: Email status check ===")
    try:
        response = requests.get(
            f"{BASE_URL}/email-status",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("ok") is True, f"Expected ok:true, got {data}"
        
        log(f"✅ Email status check successful: {data}")
        
    except Exception as e:
        log(f"❌ TEST 4 FAILED: {e}")
        raise

def test_validation():
    """
    TEST 5: Validation still works
    - Missing name -> 400
    - Missing makerworldLink -> 400
    """
    log("\n=== TEST 5: Validation checks ===")
    try:
        # Missing name
        response = requests.post(
            f"{BASE_URL}/orders",
            json={"makerworldLink": "https://makerworld.com/en/models/1211525"},
            timeout=10
        )
        assert response.status_code == 400, f"Expected 400 for missing name, got {response.status_code}"
        log("✅ Missing name returns 400")
        
        # Missing makerworldLink
        response = requests.post(
            f"{BASE_URL}/orders",
            json={"name": "Test"},
            timeout=10
        )
        assert response.status_code == 400, f"Expected 400 for missing link, got {response.status_code}"
        log("✅ Missing makerworldLink returns 400")
        
    except Exception as e:
        log(f"❌ TEST 5 FAILED: {e}")
        raise

def test_auth():
    """
    TEST 6: Auth still works
    - PUT without token -> 401
    """
    log("\n=== TEST 6: Auth checks ===")
    try:
        # Create a dummy order first
        response = requests.post(
            f"{BASE_URL}/orders",
            json={
                "name": "Auth Test",
                "makerworldLink": "https://makerworld.com/en/models/1211525"
            },
            timeout=35
        )
        assert response.status_code == 200, f"Failed to create test order: {response.status_code}"
        order_id = response.json().get("orderNumber")  # We'll use a fake ID for auth test
        
        # Try to update without auth
        response = requests.put(
            f"{BASE_URL}/orders/fake-id-12345",
            json={"status": "Abholbereit"},
            timeout=10
        )
        assert response.status_code == 401, f"Expected 401 for missing auth, got {response.status_code}"
        log("✅ PUT without Authorization returns 401")
        
    except Exception as e:
        log(f"❌ TEST 6 FAILED: {e}")
        raise

def main():
    log("Starting Vercel-Safe Email Regression Tests...")
    log(f"Base URL: {BASE_URL}")
    log(f"Test email: {TEST_EMAIL}")
    
    try:
        # Get admin token
        token = test_admin_login()
        
        # TEST 1: Create order with email (awaited confirmation + admin emails)
        order_number_1, customer_code_1, order_id_1 = test_create_order_with_email(token)
        
        # TEST 2: Create order without email (only admin email awaited)
        order_number_2, customer_code_2, order_id_2 = test_create_order_without_email(token)
        
        # TEST 3: Update status to Abholbereit (pickup email awaited)
        test_update_status_to_abholbereit(token, order_id_1)
        
        # TEST 4: Email status check
        test_email_status(token)
        
        # TEST 5: Validation
        test_validation()
        
        # TEST 6: Auth
        test_auth()
        
        log("\n" + "="*60)
        log("✅ ALL TESTS PASSED")
        log("="*60)
        log("\nSUMMARY:")
        log("- POST /api/orders WITH email: 200 OK, response time < 30s, price=null ✅")
        log("- POST /api/orders WITHOUT email: 200 OK, response time < 30s ✅")
        log("- PUT /api/orders/:id status=Abholbereit: 200 OK, response time < 15s ✅")
        log("- GET /api/email-status: 200 OK, ok:true ✅")
        log("- Validation (missing name/link): 400 ✅")
        log("- Auth (PUT without token): 401 ✅")
        log("- No MongoDB _id leaks ✅")
        log("\nVercel-safe email sending (awaited with 12s timeout) is working correctly!")
        
    except Exception as e:
        log(f"\n❌ TEST SUITE FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
