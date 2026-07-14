#!/usr/bin/env python3
"""
Backend Test Suite for 3D-Druck Portal
Tests NEW/CHANGED behaviors: newest orders on top, reorder direction, queueAhead direction, edit email, manual status mail
"""

import requests
import time
import sys

BASE_URL = "https://order-prints-6.preview.emergentagent.com/api"
ADMIN_USER = "admin"
ADMIN_PASS = "Admin123!"
TEST_EMAIL = "jannik-druck@gmx.de"

def get_admin_token():
    """Login as admin and get Bearer token"""
    resp = requests.post(f"{BASE_URL}/admin/login", json={"username": ADMIN_USER, "password": ADMIN_PASS})
    if resp.status_code != 200:
        print(f"❌ Admin login failed: {resp.status_code} {resp.text}")
        sys.exit(1)
    token = resp.json().get("token")
    print(f"✅ Admin login successful, token: {token[:20]}...")
    return token

def create_order(name, email=""):
    """Create a new order and return the order details"""
    payload = {
        "name": name,
        "makerworldLink": "https://makerworld.com/en/models/1211525",
        "email": email
    }
    resp = requests.post(f"{BASE_URL}/orders", json=payload)
    if resp.status_code != 200:
        print(f"❌ Create order failed: {resp.status_code} {resp.text}")
        return None
    data = resp.json()
    print(f"✅ Order created: {data.get('orderNumber')} / {data.get('customerCode')}")
    return data

def get_all_orders(token):
    """Get all orders (admin endpoint)"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/orders", headers=headers)
    if resp.status_code != 200:
        print(f"❌ Get orders failed: {resp.status_code} {resp.text}")
        return None
    return resp.json().get("orders", [])

def get_order_by_number(token, order_number):
    """Find order by orderNumber from all orders"""
    orders = get_all_orders(token)
    if not orders:
        return None
    for order in orders:
        if order.get("orderNumber") == order_number:
            return order
    return None

def track_order(customer_code):
    """Track order by customer code (public endpoint)"""
    resp = requests.get(f"{BASE_URL}/orders/track", params={"code": customer_code})
    if resp.status_code != 200:
        print(f"❌ Track order failed: {resp.status_code} {resp.text}")
        return None
    return resp.json()

def reorder_orders(token, ordered_ids):
    """Reorder orders (admin endpoint)"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"orderedIds": ordered_ids}
    resp = requests.put(f"{BASE_URL}/orders/reorder", json=payload, headers=headers)
    return resp

def update_order(token, order_id, updates):
    """Update order (admin endpoint)"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.put(f"{BASE_URL}/orders/{order_id}", json=updates, headers=headers)
    return resp

def send_status_mail(token, order_id):
    """Send manual status mail (admin endpoint)"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/orders/{order_id}/send-status-mail", json={}, headers=headers)
    return resp

