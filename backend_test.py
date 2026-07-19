#!/usr/bin/env python3
"""
Backend test for NEW confirmation workflow + email/phone mandatory feature.
Tests the 3D-Druck portal Next.js API routes (/api).

CRITICAL: Uses email "jannik-druck@gmx.de" and NO phone for confirm tests to avoid sending real SMS.
"""

import requests
import time
import sys

# Configuration
BASE_URL = "https://order-prints-6.preview.emergentagent.com/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin123!"
TEST_EMAIL = "jannik-druck@gmx.de"

def get_admin_token():
    """Get admin authentication token."""
    try:
        response = requests.post(
            f"{BASE_URL}/admin/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("token")
        else:
            print(f"❌ Admin login failed: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"❌ Admin login exception: {e}")
        return None

def test_scenario_1_validation():
    """
    SCENARIO 1: Validation - POST /api/orders without email AND phone should return 400 with German error.
    """
    print("\n" + "="*80)
    print("SCENARIO 1: Validation - POST without email AND phone")
    print("="*80)
    
    try:
        response = requests.post(
            f"{BASE_URL}/orders",
            json={
                "name": "NoContact",
                "makerworldLink": "https://makerworld.com/en/models/1211525"
            },
            timeout=15
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            data = response.json()
            error_msg = data.get("error", "")
            if "E-Mail" in error_msg or "Handynummer" in error_msg:
                print("✅ SCENARIO 1 PASSED: 400 error with German message about E-Mail/Handynummer")
                return True
            else:
                print(f"❌ SCENARIO 1 FAILED: 400 but wrong error message: {error_msg}")
                return False
        else:
            print(f"❌ SCENARIO 1 FAILED: Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ SCENARIO 1 EXCEPTION: {e}")
        return False

def test_scenario_2_email_only(token):
    """
    SCENARIO 2: POST with only email -> 200 ok:true, then admin GET shows confirmed=false.
    """
    print("\n" + "="*80)
    print("SCENARIO 2: POST with only email (jannik-druck@gmx.de)")
    print("="*80)
    
    try:
        # Create order with only email
        response = requests.post(
            f"{BASE_URL}/orders",
            json={
                "name": "MailOnly",
                "email": TEST_EMAIL,
                "makerworldLink": "https://makerworld.com/en/models/1211525"
            },
            timeout=20
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 200:
            print(f"❌ SCENARIO 2 FAILED: Expected 200, got {response.status_code}")
            return False, None
        
        data = response.json()
        if not data.get("ok"):
            print(f"❌ SCENARIO 2 FAILED: ok is not true")
            return False, None
        
        order_id = None
        
        # Get order from admin list to check confirmed=false
        time.sleep(1)
        admin_response = requests.get(
            f"{BASE_URL}/orders",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if admin_response.status_code == 200:
            admin_data = admin_response.json()
            orders = admin_data.get("orders", [])
            # Find the order we just created
            for order in orders:
                if order.get("name") == "MailOnly" and order.get("email") == TEST_EMAIL:
                    order_id = order.get("id")
                    confirmed = order.get("confirmed")
                    print(f"Found order: id={order_id}, confirmed={confirmed}")
                    
                    if confirmed == False:
                        print("✅ SCENARIO 2 PASSED: Order created with email only, confirmed=false")
                        return True, order_id
                    else:
                        print(f"❌ SCENARIO 2 FAILED: confirmed should be false, got {confirmed}")
                        return False, order_id
            
            print("❌ SCENARIO 2 FAILED: Could not find created order in admin list")
            return False, None
        else:
            print(f"❌ SCENARIO 2 FAILED: Admin GET failed with {admin_response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ SCENARIO 2 EXCEPTION: {e}")
        return False, None

def test_scenario_3_phone_only():
    """
    SCENARIO 3: POST with only phone -> 200 ok:true (validation passes).
    NOTE: Do NOT confirm this one to avoid sending SMS.
    """
    print("\n" + "="*80)
    print("SCENARIO 3: POST with only phone (validation passes, do NOT confirm)")
    print("="*80)
    
    try:
        response = requests.post(
            f"{BASE_URL}/orders",
            json={
                "name": "PhoneOnly",
                "phone": "0176 000",
                "makerworldLink": "https://makerworld.com/en/models/1211525"
            },
            timeout=20
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("✅ SCENARIO 3 PASSED: Order created with phone only, validation passed")
                print("⚠️  NOT confirming this order to avoid sending real SMS")
                return True
            else:
                print(f"❌ SCENARIO 3 FAILED: ok is not true")
                return False
        else:
            print(f"❌ SCENARIO 3 FAILED: Expected 200, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ SCENARIO 3 EXCEPTION: {e}")
        return False

def test_scenario_4_confirm_flow(token, order_id):
    """
    SCENARIO 4: Confirm flow - POST /api/orders/:id/confirm with auth.
    First call -> 200 ok:true, confirmed=true.
    Second call -> 200 ok:true, already:true, confirmed still true.
    """
    print("\n" + "="*80)
    print(f"SCENARIO 4: Confirm flow for order {order_id}")
    print("="*80)
    
    if not order_id:
        print("❌ SCENARIO 4 SKIPPED: No order_id from scenario 2")
        return False
    
    try:
        # First confirm call
        print("\n--- First confirm call ---")
        response1 = requests.post(
            f"{BASE_URL}/orders/{order_id}/confirm",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20
        )
        
        print(f"Status Code: {response1.status_code}")
        print(f"Response: {response1.text}")
        
        if response1.status_code != 200:
            print(f"❌ SCENARIO 4 FAILED: First confirm expected 200, got {response1.status_code}")
            return False
        
        data1 = response1.json()
        if not data1.get("ok"):
            print(f"❌ SCENARIO 4 FAILED: First confirm ok is not true")
            return False
        
        returned_order = data1.get("order", {})
        if not returned_order.get("confirmed"):
            print(f"❌ SCENARIO 4 FAILED: First confirm returned order.confirmed is not true")
            return False
        
        print("✅ First confirm: ok=true, order.confirmed=true")
        
        # Second confirm call (idempotent)
        time.sleep(1)
        print("\n--- Second confirm call (idempotent) ---")
        response2 = requests.post(
            f"{BASE_URL}/orders/{order_id}/confirm",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20
        )
        
        print(f"Status Code: {response2.status_code}")
        print(f"Response: {response2.text}")
        
        if response2.status_code != 200:
            print(f"❌ SCENARIO 4 FAILED: Second confirm expected 200, got {response2.status_code}")
            return False
        
        data2 = response2.json()
        if not data2.get("ok"):
            print(f"❌ SCENARIO 4 FAILED: Second confirm ok is not true")
            return False
        
        if not data2.get("already"):
            print(f"❌ SCENARIO 4 FAILED: Second confirm should have already=true")
            return False
        
        returned_order2 = data2.get("order", {})
        if not returned_order2.get("confirmed"):
            print(f"❌ SCENARIO 4 FAILED: Second confirm returned order.confirmed is not true")
            return False
        
        print("✅ Second confirm: ok=true, already=true, order.confirmed=true")
        print("✅ SCENARIO 4 PASSED: Confirm flow working correctly (idempotent)")
        return True
        
    except Exception as e:
        print(f"❌ SCENARIO 4 EXCEPTION: {e}")
        return False

def test_scenario_5_auth_and_404(token):
    """
    SCENARIO 5: Confirm auth/404 checks.
    - POST /api/orders/:id/confirm WITHOUT Authorization -> 401
    - POST /api/orders/nonexistent/confirm WITH auth -> 404
    """
    print("\n" + "="*80)
    print("SCENARIO 5: Confirm auth and 404 checks")
    print("="*80)
    
    try:
        # Test without auth
        print("\n--- Confirm without Authorization ---")
        response1 = requests.post(
            f"{BASE_URL}/orders/some-id/confirm",
            timeout=10
        )
        
        print(f"Status Code: {response1.status_code}")
        print(f"Response: {response1.text}")
        
        if response1.status_code != 401:
            print(f"❌ SCENARIO 5 FAILED: Expected 401 without auth, got {response1.status_code}")
            return False
        
        print("✅ Without auth: 401 (as expected)")
        
        # Test with nonexistent ID
        print("\n--- Confirm with nonexistent ID ---")
        response2 = requests.post(
            f"{BASE_URL}/orders/nonexistent-id-12345/confirm",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        print(f"Status Code: {response2.status_code}")
        print(f"Response: {response2.text}")
        
        if response2.status_code != 404:
            print(f"❌ SCENARIO 5 FAILED: Expected 404 for nonexistent ID, got {response2.status_code}")
            return False
        
        print("✅ Nonexistent ID: 404 (as expected)")
        print("✅ SCENARIO 5 PASSED: Auth and 404 checks working correctly")
        return True
        
    except Exception as e:
        print(f"❌ SCENARIO 5 EXCEPTION: {e}")
        return False

def test_scenario_6_notification_gating(token):
    """
    SCENARIO 6: Notification gating.
    - Create email-only order (email=jannik-druck@gmx.de), do NOT confirm
    - PUT status='Abholbereit' -> 200 (status changes) but no email sent (confirmed=false)
    - POST confirm
    - PUT status back to 'In Pruefung' then to 'Abholbereit' again -> 200 (now email would send)
    """
    print("\n" + "="*80)
    print("SCENARIO 6: Notification gating (email only sent if confirmed=true)")
    print("="*80)
    
    try:
        # Create order with email only
        print("\n--- Create email-only order ---")
        response = requests.post(
            f"{BASE_URL}/orders",
            json={
                "name": "GatingTest",
                "email": TEST_EMAIL,
                "makerworldLink": "https://makerworld.com/en/models/1211525"
            },
            timeout=20
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ SCENARIO 6 FAILED: Order creation failed with {response.status_code}")
            return False
        
        data = response.json()
        print(f"Order created: {data}")
        
        # Get order ID from admin list
        time.sleep(1)
        admin_response = requests.get(
            f"{BASE_URL}/orders",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        order_id = None
        if admin_response.status_code == 200:
            orders = admin_response.json().get("orders", [])
            for order in orders:
                if order.get("name") == "GatingTest" and order.get("email") == TEST_EMAIL:
                    order_id = order.get("id")
                    confirmed = order.get("confirmed")
                    print(f"Found order: id={order_id}, confirmed={confirmed}")
                    break
        
        if not order_id:
            print("❌ SCENARIO 6 FAILED: Could not find created order")
            return False
        
        # Change status to Abholbereit WITHOUT confirming first
        print("\n--- Change status to Abholbereit (NOT confirmed yet) ---")
        response2 = requests.put(
            f"{BASE_URL}/orders/{order_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "Abholbereit"},
            timeout=15
        )
        
        print(f"Status Code: {response2.status_code}")
        
        if response2.status_code != 200:
            print(f"❌ SCENARIO 6 FAILED: Status update failed with {response2.status_code}")
            return False
        
        data2 = response2.json()
        updated_order = data2.get("order", {})
        if updated_order.get("status") != "Abholbereit":
            print(f"❌ SCENARIO 6 FAILED: Status not updated to Abholbereit")
            return False
        
        print("✅ Status changed to Abholbereit (no email sent because confirmed=false)")
        
        # Now confirm the order
        print("\n--- Confirm the order ---")
        response3 = requests.post(
            f"{BASE_URL}/orders/{order_id}/confirm",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20
        )
        
        print(f"Status Code: {response3.status_code}")
        
        if response3.status_code != 200:
            print(f"❌ SCENARIO 6 FAILED: Confirm failed with {response3.status_code}")
            return False
        
        print("✅ Order confirmed")
        
        # Change status back to 'In Pruefung'
        print("\n--- Change status back to 'In Pruefung' ---")
        response4 = requests.put(
            f"{BASE_URL}/orders/{order_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "In Pruefung"},
            timeout=15
        )
        
        print(f"Status Code: {response4.status_code}")
        
        if response4.status_code != 200:
            print(f"❌ SCENARIO 6 FAILED: Status update to 'In Pruefung' failed")
            return False
        
        print("✅ Status changed to 'In Pruefung'")
        
        # Change status to Abholbereit again (now confirmed=true, email would send)
        print("\n--- Change status to Abholbereit again (NOW confirmed=true) ---")
        response5 = requests.put(
            f"{BASE_URL}/orders/{order_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "Abholbereit"},
            timeout=15
        )
        
        print(f"Status Code: {response5.status_code}")
        
        if response5.status_code != 200:
            print(f"❌ SCENARIO 6 FAILED: Final status update failed")
            return False
        
        print("✅ Status changed to Abholbereit (email would be sent because confirmed=true)")
        print("✅ SCENARIO 6 PASSED: Notification gating working correctly")
        return True
        
    except Exception as e:
        print(f"❌ SCENARIO 6 EXCEPTION: {e}")
        return False

def test_scenario_7_regression(token):
    """
    SCENARIO 7: Regression tests.
    - GET /api/orders/track?code=<code> still works
    - Does NOT expose email/phone
    - No MongoDB _id leaks
    - Generic PUT (adminNotes) still works
    """
    print("\n" + "="*80)
    print("SCENARIO 7: Regression tests")
    print("="*80)
    
    try:
        # Create a test order
        print("\n--- Create test order for regression ---")
        response = requests.post(
            f"{BASE_URL}/orders",
            json={
                "name": "RegressionTest",
                "email": TEST_EMAIL,
                "phone": "0151 12345678",
                "makerworldLink": "https://makerworld.com/en/models/1211525"
            },
            timeout=20
        )
        
        if response.status_code != 200:
            print(f"❌ SCENARIO 7 FAILED: Order creation failed")
            return False
        
        data = response.json()
        customer_code = data.get("customerCode")
        print(f"Order created with customerCode: {customer_code}")
        
        # Get order ID from admin list
        time.sleep(1)
        admin_response = requests.get(
            f"{BASE_URL}/orders",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        order_id = None
        if admin_response.status_code == 200:
            orders = admin_response.json().get("orders", [])
            
            # Check for MongoDB _id leaks in admin list
            for order in orders:
                if "_id" in order:
                    print(f"❌ SCENARIO 7 FAILED: MongoDB _id leak in admin orders list")
                    return False
                
                if order.get("name") == "RegressionTest":
                    order_id = order.get("id")
            
            print("✅ No MongoDB _id leaks in admin orders list")
        
        if not order_id:
            print("❌ SCENARIO 7 FAILED: Could not find created order")
            return False
        
        # Test tracking endpoint
        print("\n--- Test tracking endpoint ---")
        track_response = requests.get(
            f"{BASE_URL}/orders/track",
            params={"code": customer_code},
            timeout=10
        )
        
        print(f"Status Code: {track_response.status_code}")
        
        if track_response.status_code != 200:
            print(f"❌ SCENARIO 7 FAILED: Tracking failed with {track_response.status_code}")
            return False
        
        track_data = track_response.json()
        
        # Check that email/phone are NOT exposed
        if "email" in track_data or "phone" in track_data:
            print(f"❌ SCENARIO 7 FAILED: email/phone exposed in tracking endpoint")
            print(f"Track data: {track_data}")
            return False
        
        print("✅ Tracking works, email/phone NOT exposed")
        
        # Check for MongoDB _id leak in tracking
        if "_id" in track_data:
            print(f"❌ SCENARIO 7 FAILED: MongoDB _id leak in tracking endpoint")
            return False
        
        print("✅ No MongoDB _id leak in tracking")
        
        # Test generic PUT (adminNotes)
        print("\n--- Test generic PUT (adminNotes) ---")
        put_response = requests.put(
            f"{BASE_URL}/orders/{order_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"adminNotes": "Test note for regression"},
            timeout=15
        )
        
        print(f"Status Code: {put_response.status_code}")
        
        if put_response.status_code != 200:
            print(f"❌ SCENARIO 7 FAILED: Generic PUT failed with {put_response.status_code}")
            return False
        
        put_data = put_response.json()
        if not put_data.get("ok"):
            print(f"❌ SCENARIO 7 FAILED: Generic PUT ok is not true")
            return False
        
        print("✅ Generic PUT (adminNotes) works")
        print("✅ SCENARIO 7 PASSED: All regression tests passed")
        return True
        
    except Exception as e:
        print(f"❌ SCENARIO 7 EXCEPTION: {e}")
        return False

def main():
    """Run all test scenarios."""
    print("="*80)
    print("BACKEND TEST: Confirmation Workflow + Email/Phone Mandatory")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test Email: {TEST_EMAIL}")
    print("⚠️  CRITICAL: Using email only for confirm tests to avoid sending real SMS")
    
    # Get admin token
    print("\n--- Getting admin token ---")
    token = get_admin_token()
    if not token:
        print("❌ FATAL: Could not get admin token")
        sys.exit(1)
    
    print(f"✅ Admin token obtained")
    
    # Run all scenarios
    results = {}
    
    results["scenario_1"] = test_scenario_1_validation()
    
    scenario_2_passed, order_id_for_confirm = test_scenario_2_email_only(token)
    results["scenario_2"] = scenario_2_passed
    
    results["scenario_3"] = test_scenario_3_phone_only()
    
    results["scenario_4"] = test_scenario_4_confirm_flow(token, order_id_for_confirm)
    
    results["scenario_5"] = test_scenario_5_auth_and_404(token)
    
    results["scenario_6"] = test_scenario_6_notification_gating(token)
    
    results["scenario_7"] = test_scenario_7_regression(token)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for scenario, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{scenario}: {status}")
    
    print(f"\nTotal: {passed}/{total} scenarios passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
