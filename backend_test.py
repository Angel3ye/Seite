#!/usr/bin/env python3
"""
Backend test for SMS notification feature (3D-Druck portal)
⚠️ CRITICAL: DO NOT SEND REAL SMS - costs real money & reaches real people
"""
import requests
import json
import time

BASE_URL = "https://order-prints-6.preview.emergentagent.com/api"

def get_admin_token():
    """Login as admin and get Bearer token"""
    response = requests.post(f"{BASE_URL}/admin/login", json={
        "username": "admin",
        "password": "Admin123!"
    })
    if response.status_code == 200:
        return response.json().get("token")
    raise Exception(f"Admin login failed: {response.status_code} {response.text}")

def test_scenario_1_sms_config_check():
    """Scenario 1: SMS config check - GET /api/sms-status WITH admin Bearer -> 200 {ok:true}, WITHOUT -> 401"""
    print("\n" + "="*80)
    print("SCENARIO 1: SMS Config Check")
    print("="*80)
    
    try:
        # Test WITHOUT Authorization -> expect 401
        print("\n[1a] Testing GET /api/sms-status WITHOUT Authorization...")
        response = requests.get(f"{BASE_URL}/sms-status")
        if response.status_code == 401:
            print(f"✅ PASS: Without auth returned 401 (as expected)")
        else:
            print(f"❌ FAIL: Without auth returned {response.status_code}, expected 401")
            print(f"Response: {response.text}")
            return False
        
        # Test WITH Authorization -> expect 200 {ok:true}
        print("\n[1b] Testing GET /api/sms-status WITH admin Bearer token...")
        token = get_admin_token()
        response = requests.get(f"{BASE_URL}/sms-status", headers={
            "Authorization": f"Bearer {token}"
        })
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") == True:
                print(f"✅ PASS: With auth returned 200 with ok:true (SMS gateway credentials valid)")
                print(f"Response: {json.dumps(data, indent=2)}")
            else:
                print(f"❌ FAIL: With auth returned 200 but ok is not true")
                print(f"Response: {json.dumps(data, indent=2)}")
                return False
        else:
            print(f"❌ FAIL: With auth returned {response.status_code}, expected 200")
            print(f"Response: {response.text}")
            return False
        
        print("\n✅ SCENARIO 1 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ SCENARIO 1 FAILED with exception: {e}")
        return False