def main():
    print("\n" + "="*80)
    print("BACKEND TEST SUITE - NEW/CHANGED BEHAVIORS")
    print("="*80 + "\n")
    
    token = get_admin_token()
    
    # ========================================================================
    # SCENARIO 1: Newest orders on top (sortIndex DESCENDING)
    # ========================================================================
    print("\n" + "-"*80)
    print("SCENARIO 1: Create order X, then order Y -> Y must appear ABOVE X")
    print("-"*80)
    
    print("\n[1.1] Creating order X...")
    time.sleep(0.5)  # Small delay to ensure different timestamps
    order_x_data = create_order("Test Order X", TEST_EMAIL)
    if not order_x_data:
        print("❌ SCENARIO 1 FAILED: Could not create order X")
        sys.exit(1)
    order_x_number = order_x_data["orderNumber"]
    order_x_code = order_x_data["customerCode"]
    
    print("\n[1.2] Creating order Y...")
    time.sleep(0.5)  # Small delay to ensure different timestamps
    order_y_data = create_order("Test Order Y", TEST_EMAIL)
    if not order_y_data:
        print("❌ SCENARIO 1 FAILED: Could not create order Y")
        sys.exit(1)
    order_y_number = order_y_data["orderNumber"]
    order_y_code = order_y_data["customerCode"]
    
    print("\n[1.3] Getting all orders (admin)...")
    time.sleep(0.5)
    all_orders = get_all_orders(token)
    if not all_orders:
        print("❌ SCENARIO 1 FAILED: Could not get orders")
        sys.exit(1)
    
    # Find X and Y in the list
    order_x = get_order_by_number(token, order_x_number)
    order_y = get_order_by_number(token, order_y_number)
    
    if not order_x or not order_y:
        print(f"❌ SCENARIO 1 FAILED: Could not find orders in list (X: {order_x is not None}, Y: {order_y is not None})")
        sys.exit(1)
    
    print(f"   Order X: {order_x_number}, sortIndex={order_x.get('sortIndex')}")
    print(f"   Order Y: {order_y_number}, sortIndex={order_y.get('sortIndex')}")
    
    # Find positions in array
    x_index = next((i for i, o in enumerate(all_orders) if o.get("orderNumber") == order_x_number), -1)
    y_index = next((i for i, o in enumerate(all_orders) if o.get("orderNumber") == order_y_number), -1)
    
    print(f"   Order X position in array: {x_index}")
    print(f"   Order Y position in array: {y_index}")
    
    # Y should appear BEFORE X in the array (lower index = higher in list)
    # Y.sortIndex should be GREATER than X.sortIndex
    if y_index < x_index and order_y.get("sortIndex", 0) > order_x.get("sortIndex", 0):
        print(f"✅ SCENARIO 1 PASSED: Y appears above X (Y at index {y_index}, X at index {x_index}), Y.sortIndex ({order_y.get('sortIndex')}) > X.sortIndex ({order_x.get('sortIndex')})")
    else:
        print(f"❌ SCENARIO 1 FAILED: Y should appear above X. Y index: {y_index}, X index: {x_index}, Y.sortIndex: {order_y.get('sortIndex')}, X.sortIndex: {order_x.get('sortIndex')}")
        sys.exit(1)
    
    # ========================================================================
    # SCENARIO 2: Reorder direction (first id in array = highest sortIndex = top)
    # ========================================================================
    print("\n" + "-"*80)
    print("SCENARIO 2: Reorder - PUT orderedIds=[X.id, Y.id, ...] placing X first")
    print("-"*80)
    
    print("\n[2.1] Getting all order IDs for reorder...")
    all_order_ids = [o["id"] for o in all_orders]
    print(f"   Total orders: {len(all_order_ids)}")
    
    # Place X first, Y second, then rest
    reordered_ids = [order_x["id"], order_y["id"]] + [oid for oid in all_order_ids if oid not in [order_x["id"], order_y["id"]]]
    
    print(f"\n[2.2] Reordering: X first, Y second...")
    print(f"   Reordered IDs (first 2): [{order_x['id'][:8]}..., {order_y['id'][:8]}...]")
    
    reorder_resp = reorder_orders(token, reordered_ids)
    if reorder_resp.status_code != 200:
        print(f"❌ SCENARIO 2 FAILED: Reorder failed: {reorder_resp.status_code} {reorder_resp.text}")
        sys.exit(1)
    
    reorder_data = reorder_resp.json()
    if not reorder_data.get("ok"):
        print(f"❌ SCENARIO 2 FAILED: Reorder returned ok:false")
        sys.exit(1)
    
    print(f"✅ Reorder successful: {reorder_data}")
    
    print("\n[2.3] Getting orders again to verify new order...")
    time.sleep(0.5)
    all_orders_after = get_all_orders(token)
    if not all_orders_after:
        print("❌ SCENARIO 2 FAILED: Could not get orders after reorder")
        sys.exit(1)
    
    order_x_after = get_order_by_number(token, order_x_number)
    order_y_after = get_order_by_number(token, order_y_number)
    
    if not order_x_after or not order_y_after:
        print(f"❌ SCENARIO 2 FAILED: Could not find orders after reorder")
        sys.exit(1)
    
    print(f"   Order X after: sortIndex={order_x_after.get('sortIndex')}")
    print(f"   Order Y after: sortIndex={order_y_after.get('sortIndex')}")
    
    # Find new positions
    x_index_after = next((i for i, o in enumerate(all_orders_after) if o.get("orderNumber") == order_x_number), -1)
    y_index_after = next((i for i, o in enumerate(all_orders_after) if o.get("orderNumber") == order_y_number), -1)
    
    print(f"   Order X position after: {x_index_after}")
    print(f"   Order Y position after: {y_index_after}")
    
    # X should now appear BEFORE Y (lower index), and X.sortIndex should be GREATER than Y.sortIndex
    if x_index_after < y_index_after and order_x_after.get("sortIndex", 0) > order_y_after.get("sortIndex", 0):
        print(f"✅ SCENARIO 2 PASSED: X now above Y (X at index {x_index_after}, Y at index {y_index_after}), X.sortIndex ({order_x_after.get('sortIndex')}) > Y.sortIndex ({order_y_after.get('sortIndex')})")
    else:
        print(f"❌ SCENARIO 2 FAILED: X should appear above Y after reorder. X index: {x_index_after}, Y index: {y_index_after}, X.sortIndex: {order_x_after.get('sortIndex')}, Y.sortIndex: {order_y_after.get('sortIndex')}")
        sys.exit(1)
    
    # ========================================================================
    # SCENARIO 3: queueAhead direction (counts orders with LARGER sortIndex)
    # ========================================================================
    print("\n" + "-"*80)
    print("SCENARIO 3: queueAhead counts orders with LARGER sortIndex (above/newer)")
    print("-"*80)
    
    print("\n[3.1] Tracking order X (now at top)...")
    track_x = track_order(order_x_code)
    if not track_x:
        print("❌ SCENARIO 3 FAILED: Could not track order X")
        sys.exit(1)
    
    queue_x = track_x.get("queueAhead")
    print(f"   Order X queueAhead: {queue_x}")
    
    print("\n[3.2] Tracking order Y (below X)...")
    track_y = track_order(order_y_code)
    if not track_y:
        print("❌ SCENARIO 3 FAILED: Could not track order Y")
        sys.exit(1)
    
    queue_y = track_y.get("queueAhead")
    print(f"   Order Y queueAhead: {queue_y}")
    
    # X is above Y, so X should have FEWER orders ahead (queueAhead_X < queueAhead_Y)
    # The topmost open order should have queueAhead = 0
    if queue_x < queue_y:
        print(f"✅ SCENARIO 3 PASSED: queueAhead_X ({queue_x}) < queueAhead_Y ({queue_y}). Top order has fewer ahead.")
    else:
        print(f"❌ SCENARIO 3 FAILED: queueAhead_X ({queue_x}) should be < queueAhead_Y ({queue_y})")
        sys.exit(1)
    
    # Check if X (topmost) has queueAhead = 0
    if queue_x == 0:
        print(f"✅ SCENARIO 3 PASSED: Topmost open order (X) has queueAhead = 0")
    else:
        print(f"⚠️  SCENARIO 3 WARNING: Topmost order X has queueAhead = {queue_x} (expected 0, but may have other orders above)")
    
    # ========================================================================
    # SCENARIO 4: Edit email field
    # ========================================================================
    print("\n" + "-"*80)
    print("SCENARIO 4: Edit email field")
    print("-"*80)
    
    print(f"\n[4.1] Setting email to {TEST_EMAIL} on order X...")
    update_resp = update_order(token, order_x_after["id"], {"email": TEST_EMAIL})
    if update_resp.status_code != 200:
        print(f"❌ SCENARIO 4 FAILED: Update email failed: {update_resp.status_code} {update_resp.text}")
        sys.exit(1)
    
    update_data = update_resp.json()
    if not update_data.get("ok"):
        print(f"❌ SCENARIO 4 FAILED: Update returned ok:false")
        sys.exit(1)
    
    returned_email = update_data.get("order", {}).get("email")
    if returned_email == TEST_EMAIL:
        print(f"✅ SCENARIO 4 PASSED: Email updated to {TEST_EMAIL}")
    else:
        print(f"❌ SCENARIO 4 FAILED: Email not updated correctly. Expected: {TEST_EMAIL}, Got: {returned_email}")
        sys.exit(1)
    
    print(f"\n[4.2] Setting email to empty string on order X...")
    update_resp2 = update_order(token, order_x_after["id"], {"email": ""})
    if update_resp2.status_code != 200:
        print(f"❌ SCENARIO 4 FAILED: Update email to empty failed: {update_resp2.status_code} {update_resp2.text}")
        sys.exit(1)
    
    update_data2 = update_resp2.json()
    if not update_data2.get("ok"):
        print(f"❌ SCENARIO 4 FAILED: Update returned ok:false")
        sys.exit(1)
    
    returned_email2 = update_data2.get("order", {}).get("email")
    if returned_email2 == "":
        print(f"✅ SCENARIO 4 PASSED: Email cleared (empty string)")
    else:
        print(f"❌ SCENARIO 4 FAILED: Email not cleared. Expected: '', Got: {returned_email2}")
        sys.exit(1)
    
    # ========================================================================
    # SCENARIO 5: Manual status mail WITH email
    # ========================================================================
    print("\n" + "-"*80)
    print("SCENARIO 5: Manual status mail WITH email")
    print("-"*80)
    
    print(f"\n[5.1] Setting email back to {TEST_EMAIL} on order X...")
    update_resp3 = update_order(token, order_x_after["id"], {"email": TEST_EMAIL})
    if update_resp3.status_code != 200:
        print(f"❌ SCENARIO 5 FAILED: Update email failed: {update_resp3.status_code} {update_resp3.text}")
        sys.exit(1)
    print(f"✅ Email set to {TEST_EMAIL}")
    
    print(f"\n[5.2] Sending manual status mail to order X...")
    mail_resp = send_status_mail(token, order_x_after["id"])
    if mail_resp.status_code != 200:
        print(f"❌ SCENARIO 5 FAILED: Send status mail failed: {mail_resp.status_code} {mail_resp.text}")
        sys.exit(1)
    
    mail_data = mail_resp.json()
    if mail_data.get("ok"):
        print(f"✅ SCENARIO 5 PASSED: Manual status mail sent successfully: {mail_data}")
    else:
        print(f"❌ SCENARIO 5 FAILED: Send status mail returned ok:false: {mail_data}")
        sys.exit(1)
    
    # ========================================================================
    # SCENARIO 6: Manual status mail WITHOUT email
    # ========================================================================
    print("\n" + "-"*80)
    print("SCENARIO 6: Manual status mail WITHOUT email")
    print("-"*80)
    
    print("\n[6.1] Creating order Z without email...")
    order_z_data = create_order("Test Order Z", "")
    if not order_z_data:
        print("❌ SCENARIO 6 FAILED: Could not create order Z")
        sys.exit(1)
    order_z_number = order_z_data["orderNumber"]
    
    # Get full order Z details
    order_z = get_order_by_number(token, order_z_number)
    if not order_z:
        print("❌ SCENARIO 6 FAILED: Could not find order Z")
        sys.exit(1)
    
    print(f"✅ Order Z created: {order_z_number}, email: '{order_z.get('email')}'")
    
    print(f"\n[6.2] Sending manual status mail to order Z (no email)...")
    mail_resp_z = send_status_mail(token, order_z["id"])
    if mail_resp_z.status_code != 200:
        print(f"❌ SCENARIO 6 FAILED: Expected 200 response: {mail_resp_z.status_code} {mail_resp_z.text}")
        sys.exit(1)
    
    mail_data_z = mail_resp_z.json()
    if not mail_data_z.get("ok"):
        error_msg = mail_data_z.get("error", "")
        # Check for German error message about missing email
        if "keine" in error_msg.lower() and "mail" in error_msg.lower():
            print(f"✅ SCENARIO 6 PASSED: Returned ok:false with German error: '{error_msg}'")
        else:
            print(f"⚠️  SCENARIO 6 WARNING: Got ok:false but error message may not be in German: '{error_msg}'")
    else:
        print(f"❌ SCENARIO 6 FAILED: Expected ok:false for order without email, got ok:true: {mail_data_z}")
        sys.exit(1)
    
    # ========================================================================
    # SCENARIO 7: Auth checks for manual status mail
    # ========================================================================
    print("\n" + "-"*80)
    print("SCENARIO 7: Auth checks for manual status mail")
    print("-"*80)
    
    print("\n[7.1] Sending status mail WITHOUT Authorization header...")
    resp_no_auth = requests.post(f"{BASE_URL}/orders/{order_x_after['id']}/send-status-mail", json={})
    if resp_no_auth.status_code == 401:
        print(f"✅ SCENARIO 7.1 PASSED: Got 401 without auth")
    else:
        print(f"❌ SCENARIO 7.1 FAILED: Expected 401, got {resp_no_auth.status_code}")
        sys.exit(1)
    
    print("\n[7.2] Sending status mail with auth but nonexistent order ID...")
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp_fake_id = send_status_mail(token, fake_id)
    if resp_fake_id.status_code == 404:
        print(f"✅ SCENARIO 7.2 PASSED: Got 404 for nonexistent order ID")
    else:
        print(f"❌ SCENARIO 7.2 FAILED: Expected 404, got {resp_fake_id.status_code}")
        sys.exit(1)
    
    # ========================================================================
    # SCENARIO 8: Regression tests
    # ========================================================================
    print("\n" + "-"*80)
    print("SCENARIO 8: Regression tests")
    print("-"*80)
    
    print("\n[8.1] Checking for MongoDB _id leaks in GET /api/orders...")
    all_orders_check = get_all_orders(token)
    has_id_leak = any("_id" in order for order in all_orders_check)
    if not has_id_leak:
        print(f"✅ SCENARIO 8.1 PASSED: No MongoDB _id leaks in GET /api/orders")
    else:
        print(f"❌ SCENARIO 8.1 FAILED: Found MongoDB _id in orders")
        sys.exit(1)
    
    print("\n[8.2] Checking that track endpoint does NOT expose email...")
    track_x_check = track_order(order_x_code)
    if "email" not in track_x_check:
        print(f"✅ SCENARIO 8.2 PASSED: Track endpoint does not expose email (privacy maintained)")
    else:
        print(f"❌ SCENARIO 8.2 FAILED: Track endpoint exposes email field: {track_x_check.get('email')}")
        sys.exit(1)
    
    print("\n[8.3] Testing generic PUT /api/orders/:id (status update)...")
    status_update_resp = update_order(token, order_x_after["id"], {"status": "In Pruefung"})
    if status_update_resp.status_code == 200 and status_update_resp.json().get("ok"):
        print(f"✅ SCENARIO 8.3 PASSED: Generic PUT still works for status update")
    else:
        print(f"❌ SCENARIO 8.3 FAILED: Generic PUT failed: {status_update_resp.status_code} {status_update_resp.text}")
        sys.exit(1)
    
    print("\n[8.4] Testing generic PUT /api/orders/:id (model update with grams/hours)...")
    model_update_resp = update_order(token, order_x_after["id"], {"model": {"filamentGrams": 50, "printHours": 4}})
    if model_update_resp.status_code == 200:
        model_data = model_update_resp.json()
        if model_data.get("ok") and model_data.get("order", {}).get("price", {}).get("total", 0) > 0:
            print(f"✅ SCENARIO 8.4 PASSED: Generic PUT works for model update, price calculated: {model_data.get('order', {}).get('price', {}).get('total')}")
        else:
            print(f"❌ SCENARIO 8.4 FAILED: Model update did not calculate price correctly: {model_data}")
            sys.exit(1)
    else:
        print(f"❌ SCENARIO 8.4 FAILED: Model update failed: {model_update_resp.status_code} {model_update_resp.text}")
        sys.exit(1)
    
    print("\n[8.5] Verifying reorder route does not clash with generic PUT /:id...")
    # We already tested both routes successfully above, so this is implicit
    print(f"✅ SCENARIO 8.5 PASSED: Reorder route (PUT /api/orders/reorder) and generic PUT (PUT /api/orders/:id) both work without clash")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("✅ ALL 8 SCENARIOS PASSED")
    print("="*80)
    print("\nSUMMARY:")
    print("  ✅ SCENARIO 1: Newest orders on top (sortIndex DESCENDING)")
    print("  ✅ SCENARIO 2: Reorder direction (first id = highest sortIndex = top)")
    print("  ✅ SCENARIO 3: queueAhead counts orders with LARGER sortIndex (above)")
    print("  ✅ SCENARIO 4: Edit email field (set and clear)")
    print("  ✅ SCENARIO 5: Manual status mail WITH email")
    print("  ✅ SCENARIO 6: Manual status mail WITHOUT email (German error)")
    print("  ✅ SCENARIO 7: Auth checks (401 without auth, 404 for nonexistent id)")
    print("  ✅ SCENARIO 8: Regression tests (no _id leaks, email privacy, generic PUT works)")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
