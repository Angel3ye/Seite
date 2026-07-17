#!/usr/bin/env python3
"""
Backend API Test for 3D-Druck Portal - queueAhead Direction Verification
Tests the UPDATED queueAhead logic where orders with SMALLER sortIndex (older) are counted.
"""

import requests
import time
import sys

# Base URL from environment
BASE_URL = "https://order-prints-6.preview.emergentagent.com/api"

def test_queueahead_direction():
    """
    Test queueAhead direction: oldest (smallest sortIndex) should have queueAhead=0,
    newer orders should have MORE ahead.
    """
    print("\n" + "="*80)
    print("TEST: queueAhead Direction Verification")
    print("="*80)
    
    try:
        # Step 1: Admin login
        print("\n[STEP 1] Admin login...")
        login_resp = requests.post(
            f"{BASE_URL}/admin/login",
            json={"username": "admin", "password": "Admin123!"},
            timeout=10
        )
        print(f"Login status: {login_resp.status_code}")
        if login_resp.status_code != 200:
            print(f"❌ Login failed: {login_resp.text}")
            return False
        
        token = login_resp.json().get("token")
        if not token:
            print("❌ No token in login response")
            return False
        print(f"✅ Login successful, token: {token[:20]}...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Create 3 orders P, Q, R in sequence
        print("\n[STEP 2] Creating 3 orders P, Q, R in sequence...")
        orders = []
        for name in ["P", "Q", "R"]:
            time.sleep(0.5)  # Small delay to ensure different sortIndex
            order_resp = requests.post(
                f"{BASE_URL}/orders",
                json={
                    "name": name,
                    "makerworldLink": "https://makerworld.com/en/models/1211525",
                    "email": ""  # No email to speed up test
                },
                timeout=15
            )
            print(f"Create order {name} status: {order_resp.status_code}")
            if order_resp.status_code != 200:
                print(f"❌ Failed to create order {name}: {order_resp.text}")
                return False
            
            order_data = order_resp.json()
            if not order_data.get("ok"):
                print(f"❌ Order {name} creation returned ok=false")
                return False
            
            orders.append({
                "name": name,
                "orderNumber": order_data.get("orderNumber"),
                "customerCode": order_data.get("customerCode")
            })
            print(f"✅ Order {name} created: {order_data.get('orderNumber')}, code: {order_data.get('customerCode')}")
        
        # Step 3: Get admin list to verify sortIndex order
        print("\n[STEP 3] Getting admin order list to verify sortIndex...")
        list_resp = requests.get(f"{BASE_URL}/orders", headers=headers, timeout=10)
        print(f"Admin list status: {list_resp.status_code}")
        if list_resp.status_code != 200:
            print(f"❌ Failed to get admin list: {list_resp.text}")
            return False
        
        all_orders = list_resp.json().get("orders", [])
        print(f"Total orders in admin list: {len(all_orders)}")
        
        # Debug: print our order codes
        print(f"Looking for orders:")
        for order in orders:
            print(f"  {order['name']}: code={order['customerCode']}")
        
        # Find our orders in the list by customerCode
        order_details = {}
        for order in orders:
            found = next((o for o in all_orders if o["customerCode"] == order["customerCode"]), None)
            if not found:
                print(f"❌ Order {order['name']} (code={order['customerCode']}) not found in admin list")
                print(f"   First 3 order codes in admin list: {[o.get('customerCode', 'NO_CODE') for o in all_orders[:3]]}")
                return False
            order_details[order["name"]] = {
                "id": found["id"],
                "sortIndex": found.get("sortIndex"),
                "customerCode": found["customerCode"],
                "status": found["status"]
            }
            print(f"Order {order['name']}: sortIndex={found.get('sortIndex')}, status={found['status']}")
        
        # Verify sortIndex order: P < Q < R (P oldest, R newest)
        if not (order_details["P"]["sortIndex"] < order_details["Q"]["sortIndex"] < order_details["R"]["sortIndex"]):
            print(f"❌ sortIndex order incorrect: P={order_details['P']['sortIndex']}, Q={order_details['Q']['sortIndex']}, R={order_details['R']['sortIndex']}")
            return False
        print(f"✅ sortIndex order correct: P < Q < R")
        
        # Verify admin list is sorted DESCENDING (R before Q before P)
        our_order_codes = [o["customerCode"] for o in orders]
        our_orders_in_list = [o for o in all_orders if o["customerCode"] in our_order_codes]
        if len(our_orders_in_list) != 3:
            print(f"❌ Expected 3 orders in list, found {len(our_orders_in_list)}")
            return False
        
        # Check if R appears before Q, and Q before P in the list
        r_index = next(i for i, o in enumerate(all_orders) if o["customerCode"] == order_details["R"]["customerCode"])
        q_index = next(i for i, o in enumerate(all_orders) if o["customerCode"] == order_details["Q"]["customerCode"])
        p_index = next(i for i, o in enumerate(all_orders) if o["customerCode"] == order_details["P"]["customerCode"])
        
        if not (r_index < q_index < p_index):
            print(f"❌ Admin list order incorrect: R at {r_index}, Q at {q_index}, P at {p_index}")
            return False
        print(f"✅ Admin list sorted DESCENDING: R (index {r_index}) before Q (index {q_index}) before P (index {p_index})")
        
        # Step 4: Track each order and verify queueAhead
        print("\n[STEP 4] Tracking orders to verify queueAhead...")
        queue_positions = {}
        for order in orders:
            track_resp = requests.get(
                f"{BASE_URL}/orders/track",
                params={"code": order["customerCode"]},
                timeout=10
            )
            print(f"Track {order['name']} status: {track_resp.status_code}")
            if track_resp.status_code != 200:
                print(f"❌ Failed to track order {order['name']}: {track_resp.text}")
                return False
            
            track_data = track_resp.json()
            queue_ahead = track_data.get("queueAhead")
            queue_positions[order["name"]] = queue_ahead
            print(f"Order {order['name']}: queueAhead={queue_ahead}")
            
            # Verify email is NOT exposed
            if "email" in track_data:
                print(f"❌ PRIVACY VIOLATION: email exposed in tracking for order {order['name']}")
                return False
            
            # Verify no MongoDB _id leak
            if "_id" in track_data:
                print(f"❌ SECURITY ISSUE: MongoDB _id exposed in tracking for order {order['name']}")
                return False
        
        print(f"✅ No email or _id leaks in tracking responses")
        
        # Verify queueAhead order: P < Q < R (P oldest = fewest ahead, R newest = most ahead)
        if not (queue_positions["P"] < queue_positions["Q"] < queue_positions["R"]):
            print(f"❌ queueAhead order incorrect: P={queue_positions['P']}, Q={queue_positions['Q']}, R={queue_positions['R']}")
            print(f"   Expected: P < Q < R (older orders have fewer ahead)")
            return False
        print(f"✅ queueAhead order correct: P ({queue_positions['P']}) < Q ({queue_positions['Q']}) < R ({queue_positions['R']})")
        
        # Check if P has queueAhead=0 (if it's the globally oldest open order)
        if queue_positions["P"] == 0:
            print(f"✅ Order P has queueAhead=0 (globally oldest open order)")
        else:
            print(f"ℹ️  Order P has queueAhead={queue_positions['P']} (there are {queue_positions['P']} older open orders)")
        
        # Step 5: Mark P as "Abgeschlossen"
        print("\n[STEP 5] Marking order P as 'Abgeschlossen'...")
        update_resp = requests.put(
            f"{BASE_URL}/orders/{order_details['P']['id']}",
            headers=headers,
            json={"status": "Abgeschlossen"},
            timeout=10
        )
        print(f"Update P status: {update_resp.status_code}")
        if update_resp.status_code != 200:
            print(f"❌ Failed to update order P: {update_resp.text}")
            return False
        
        update_data = update_resp.json()
        if not update_data.get("ok"):
            print(f"❌ Update P returned ok=false")
            return False
        print(f"✅ Order P marked as 'Abgeschlossen'")
        
        # Step 6: Track Q again and verify queueAhead decreased
        print("\n[STEP 6] Tracking order Q again to verify queueAhead decreased...")
        time.sleep(0.5)  # Small delay to ensure update is persisted
        track_q_resp = requests.get(
            f"{BASE_URL}/orders/track",
            params={"code": orders[1]["customerCode"]},
            timeout=10
        )
        print(f"Track Q (after P completed) status: {track_q_resp.status_code}")
        if track_q_resp.status_code != 200:
            print(f"❌ Failed to track order Q: {track_q_resp.text}")
            return False
        
        track_q_data = track_q_resp.json()
        new_queue_ahead_q = track_q_data.get("queueAhead")
        print(f"Order Q queueAhead: before={queue_positions['Q']}, after={new_queue_ahead_q}")
        
        expected_decrease = queue_positions["Q"] - 1
        if new_queue_ahead_q != expected_decrease:
            print(f"❌ queueAhead for Q did not decrease correctly: expected {expected_decrease}, got {new_queue_ahead_q}")
            return False
        print(f"✅ Order Q queueAhead decreased by 1 (from {queue_positions['Q']} to {new_queue_ahead_q})")
        
        # Step 7: Track P and verify queueAhead=0 (completed orders always 0)
        print("\n[STEP 7] Tracking order P (completed) to verify queueAhead=0...")
        track_p_resp = requests.get(
            f"{BASE_URL}/orders/track",
            params={"code": orders[0]["customerCode"]},
            timeout=10
        )
        print(f"Track P (completed) status: {track_p_resp.status_code}")
        if track_p_resp.status_code != 200:
            print(f"❌ Failed to track order P: {track_p_resp.text}")
            return False
        
        track_p_data = track_p_resp.json()
        queue_ahead_p = track_p_data.get("queueAhead")
        print(f"Order P (completed) queueAhead: {queue_ahead_p}")
        
        if queue_ahead_p != 0:
            print(f"❌ Completed order P should have queueAhead=0, got {queue_ahead_p}")
            return False
        print(f"✅ Completed order P has queueAhead=0 (as expected)")
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED: queueAhead direction verified correctly")
        print("="*80)
        print("\nSUMMARY:")
        print(f"  - Admin list sorted by sortIndex DESCENDING (newest on top): ✅")
        print(f"  - queueAhead counts orders with SMALLER sortIndex (older): ✅")
        print(f"  - Order P (oldest) had queueAhead={queue_positions['P']} (smallest): ✅")
        print(f"  - Order Q had queueAhead={queue_positions['Q']} (middle): ✅")
        print(f"  - Order R (newest) had queueAhead={queue_positions['R']} (largest): ✅")
        print(f"  - After P completed, Q's queueAhead decreased by 1: ✅")
        print(f"  - Completed order P has queueAhead=0: ✅")
        print(f"  - No email exposure in tracking: ✅")
        print(f"  - No MongoDB _id leaks: ✅")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_queueahead_direction()
    sys.exit(0 if success else 1)