def test_scenario_2_order_without_phone():
    """Scenario 2: Order without phone - POST /api/orders (NO phone, NO email) -> 200 ok:true"""
    print("\n" + "="*80)
    print("SCENARIO 2: Create Order WITHOUT Phone")
    print("="*80)
    
    try:
        print("\n[2] Creating order WITHOUT phone and WITHOUT email...")
        response = requests.post(f"{BASE_URL}/orders", json={
            "name": "SMS Feld Test",
            "makerworldLink": "https://makerworld.com/en/models/1211525",
            "size": 100,
            "quantity": 1,
            "priority": "Normal"
            # NO phone, NO email
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") == True:
                order_id = data.get("orderNumber")  # We'll use customerCode for tracking
                customer_code = data.get("customerCode")
                print(f"✅ PASS: Order created successfully")
                print(f"Order Number: {order_id}")
                print(f"Customer Code: {customer_code}")
                print(f"Response: {json.dumps(data, indent=2)}")
                
                # Return the customer code for use in later tests
                return customer_code
            else:
                print(f"❌ FAIL: Response ok is not true")
                print(f"Response: {json.dumps(data, indent=2)}")
                return None
        else:
            print(f"❌ FAIL: Order creation returned {response.status_code}, expected 200")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ SCENARIO 2 FAILED with exception: {e}")
        return None

def test_scenario_3_phone_stored_via_field_update(customer_code):
    """Scenario 3: Phone stored via field update (NO SMS triggered) - PUT /api/orders/<id> with phone"""
    print("\n" + "="*80)
    print("SCENARIO 3: Store Phone via Field Update (NO SMS)")
    print("="*80)
    
    try:
        # First, get the order ID from customer code
        print(f"\n[3a] Getting order details for customer code: {customer_code}")
        token = get_admin_token()
        response = requests.get(f"{BASE_URL}/orders", headers={
            "Authorization": f"Bearer {token}"
        })
        
        if response.status_code != 200:
            print(f"❌ FAIL: Could not get orders list: {response.status_code}")
            return False
        
        orders = response.json().get("orders", [])
        order = next((o for o in orders if o.get("customerCode") == customer_code), None)
        
        if not order:
            print(f"❌ FAIL: Could not find order with customer code {customer_code}")
            return False
        
        order_id = order.get("id")
        print(f"Found order ID: {order_id}")
        
        # Update the order with phone field (NO status change)
        print(f"\n[3b] Updating order {order_id} with phone field...")
        response = requests.put(f"{BASE_URL}/orders/{order_id}", 
            headers={"Authorization": f"Bearer {token}"},
            json={"phone": "0151 23456789"}  # IMPORTANT: NO status change
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") == True:
                returned_order = data.get("order", {})
                returned_phone = returned_order.get("phone")
                if returned_phone == "0151 23456789":
                    print(f"✅ PASS: Phone stored successfully in response")
                    print(f"Phone in response: {returned_phone}")
                else:
                    print(f"❌ FAIL: Phone in response is '{returned_phone}', expected '0151 23456789'")
                    return False
                
                # Verify via admin GET /api/orders
                print(f"\n[3c] Verifying phone via admin GET /api/orders...")
                response = requests.get(f"{BASE_URL}/orders", headers={
                    "Authorization": f"Bearer {token}"
                })
                orders = response.json().get("orders", [])
                order = next((o for o in orders if o.get("id") == order_id), None)
                
                if order and order.get("phone") == "0151 23456789":
                    print(f"✅ PASS: Phone verified in admin orders list")
                    print(f"Phone in admin list: {order.get('phone')}")
                    print("\n✅ SCENARIO 3 PASSED")
                    return order_id  # Return order_id for next tests
                else:
                    print(f"❌ FAIL: Phone not found or incorrect in admin orders list")
                    print(f"Phone in admin list: {order.get('phone') if order else 'order not found'}")
                    return False
            else:
                print(f"❌ FAIL: Response ok is not true")
                print(f"Response: {json.dumps(data, indent=2)}")
                return False
        else:
            print(f"❌ FAIL: Update returned {response.status_code}, expected 200")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ SCENARIO 3 FAILED with exception: {e}")
        return False

def test_scenario_4_clear_phone(order_id):
    """Scenario 4: Clear phone - PUT /api/orders/<id> {"phone":""} -> 200, phone empty"""
    print("\n" + "="*80)
    print("SCENARIO 4: Clear Phone Field")
    print("="*80)
    
    try:
        print(f"\n[4] Clearing phone field for order {order_id}...")
        token = get_admin_token()
        response = requests.put(f"{BASE_URL}/orders/{order_id}", 
            headers={"Authorization": f"Bearer {token}"},
            json={"phone": ""}
        )
        
        if response.status_code == 200:
            data = response.json()
            returned_order = data.get("order", {})
            returned_phone = returned_order.get("phone")
            if returned_phone == "":
                print(f"✅ PASS: Phone cleared successfully (empty string)")
                print(f"Phone in response: '{returned_phone}'")
                print("\n✅ SCENARIO 4 PASSED")
                return True
            else:
                print(f"❌ FAIL: Phone is '{returned_phone}', expected empty string")
                return False
        else:
            print(f"❌ FAIL: Update returned {response.status_code}, expected 200")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ SCENARIO 4 FAILED with exception: {e}")
        return False

def test_scenario_5_email_alongside(order_id):
    """Scenario 5: Email still works alongside - PUT /api/orders/<id> {"email":"..."} -> 200"""
    print("\n" + "="*80)
    print("SCENARIO 5: Email Works Alongside Phone")
    print("="*80)
    
    try:
        print(f"\n[5] Setting email field for order {order_id}...")
        token = get_admin_token()
        response = requests.put(f"{BASE_URL}/orders/{order_id}", 
            headers={"Authorization": f"Bearer {token}"},
            json={"email": "jannik-druck@gmx.de"}  # NO status change
        )
        
        if response.status_code == 200:
            data = response.json()
            returned_order = data.get("order", {})
            returned_email = returned_order.get("email")
            if returned_email == "jannik-druck@gmx.de":
                print(f"✅ PASS: Email set successfully")
                print(f"Email in response: {returned_email}")
                print("\n✅ SCENARIO 5 PASSED")
                return True
            else:
                print(f"❌ FAIL: Email is '{returned_email}', expected 'jannik-druck@gmx.de'")
                return False
        else:
            print(f"❌ FAIL: Update returned {response.status_code}, expected 200")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ SCENARIO 5 FAILED with exception: {e}")
        return False

def test_scenario_6_privacy(customer_code):
    """Scenario 6: Privacy - GET /api/orders/track?code=<code> must NOT contain phone or email"""
    print("\n" + "="*80)
    print("SCENARIO 6: Privacy Check (No Phone/Email in Tracking)")
    print("="*80)
    
    try:
        print(f"\n[6] Getting tracking info for customer code: {customer_code}")
        response = requests.get(f"{BASE_URL}/orders/track?code={customer_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Tracking response: {json.dumps(data, indent=2)}")
            
            # Check that phone and email are NOT in the response
            if "phone" in data:
                print(f"❌ FAIL: 'phone' field found in tracking response (privacy violation)")
                return False
            if "email" in data:
                print(f"❌ FAIL: 'email' field found in tracking response (privacy violation)")
                return False
            
            print(f"✅ PASS: Neither 'phone' nor 'email' fields found in tracking response (privacy maintained)")
            print("\n✅ SCENARIO 6 PASSED")
            return True
        else:
            print(f"❌ FAIL: Tracking returned {response.status_code}, expected 200")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ SCENARIO 6 FAILED with exception: {e}")
        return False

def test_scenario_7_regression(order_id):
    """Scenario 7: Regression - no MongoDB _id leaks, generic PUT works, order creation quick"""
    print("\n" + "="*80)
    print("SCENARIO 7: Regression Tests")
    print("="*80)
    
    try:
        token = get_admin_token()
        
        # Test 7a: No MongoDB _id leaks in admin orders list
        print("\n[7a] Checking for MongoDB _id leaks in admin orders list...")
        response = requests.get(f"{BASE_URL}/orders", headers={
            "Authorization": f"Bearer {token}"
        })
        if response.status_code == 200:
            orders = response.json().get("orders", [])
            has_mongo_id = any("_id" in order for order in orders)
            if has_mongo_id:
                print(f"❌ FAIL: MongoDB _id found in orders list")
                return False
            else:
                print(f"✅ PASS: No MongoDB _id leaks in orders list")
        else:
            print(f"❌ FAIL: Could not get orders list: {response.status_code}")
            return False
        
        # Test 7b: Generic PUT (e.g. adminNotes) still returns 200
        print(f"\n[7b] Testing generic PUT with adminNotes...")
        response = requests.put(f"{BASE_URL}/orders/{order_id}", 
            headers={"Authorization": f"Bearer {token}"},
            json={"adminNotes": "test regression"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") == True:
                print(f"✅ PASS: Generic PUT (adminNotes) returned 200 ok:true")
            else:
                print(f"❌ FAIL: Generic PUT returned 200 but ok is not true")
                return False
        else:
            print(f"❌ FAIL: Generic PUT returned {response.status_code}, expected 200")
            return False
        
        # Test 7c: Creating an order still returns quickly
        print(f"\n[7c] Testing order creation speed...")
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/orders", json={
            "name": "Speed Test Order",
            "makerworldLink": "https://makerworld.com/en/models/1211525",
            "size": 100,
            "quantity": 1,
            "priority": "Normal"
        })
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") == True:
                print(f"✅ PASS: Order created successfully in {elapsed:.3f}s")
                if elapsed > 30:
                    print(f"⚠️  WARNING: Order creation took {elapsed:.3f}s (>30s may timeout on serverless)")
            else:
                print(f"❌ FAIL: Order creation ok is not true")
                return False
        else:
            print(f"❌ FAIL: Order creation returned {response.status_code}, expected 200")
            return False
        
        print("\n✅ SCENARIO 7 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ SCENARIO 7 FAILED with exception: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("SMS NOTIFICATION BACKEND TESTING")
    print("⚠️  CRITICAL: NO REAL SMS WILL BE SENT (testing field storage & config only)")
    print("="*80)
    
    results = {}
    
    # Scenario 1: SMS config check
    results["scenario_1"] = test_scenario_1_sms_config_check()
    
    # Scenario 2: Create order without phone
    customer_code = test_scenario_2_order_without_phone()
    results["scenario_2"] = customer_code is not None
    
    if customer_code:
        # Scenario 3: Store phone via field update
        order_id = test_scenario_3_phone_stored_via_field_update(customer_code)
        results["scenario_3"] = order_id is not False and order_id is not None
        
        if order_id:
            # Scenario 4: Clear phone
            results["scenario_4"] = test_scenario_4_clear_phone(order_id)
            
            # Scenario 5: Email alongside
            results["scenario_5"] = test_scenario_5_email_alongside(order_id)
            
            # Scenario 6: Privacy check
            results["scenario_6"] = test_scenario_6_privacy(customer_code)
            
            # Scenario 7: Regression tests
            results["scenario_7"] = test_scenario_7_regression(order_id)
        else:
            print("\n⚠️  Skipping scenarios 4-7 due to scenario 3 failure")
            results["scenario_4"] = False
            results["scenario_5"] = False
            results["scenario_6"] = False
            results["scenario_7"] = False
    else:
        print("\n⚠️  Skipping scenarios 3-7 due to scenario 2 failure")
        results["scenario_3"] = False
        results["scenario_4"] = False
        results["scenario_5"] = False
        results["scenario_6"] = False
        results["scenario_7"] = False
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for scenario, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{scenario.replace('_', ' ').title()}: {status}")
    
    print(f"\nTotal: {passed}/{total} scenarios passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())
