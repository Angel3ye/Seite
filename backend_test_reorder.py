#!/usr/bin/env python3
"""
Backend API Test Suite - Order Reorder Feature
Tests the NEW "reorder orders / queue position" backend feature.
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

def test_create_three_orders(token):
    """
    SCENARIO 1: Create 3 fresh orders A, B, C via POST /api/orders
    - Each with name + makerworldLink "https://makerworld.com/en/models/1211525"
    - Status defaults to "Eingegangen"
    - Record their ids, orderNumbers, customerCodes
    """
    log("\n=== SCENARIO 1: Create 3 fresh orders A, B, C ===")
    orders = []
    
    for i, name in enumerate(['Order A', 'Order B', 'Order C']):
        try:
            log(f"Creating {name}...")
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/orders",
                json={
                    "name": name,
                    "email": TEST_EMAIL,
                    "makerworldLink": "https://makerworld.com/en/models/1211525",
                    "color": "Schwarz",
                    "material": "PLA",
                    "size": 100,
                    "quantity": 1,
                    "priority": "Normal"
                },
                timeout=35
            )
            elapsed = time.time() - start_time
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()
            assert data.get("ok") is True, f"Expected ok:true, got {data}"
            assert "orderNumber" in data, "orderNumber not in response"
            assert "customerCode" in data, "customerCode not in response"
            
            log(f"✅ {name} created in {elapsed:.3f}s")
            log(f"   orderNumber: {data['orderNumber']}")
            log(f"   customerCode: {data['customerCode']}")
            
            # Get full order details from admin list to get the id
            list_response = requests.get(
                f"{BASE_URL}/orders",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            assert list_response.status_code == 200, f"Expected 200, got {list_response.status_code}"
            all_orders = list_response.json().get("orders", [])
            order = next((o for o in all_orders if o["orderNumber"] == data["orderNumber"]), None)
            assert order is not None, f"Order {data['orderNumber']} not found in admin list"
            assert order["status"] == "Eingegangen", f"Expected status 'Eingegangen', got {order['status']}"
            
            orders.append({
                "name": name,
                "id": order["id"],
                "orderNumber": data["orderNumber"],
                "customerCode": data["customerCode"],
                "sortIndex": order.get("sortIndex")
            })
            
            log(f"   id: {order['id']}")
            log(f"   sortIndex: {order.get('sortIndex')}")
            
            # Small delay to ensure different sortIndex values (Date.now())
            time.sleep(0.1)
            
        except Exception as e:
            log(f"❌ Failed to create {name}: {e}")
            raise
    
    log(f"✅ SCENARIO 1 PASSED: Created 3 orders A, B, C")
    return orders

def test_get_orders_sorted(token, orders):
    """
    SCENARIO 2: GET /api/orders (admin) -> 200, returns orders sorted by sortIndex ascending
    - Confirm A, B, C appear (newest appended at the END of the queue since sortIndex=Date.now())
    - Note their relative order
    """
    log("\n=== SCENARIO 2: GET /api/orders (admin) - verify sorting by sortIndex ===")
    try:
        response = requests.get(
            f"{BASE_URL}/orders",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "orders" in data, "orders not in response"
        all_orders = data["orders"]
        
        # Find our test orders in the list
        order_a = next((o for o in all_orders if o["id"] == orders[0]["id"]), None)
        order_b = next((o for o in all_orders if o["id"] == orders[1]["id"]), None)
        order_c = next((o for o in all_orders if o["id"] == orders[2]["id"]), None)
        
        assert order_a is not None, "Order A not found in admin list"
        assert order_b is not None, "Order B not found in admin list"
        assert order_c is not None, "Order C not found in admin list"
        
        # Verify sortIndex exists and is numeric
        assert isinstance(order_a.get("sortIndex"), (int, float)), f"Order A sortIndex not numeric: {order_a.get('sortIndex')}"
        assert isinstance(order_b.get("sortIndex"), (int, float)), f"Order B sortIndex not numeric: {order_b.get('sortIndex')}"
        assert isinstance(order_c.get("sortIndex"), (int, float)), f"Order C sortIndex not numeric: {order_c.get('sortIndex')}"
        
        # Verify they are sorted (A < B < C since created in that order)
        assert order_a["sortIndex"] < order_b["sortIndex"], f"Order A should be before B: {order_a['sortIndex']} >= {order_b['sortIndex']}"
        assert order_b["sortIndex"] < order_c["sortIndex"], f"Order B should be before C: {order_b['sortIndex']} >= {order_c['sortIndex']}"
        
        log(f"✅ Orders sorted correctly by sortIndex:")
        log(f"   Order A: sortIndex={order_a['sortIndex']}")
        log(f"   Order B: sortIndex={order_b['sortIndex']}")
        log(f"   Order C: sortIndex={order_c['sortIndex']}")
        log(f"   Relative order: A < B < C ✅")
        
        # Update our orders list with current sortIndex values
        orders[0]["sortIndex"] = order_a["sortIndex"]
        orders[1]["sortIndex"] = order_b["sortIndex"]
        orders[2]["sortIndex"] = order_c["sortIndex"]
        
        log(f"✅ SCENARIO 2 PASSED: GET /api/orders returns orders sorted by sortIndex ascending")
        
    except Exception as e:
        log(f"❌ SCENARIO 2 FAILED: {e}")
        raise

def test_reorder_orders(token, orders):
    """
    SCENARIO 3: Reorder: PUT /api/orders/reorder with Bearer auth
    - body {"orderedIds":[C.id, A.id, B.id]} (some permutation putting C first)
    - Expect 200 ok:true
    - Then GET /api/orders again -> the first three (by sortIndex) must now reflect C, A, B order
    - (C.sortIndex < A.sortIndex < B.sortIndex)
    """
    log("\n=== SCENARIO 3: Reorder orders - PUT /api/orders/reorder ===")
    try:
        # Reorder: C, A, B (putting C first)
        new_order = [orders[2]["id"], orders[0]["id"], orders[1]["id"]]  # C, A, B
        log(f"Reordering to: C, A, B")
        log(f"   orderedIds: {new_order}")
        
        response = requests.put(
            f"{BASE_URL}/orders/reorder",
            json={"orderedIds": new_order},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("ok") is True, f"Expected ok:true, got {data}"
        
        log(f"✅ Reorder request successful: {data}")
        
        # Verify the new order by fetching the list again
        log("Verifying new order with GET /api/orders...")
        list_response = requests.get(
            f"{BASE_URL}/orders",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        assert list_response.status_code == 200, f"Expected 200, got {list_response.status_code}"
        
        all_orders = list_response.json().get("orders", [])
        order_a = next((o for o in all_orders if o["id"] == orders[0]["id"]), None)
        order_b = next((o for o in all_orders if o["id"] == orders[1]["id"]), None)
        order_c = next((o for o in all_orders if o["id"] == orders[2]["id"]), None)
        
        assert order_a is not None, "Order A not found after reorder"
        assert order_b is not None, "Order B not found after reorder"
        assert order_c is not None, "Order C not found after reorder"
        
        # Verify new sortIndex values reflect the new order (C < A < B)
        assert order_c["sortIndex"] < order_a["sortIndex"], f"Order C should be before A: {order_c['sortIndex']} >= {order_a['sortIndex']}"
        assert order_a["sortIndex"] < order_b["sortIndex"], f"Order A should be before B: {order_a['sortIndex']} >= {order_b['sortIndex']}"
        
        log(f"✅ New order verified:")
        log(f"   Order C: sortIndex={order_c['sortIndex']} (was {orders[2]['sortIndex']})")
        log(f"   Order A: sortIndex={order_a['sortIndex']} (was {orders[0]['sortIndex']})")
        log(f"   Order B: sortIndex={order_b['sortIndex']} (was {orders[1]['sortIndex']})")
        log(f"   New relative order: C < A < B ✅")
        
        # Update our orders list with new sortIndex values
        orders[0]["sortIndex"] = order_a["sortIndex"]
        orders[1]["sortIndex"] = order_b["sortIndex"]
        orders[2]["sortIndex"] = order_c["sortIndex"]
        
        log(f"✅ SCENARIO 3 PASSED: Reorder successful, sortIndex updated correctly")
        
    except Exception as e:
        log(f"❌ SCENARIO 3 FAILED: {e}")
        raise

def test_queue_position_reflects_manual_order(token, orders):
    """
    SCENARIO 4: Queue position reflects manual order
    - Pick the order now LAST among these three that is still open (status Eingegangen)
    - GET /api/orders/track?code=<its code> -> queueAhead must equal the number of OPEN orders ahead of it
    - At minimum, verify that after step 3, the order placed FIRST (C) has a SMALLER queueAhead than the order placed later
    - Concretely: track C -> note queueAhead_C; track B -> note queueAhead_B; assert queueAhead_C < queueAhead_B
    """
    log("\n=== SCENARIO 4: Queue position reflects manual order ===")
    try:
        # Track Order C (now first in queue)
        log(f"Tracking Order C (customerCode: {orders[2]['customerCode']})...")
        response_c = requests.get(
            f"{BASE_URL}/orders/track",
            params={"code": orders[2]["customerCode"]},
            timeout=10
        )
        assert response_c.status_code == 200, f"Expected 200, got {response_c.status_code}"
        data_c = response_c.json()
        queueAhead_c = data_c.get("queueAhead")
        assert queueAhead_c is not None, "queueAhead not in response for Order C"
        log(f"✅ Order C queueAhead: {queueAhead_c}")
        
        # Track Order A (now second in queue)
        log(f"Tracking Order A (customerCode: {orders[0]['customerCode']})...")
        response_a = requests.get(
            f"{BASE_URL}/orders/track",
            params={"code": orders[0]["customerCode"]},
            timeout=10
        )
        assert response_a.status_code == 200, f"Expected 200, got {response_a.status_code}"
        data_a = response_a.json()
        queueAhead_a = data_a.get("queueAhead")
        assert queueAhead_a is not None, "queueAhead not in response for Order A"
        log(f"✅ Order A queueAhead: {queueAhead_a}")
        
        # Track Order B (now last in queue)
        log(f"Tracking Order B (customerCode: {orders[1]['customerCode']})...")
        response_b = requests.get(
            f"{BASE_URL}/orders/track",
            params={"code": orders[1]["customerCode"]},
            timeout=10
        )
        assert response_b.status_code == 200, f"Expected 200, got {response_b.status_code}"
        data_b = response_b.json()
        queueAhead_b = data_b.get("queueAhead")
        assert queueAhead_b is not None, "queueAhead not in response for Order B"
        log(f"✅ Order B queueAhead: {queueAhead_b}")
        
        # Verify queueAhead reflects the manual order: C < A < B
        assert queueAhead_c < queueAhead_a, f"Order C should have fewer orders ahead than A: {queueAhead_c} >= {queueAhead_a}"
        assert queueAhead_a < queueAhead_b, f"Order A should have fewer orders ahead than B: {queueAhead_a} >= {queueAhead_b}"
        
        log(f"✅ Queue positions verified:")
        log(f"   Order C (first): queueAhead={queueAhead_c}")
        log(f"   Order A (second): queueAhead={queueAhead_a}")
        log(f"   Order B (last): queueAhead={queueAhead_b}")
        log(f"   Relationship: {queueAhead_c} < {queueAhead_a} < {queueAhead_b} ✅")
        
        log(f"✅ SCENARIO 4 PASSED: Queue position reflects manual order")
        
        # Store queueAhead values for next test
        orders[0]["queueAhead"] = queueAhead_a
        orders[1]["queueAhead"] = queueAhead_b
        orders[2]["queueAhead"] = queueAhead_c
        
    except Exception as e:
        log(f"❌ SCENARIO 4 FAILED: {e}")
        raise

def test_queue_shrinks_when_order_completed(token, orders):
    """
    SCENARIO 5: Change one ahead-order to a done status and re-check queue shrinks
    - As admin PUT /api/orders/<C.id> {"status":"Abgeschlossen"}
    - Then track B again -> queueAhead_B should DECREASE by 1 compared to step 4
    - (since C no longer counts)
    """
    log("\n=== SCENARIO 5: Queue shrinks when ahead-order marked as done ===")
    try:
        # Mark Order C as "Abgeschlossen"
        log(f"Marking Order C (id: {orders[2]['id']}) as 'Abgeschlossen'...")
        response = requests.put(
            f"{BASE_URL}/orders/{orders[2]['id']}",
            json={"status": "Abgeschlossen"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=20
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("ok") is True, f"Expected ok:true, got {data}"
        assert data["order"]["status"] == "Abgeschlossen", f"Status not updated: {data['order']['status']}"
        log(f"✅ Order C marked as 'Abgeschlossen'")
        
        # Track Order B again to verify queueAhead decreased
        log(f"Tracking Order B again (customerCode: {orders[1]['customerCode']})...")
        response_b = requests.get(
            f"{BASE_URL}/orders/track",
            params={"code": orders[1]["customerCode"]},
            timeout=10
        )
        assert response_b.status_code == 200, f"Expected 200, got {response_b.status_code}"
        data_b = response_b.json()
        new_queueAhead_b = data_b.get("queueAhead")
        assert new_queueAhead_b is not None, "queueAhead not in response for Order B"
        
        old_queueAhead_b = orders[1]["queueAhead"]
        log(f"✅ Order B queueAhead: {new_queueAhead_b} (was {old_queueAhead_b})")
        
        # Verify queueAhead decreased by 1 (since C is now done and doesn't count)
        assert new_queueAhead_b == old_queueAhead_b - 1, f"Expected queueAhead to decrease by 1: {new_queueAhead_b} != {old_queueAhead_b - 1}"
        
        log(f"✅ Queue shrunk correctly: queueAhead decreased from {old_queueAhead_b} to {new_queueAhead_b}")
        
        # Also verify Order C now shows queueAhead=0 (since it's completed)
        log(f"Tracking Order C to verify queueAhead=0 (completed orders)...")
        response_c = requests.get(
            f"{BASE_URL}/orders/track",
            params={"code": orders[2]["customerCode"]},
            timeout=10
        )
        assert response_c.status_code == 200, f"Expected 200, got {response_c.status_code}"
        data_c = response_c.json()
        queueAhead_c = data_c.get("queueAhead")
        assert queueAhead_c == 0, f"Expected queueAhead=0 for completed order, got {queueAhead_c}"
        log(f"✅ Order C (completed) shows queueAhead=0 as expected")
        
        log(f"✅ SCENARIO 5 PASSED: Queue shrinks when ahead-order marked as done")
        
    except Exception as e:
        log(f"❌ SCENARIO 5 FAILED: {e}")
        raise

def test_auth_and_validation(token, orders):
    """
    SCENARIO 6: Auth & validation
    - PUT /api/orders/reorder WITHOUT Authorization -> 401
    - PUT /api/orders/reorder with auth but body {} or {"orderedIds":[]} -> 400
    """
    log("\n=== SCENARIO 6: Auth & validation checks ===")
    try:
        # Test 1: PUT /api/orders/reorder WITHOUT Authorization -> 401
        log("Testing PUT /api/orders/reorder without Authorization...")
        response = requests.put(
            f"{BASE_URL}/orders/reorder",
            json={"orderedIds": [orders[0]["id"], orders[1]["id"]]},
            timeout=10
        )
        assert response.status_code == 401, f"Expected 401 for missing auth, got {response.status_code}"
        log(f"✅ PUT /api/orders/reorder without Authorization returns 401")
        
        # Test 2: PUT /api/orders/reorder with auth but empty body -> 400
        log("Testing PUT /api/orders/reorder with empty body...")
        response = requests.put(
            f"{BASE_URL}/orders/reorder",
            json={},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        assert response.status_code == 400, f"Expected 400 for empty body, got {response.status_code}"
        log(f"✅ PUT /api/orders/reorder with empty body returns 400")
        
        # Test 3: PUT /api/orders/reorder with auth but empty orderedIds array -> 400
        log("Testing PUT /api/orders/reorder with empty orderedIds array...")
        response = requests.put(
            f"{BASE_URL}/orders/reorder",
            json={"orderedIds": []},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        assert response.status_code == 400, f"Expected 400 for empty orderedIds, got {response.status_code}"
        log(f"✅ PUT /api/orders/reorder with empty orderedIds returns 400")
        
        log(f"✅ SCENARIO 6 PASSED: Auth & validation checks working correctly")
        
    except Exception as e:
        log(f"❌ SCENARIO 6 FAILED: {e}")
        raise

def test_regression(token, orders):
    """
    SCENARIO 7: Regression checks
    - No MongoDB _id leaks
    - GET /api/orders/track does NOT expose email
    - Existing single-order PUT (status/model) still works (200)
    - Reorder route does not clash with the generic PUT /api/orders/:id
    """
    log("\n=== SCENARIO 7: Regression checks ===")
    try:
        # Test 1: No MongoDB _id leaks in GET /api/orders
        log("Testing no MongoDB _id leaks in GET /api/orders...")
        response = requests.get(
            f"{BASE_URL}/orders",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        all_orders = response.json().get("orders", [])
        for order in all_orders:
            assert "_id" not in order, f"MongoDB _id leaked in order: {order.get('orderNumber')}"
        log(f"✅ No MongoDB _id leaks in GET /api/orders")
        
        # Test 2: GET /api/orders/track does NOT expose email
        log("Testing GET /api/orders/track does not expose email...")
        response = requests.get(
            f"{BASE_URL}/orders/track",
            params={"code": orders[0]["customerCode"]},
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "email" not in data, f"Email exposed in tracking response: {data}"
        log(f"✅ GET /api/orders/track does NOT expose email (privacy maintained)")
        
        # Test 3: Existing single-order PUT (status/model) still works
        log("Testing existing PUT /api/orders/:id (status update)...")
        response = requests.put(
            f"{BASE_URL}/orders/{orders[0]['id']}",
            json={"status": "In Pruefung"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=20
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("ok") is True, f"Expected ok:true, got {data}"
        assert data["order"]["status"] == "In Pruefung", f"Status not updated: {data['order']['status']}"
        log(f"✅ Existing PUT /api/orders/:id (status update) still works")
        
        # Test 4: PUT /api/orders/:id with model update still works
        log("Testing existing PUT /api/orders/:id (model update)...")
        response = requests.put(
            f"{BASE_URL}/orders/{orders[0]['id']}",
            json={"model": {"filamentGrams": 50, "printHours": 4}},
            headers={"Authorization": f"Bearer {token}"},
            timeout=20
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("ok") is True, f"Expected ok:true, got {data}"
        assert data["order"]["model"]["filamentGrams"] == 50, f"filamentGrams not updated: {data['order']['model']}"
        assert data["order"]["model"]["printHours"] == 4, f"printHours not updated: {data['order']['model']}"
        # Verify price was calculated (since we set grams/hours)
        assert data["order"]["price"] is not None, f"Price should be calculated after setting grams/hours"
        assert data["order"]["price"]["total"] > 0, f"Price total should be > 0: {data['order']['price']['total']}"
        log(f"✅ Existing PUT /api/orders/:id (model update) still works, price calculated correctly")
        
        # Test 5: Verify reorder route does not clash with generic PUT /api/orders/:id
        log("Testing reorder route does not clash with generic PUT /api/orders/:id...")
        # This is implicitly tested by the above tests, but let's be explicit
        # Try to PUT to /api/orders/reorder with a valid order ID (should still hit reorder endpoint)
        response = requests.put(
            f"{BASE_URL}/orders/reorder",
            json={"orderedIds": [orders[0]["id"], orders[1]["id"]]},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("ok") is True, f"Expected ok:true, got {data}"
        log(f"✅ Reorder route does not clash with generic PUT /api/orders/:id")
        
        log(f"✅ SCENARIO 7 PASSED: All regression checks passed")
        
    except Exception as e:
        log(f"❌ SCENARIO 7 FAILED: {e}")
        raise

def main():
    log("Starting Order Reorder Feature Tests...")
    log(f"Base URL: {BASE_URL}")
    log(f"Test email: {TEST_EMAIL}")
    
    try:
        # Get admin token
        token = test_admin_login()
        
        # SCENARIO 1: Create 3 fresh orders A, B, C
        orders = test_create_three_orders(token)
        
        # SCENARIO 2: GET /api/orders (admin) - verify sorting by sortIndex
        test_get_orders_sorted(token, orders)
        
        # SCENARIO 3: Reorder orders - PUT /api/orders/reorder
        test_reorder_orders(token, orders)
        
        # SCENARIO 4: Queue position reflects manual order
        test_queue_position_reflects_manual_order(token, orders)
        
        # SCENARIO 5: Queue shrinks when ahead-order marked as done
        test_queue_shrinks_when_order_completed(token, orders)
        
        # SCENARIO 6: Auth & validation checks
        test_auth_and_validation(token, orders)
        
        # SCENARIO 7: Regression checks
        test_regression(token, orders)
        
        log("\n" + "="*60)
        log("✅ ALL TESTS PASSED")
        log("="*60)
        log("\nSUMMARY:")
        log("✅ SCENARIO 1: Created 3 orders A, B, C with sortIndex")
        log("✅ SCENARIO 2: GET /api/orders returns orders sorted by sortIndex ascending")
        log("✅ SCENARIO 3: PUT /api/orders/reorder successfully reordered to C, A, B")
        log("✅ SCENARIO 4: Queue position (queueAhead) reflects manual order")
        log("✅ SCENARIO 5: Queue shrinks when ahead-order marked as done")
        log("✅ SCENARIO 6: Auth & validation working (401 without auth, 400 for empty body)")
        log("✅ SCENARIO 7: Regression checks passed (no _id leaks, email not exposed, existing PUT works)")
        log("\nOrder reorder feature is working correctly!")
        
    except Exception as e:
        log(f"\n❌ TEST SUITE FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
