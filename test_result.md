#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: "3D Druck Service - privates Auftragsportal. Auftragsformular mit MakerWorld-Vorschau, Preisschaetzung, Kundencode-Status-Tracking, geschuetzter Admin-Bereich (admin/Admin123!) mit Auftragsverwaltung (Status aendern, bearbeiten, loeschen, Fotos hochladen). Next.js + MongoDB."

backend:
  - task: "SMS-Benachrichtigungen via Android SMS-Gateway (Eingang/Druck startet/Abholbereit)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js, lib/sms.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "NEU: SMS ueber sms-gate.app (Android-Gateway, Cloud). Neues optionales Feld 'phone' im Auftrag (im Formular + im Admin editierbar). 3 SMS (idempotent via order.smsSent): (1) bei Auftragseingang, (2) Statuswechsel -> 'Druck läuft', (3) Statuswechsel -> 'Abholbereit'. Best-effort (withTimeout, blockiert nie). Zugangsdaten via verifySmsConnection manuell bestaetigt (Token 201). WICHTIG FUER TEST: KEINE echten SMS an fremde/zufaellige Nummern senden (kostet echtes Geld + geht an reale Personen). Nur testen: (a) GET /api/sms-status mit Admin-Auth -> {ok:true}; ohne Auth 401. (b) POST /api/orders OHNE phone -> 200 (keine SMS). (c) PUT /api/orders/:id {phone:'0151...'} -> gespeichert, KEIN SMS-Versand bei reinem Feld-Update. (d) Admin GET /api/orders enthaelt 'phone'. (e) phone NICHT im oeffentlichen Track-Endpoint. BITTE bei Statuswechsel-Tests (Druck läuft/Abholbereit) nur Auftraege OHNE phone verwenden, damit keine echte SMS rausgeht."
        -working: true
        -agent: "testing"
        -comment: "✅ SMS NOTIFICATION FEATURE FULLY TESTED (7/7 scenarios passed). NO REAL SMS SENT (field storage & config only tested). SCENARIO 1 - SMS config check: GET /api/sms-status WITHOUT auth -> 401 (as expected). WITH admin Bearer token -> 200 {ok:true} (SMS gateway credentials valid). SCENARIO 2 - Order without phone: POST /api/orders (NO phone, NO email) -> 200 ok:true, orderNumber (3D-791839), customerCode (YPP69KUW), price=null. SCENARIO 3 - Phone stored via field update (NO SMS triggered): PUT /api/orders/:id {phone:'0151 23456789'} with Bearer auth -> 200 ok:true, phone stored successfully in response and verified in admin GET /api/orders. IMPORTANT: NO status change in this request, so NO SMS sent. SCENARIO 4 - Clear phone: PUT /api/orders/:id {phone:''} -> 200, phone cleared (empty string). SCENARIO 5 - Email alongside: PUT /api/orders/:id {email:'jannik-druck@gmx.de'} -> 200, email set successfully (no status change). SCENARIO 6 - Privacy: GET /api/orders/track?code=YPP69KUW -> 200, response does NOT contain 'phone' or 'email' fields (privacy maintained). SCENARIO 7 - Regression: No MongoDB _id leaks in admin orders list. Generic PUT {adminNotes:'test'} -> 200 ok:true. Order creation quick (1.006s). All backend APIs working correctly. SMS feature ready for production use."

  - task: "E-Mail bearbeiten + manuelle Status-Mail + neueste Auftraege oben"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js, lib/email.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "NEU: (1) Sortierung geaendert -> GET /api/orders sortiert jetzt nach sortIndex ABSTEIGEND (neueste oben). Neue Auftraege bekommen sortIndex=Date.now() (oben). Reorder-Endpoint setzt sortIndex = (n - index), sodass oben = groesster sortIndex. (2) queueAhead zaehlt jetzt offene Auftraege mit GROESSEREM sortIndex (=weiter oben). (3) E-Mail editierbar: PUT /api/orders/:id mit {email:'...'} aktualisiert die Adresse (Feld war bereits erlaubt). (4) NEU POST /api/orders/:id/send-status-mail (Bearer Auth): sendet dem Kunden eine Status-Mail (aktueller Status, Preis falls gesetzt, Kundennachricht, Tracking-Link). Ohne Auth 401; ohne hinterlegte E-Mail {ok:false, error}; unbekannte id 404. Zu testen: (a) 2 neue Auftraege -> GET /api/orders: neuester zuerst. (b) reorder -> Reihenfolge bleibt konsistent, queueAhead passt (oberster offener = 0 ahead, unterer offener = mehr). (c) PUT email auf jannik-druck@gmx.de -> gespeichert. (d) POST send-status-mail mit email -> 200 ok:true; ohne email -> ok:false. Emails best-effort, email=jannik-druck@gmx.de nutzen."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL 8 SCENARIOS PASSED (NEW/CHANGED BEHAVIORS FULLY TESTED). SCENARIO 1 - Newest orders on top: Created order X (3D-352163, sortIndex=1784009272279), then order Y (3D-158720, sortIndex=1784009273602). GET /api/orders returned Y at index 0, X at index 1 (Y before X in array). Y.sortIndex (1784009273602) > X.sortIndex (1784009272279). Verified: newest orders appear at TOP (sortIndex DESCENDING). SCENARIO 2 - Reorder direction: PUT /api/orders/reorder with orderedIds=[X.id, Y.id, ...rest] (28 total orders) -> 200 OK, ok:true. After reorder: X.sortIndex=28, Y.sortIndex=27, X at index 0, Y at index 1. Verified: first id in array gets HIGHEST sortIndex and appears at TOP. SCENARIO 3 - queueAhead direction: Track X (top order) -> queueAhead=0. Track Y (below X) -> queueAhead=1. Verified: queueAhead counts orders with LARGER sortIndex (above/newer in list), topmost open order has queueAhead=0. SCENARIO 4 - Edit email: PUT /api/orders/X.id {email:'jannik-druck@gmx.de'} with auth -> 200 OK, ok:true, returned order.email='jannik-druck@gmx.de'. PUT {email:''} -> 200 OK, email cleared (empty string). SCENARIO 5 - Manual status mail WITH email: Set email on X to jannik-druck@gmx.de. POST /api/orders/X.id/send-status-mail with Bearer auth -> 200 OK, ok:true (mail sent successfully). SCENARIO 6 - Manual status mail WITHOUT email: Created order Z (3D-684789) without email. POST /api/orders/Z.id/send-status-mail with auth -> 200 OK, ok:false, error:'Für diesen Auftrag ist keine E-Mail-Adresse hinterlegt.' (German error message as expected). SCENARIO 7 - Auth checks: POST send-status-mail WITHOUT Authorization -> 401 (as expected). POST with auth but nonexistent order ID (00000000-0000-0000-0000-000000000000) -> 404 (as expected). SCENARIO 8 - Regression: No MongoDB _id leaks in GET /api/orders. Track endpoint does NOT expose email (privacy maintained). Generic PUT /api/orders/:id for status update -> 200 OK (status changed to 'In Pruefung'). Generic PUT for model update {filamentGrams:50, printHours:4} -> 200 OK, price.total=8.35 (calculated correctly). Reorder route (PUT /api/orders/reorder) and generic PUT (PUT /api/orders/:id) both work without clash. All backend APIs working correctly. Ready for user acceptance."
        -working: true
        -agent: "testing"
        -comment: "✅ UPDATED queueAhead DIRECTION VERIFIED (7/7 tests passed). CRITICAL CHANGE: queueAhead logic FLIPPED to count orders with SMALLER sortIndex (older, printed earlier). Created 3 orders P, Q, R in sequence (P oldest, R newest). Verified sortIndex order: P.sortIndex=1784305700685 < Q.sortIndex=1784305701936 < R.sortIndex=1784305703299. Admin list sorted DESCENDING: R at index 0, Q at index 1, P at index 2 (newest on top). Tracked all three orders: P.queueAhead=26 (smallest), Q.queueAhead=27, R.queueAhead=28 (largest). Verified queueAhead(P) < queueAhead(Q) < queueAhead(R) - older orders have FEWER ahead, newer orders have MORE ahead. Marked P as 'Abgeschlossen' -> Q.queueAhead decreased from 27 to 26 (P no longer counts). Completed order P has queueAhead=0 (as expected). Code verification: line 470 in route.js uses 'key(o) < myKey' to count orders with SMALLER sortIndex. Regression: No email exposure in tracking (privacy maintained), no MongoDB _id leaks (security maintained). All backend APIs working correctly. queueAhead direction now matches specification: BOTTOM of admin list (oldest/smallest sortIndex) = next to print, order with SMALLEST sortIndex among open orders has SMALLEST queueAhead."

  - task: "Auftrags-Reihenfolge aendern (PUT /api/orders/reorder + sortIndex, Queue-Bezug)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "NEU: Auftraege haben jetzt ein Feld 'sortIndex' (Warteschlangen-Reihenfolge). (1) GET /api/orders (Admin) sortiert nach sortIndex aufsteigend; fehlender sortIndex wird lazy aus createdAt migriert und persistiert. (2) POST /api/orders setzt sortIndex=Date.now() -> neue Auftraege ans Ende. (3) NEU PUT /api/orders/reorder (Bearer Auth) body {orderedIds:[...]} setzt sortIndex=Index (0,1,2...) fuer alle IDs -> ohne Auth 401, leere Liste 400. (4) queueAhead im Track-Endpoint zaehlt jetzt offene Auftraege mit KLEINEREM sortIndex (=weiter vorne in der manuellen Reihenfolge) statt nach createdAt. Zu testen: 3 Auftraege anlegen, GET /api/orders Reihenfolge notieren, PUT reorder mit umgekehrter ID-Reihenfolge, erneut GET -> neue Reihenfolge; Track eines hinteren offenen Auftrags -> queueAhead entspricht Anzahl offener Auftraege davor; nach reorder aendert sich queueAhead entsprechend."
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED (ALL 7 SCENARIOS PASSED): REORDER FEATURE FULLY WORKING. SCENARIO 1 - Created 3 orders A, B, C: POST /api/orders -> 200 OK, each with sortIndex=Date.now() (A=1783955373120, B=1783955374497, C=1783955375643), orderNumber (3D-XXXXXX), customerCode (8 chars), status='Eingegangen'. SCENARIO 2 - GET /api/orders (admin): Returns orders sorted by sortIndex ascending, verified A < B < C. SCENARIO 3 - Reorder: PUT /api/orders/reorder with Bearer auth, body {orderedIds:[C.id, A.id, B.id]} -> 200 OK, ok:true. GET /api/orders again: sortIndex updated to reflect new order (C.sortIndex=0, A.sortIndex=1, B.sortIndex=2), verified C < A < B. SCENARIO 4 - Queue position reflects manual order: GET /api/orders/track for C -> queueAhead=0 (first in queue), A -> queueAhead=1 (one ahead), B -> queueAhead=3 (three ahead). Verified queueAhead_C < queueAhead_A < queueAhead_B. SCENARIO 5 - Queue shrinks when ahead-order completed: PUT /api/orders/C.id {status:'Abgeschlossen'} with auth -> 200 OK. Track B again -> queueAhead decreased from 3 to 2 (C no longer counts). Track C -> queueAhead=0 (completed orders always 0). SCENARIO 6 - Auth & validation: PUT /api/orders/reorder without Authorization -> 401. PUT with auth but empty body {} -> 400. PUT with auth but empty orderedIds [] -> 400. SCENARIO 7 - Regression: No MongoDB _id leaks in GET /api/orders. GET /api/orders/track does NOT expose email (privacy maintained). Existing PUT /api/orders/:id (status update) -> 200 OK, status updated. Existing PUT /api/orders/:id (model update with grams/hours) -> 200 OK, price calculated correctly. Reorder route does not clash with generic PUT /api/orders/:id. All backend APIs working correctly."

  - task: "Preis erst vom Admin (Auftrag ohne Gramm/Zeit/Preis) + E-Mail-Link + Admin-Info-Mail"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js, lib/email.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "GEAENDERT: POST /api/orders benoetigt KEINE Gramm/Zeit mehr und berechnet KEINEN Preis -> order.price = null. Preis entsteht erst, wenn Admin via PUT /api/orders/:id model.filamentGrams/printHours (oder size/quantity/priority) setzt -> dann wird price neu berechnet. Bestaetigungs-Mail enthaelt jetzt einen direkten Status-Link (NEXT_PUBLIC_BASE_URL/?track=CODE). NEU: Admin-Info-Mail an GMX_FROM_EMAIL (jannik-druck@gmx.de) bei JEDEM neuen Auftrag mit allen Kerndaten. Abhol-Mail enthaelt jetzt Preis (falls gesetzt) + Status-Link. Zu testen: (1) POST /api/orders nur mit name+makerworldLink -> 200, danach Admin GET /api/orders: order.price === null. (2) PUT /api/orders/:id mit {model:{filamentGrams:45,printHours:3}} + Auth -> 200, order.price.total > 0. (3) PUT status='Abholbereit' -> 200. (4) Track vor Preis: price null; nach Preis: price gesetzt. Emails best-effort (nie blockierend). Fuer Sends email=jannik-druck@gmx.de nutzen."
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED (26/26 tests passed): CHANGED PRICING FLOW VERIFIED. TEST 1 - Create minimal order WITHOUT grams/hours: POST /api/orders with name+email+makerworldLink -> 200 OK, ok:true, orderNumber (3D-598398), customerCode (LUBHLYKX), price=null (as expected). Response does NOT require grams/hours. TEST 1b - Admin GET /api/orders: order.price is null (not an object), no MongoDB _id leak. TEST 2 - Track before pricing: GET /api/orders/track?code -> 200, price=null, email NOT exposed (privacy maintained). TEST 3 - Admin sets grams/time: PUT /api/orders/:id with {model:{filamentGrams:45,printHours:3}} + Bearer auth -> 200 OK, ok:true, order.price.total=6.67 (numeric > 0). CRITICAL FIX APPLIED: model.image and modelName now preserved after setting grams (was being wiped, now merged correctly). TEST 4 - Track after pricing: price.total=6.67 (numeric value from TEST 3). TEST 5 - Eilig recalculation: PUT priority='Eilig' -> 200, price.total=8.34 (exactly 25% higher, ratio 1.250). TEST 6 - Status to Abholbereit: PUT status='Abholbereit' with auth -> 200, status updated, response quick (0.128s, email sent async/non-blocking). TEST 7-8 - Validation: POST without makerworldLink -> 400, POST without name -> 400 (as expected). TEST 9 - Auth: PUT without Authorization -> 401 (as expected). TEST 10 - Regression: GET /api/email-status with auth -> 200, ok:true. TEST 11 - Regression: No MongoDB _id leaks in tracking. All scenarios from review request verified successfully. Key findings: Orders created WITHOUT price (price=null), price calculated when admin sets grams/printHours, Eilig adds ~25% surcharge, email NOT exposed in tracking, validation and auth working correctly."

        -working: true
        -agent: "testing"
        -comment: "✅ VERCEL-SAFE EMAIL REGRESSION TESTED (6/6 tests passed). CRITICAL CHANGE VERIFIED: Emails are now AWAITED with 12s timeout (instead of fire-and-forget) to prevent Vercel serverless freeze. TEST 1 - POST /api/orders WITH email (jannik-druck@gmx.de) -> 200 OK in 4.948s (image fetch + awaited confirmation + admin emails), ok:true, orderNumber (3D-633965), customerCode (4V8BJPLC), price=null. Response time well under 30s limit. TEST 2 - POST /api/orders WITHOUT email -> 200 OK in 0.768s (only admin email awaited), ok:true. TEST 3 - PUT /api/orders/:id status='Abholbereit' with auth -> 200 OK in 0.447s (pickup email awaited), status updated correctly. TEST 4 - GET /api/email-status with auth -> 200 OK, ok:true. TEST 5 - Validation: missing name/link -> 400. TEST 6 - Auth: PUT without token -> 401. No MongoDB _id leaks. All response times acceptable. Awaited email sending (with timeout) working correctly without blocking API responses."
  - task: "MakerWorld Vorschaubild laden (auto bei Auftrag + POST /api/orders/:id/fetch-image)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "NEU: Beim Auftrag erstellen wird via Firecrawl NUR das Vorschaubild (og:image) + Modellname von der MakerWorld-URL geladen und in order.model.image/modelName gespeichert (max 12s, best effort - Gramm/Zeit bleiben manuell). Zusaetzlich Admin-Endpunkt POST /api/orders/:id/fetch-image (Bearer Auth) zum Nachladen/Aktualisieren des Bildes fuer bestehende Auftraege -> liefert {ok:true, order} oder {ok:false, error:'Kein Bild gefunden'}. Ohne Auth 401. Firecrawl-Bildabruf manuell verifiziert (og:image kam korrekt zurueck). Zu testen: (1) POST /api/orders mit gueltigem makerworldLink (z.B. https://makerworld.com/en/models/1211525) -> 200, danach Admin GET /api/orders: order.model.image ist eine URL. (2) POST /api/orders/:id/fetch-image mit Auth -> 200 ok:true, order.model.image gesetzt. (3) ohne Auth -> 401. (4) ungueltige/nicht existierende id -> 404."
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED (22/22 tests passed): SCENARIO 1 - Auto image fetch on order creation: POST /api/orders with makerworldLink (https://makerworld.com/en/models/1211525) -> 200 OK, ok:true, orderNumber (3D-558586), customerCode (E6TABW2F), quick response (3.403s). Admin GET /api/orders confirmed order.model.image is a valid URL (https://makerworld.bblmw.com/makerworld/model/USd7effb5cd9a105/design/2025-03-15_fdf7f01d8ab43.jpg...), order.model.modelName exists ('Understructure for Piranha Plant Switch Dock'). Manual values preserved: filamentGrams=45, printHours=3. No MongoDB _id leak. SCENARIO 2 - Manual fetch-image endpoint: POST /api/orders/:id/fetch-image with Bearer auth -> 200 OK, ok:true, order.model.image set to valid URL. SCENARIO 3 - Auth check: POST without Authorization header -> 401 (as expected). SCENARIO 4 - Not found: POST with nonexistent ID -> 404 (as expected). SCENARIO 5 - Regression: Order creation still quick (1.956s), no MongoDB _id leaks, GET /api/orders/track works correctly with all fields present, email NOT exposed in tracking (privacy maintained). All scenarios verified successfully."

  - task: "MakerWorld Vorschau (POST /api/makerworld-preview)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Best-effort OG-Meta Scraping. Testen mit einer echten MakerWorld URL und mit ungueltiger URL (soll ok:false liefern, kein 500)."
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED: Invalid URL returns 200 with ok:false (no 500 error). Missing URL returns 400. Endpoint handles errors gracefully as expected."

  - task: "Auftrag erstellen (POST /api/orders)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Erzeugt id(uuid), orderNumber(3D-XXXXXX), customerCode(8 Zeichen), berechnet Preis, Status Eingegangen. Pflichtfelder name + makerworldLink. Preis muss +20% Gewinn und bei Eilig +25% enthalten."
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED: Creates orders with correct orderNumber format (3D-XXXXXX), customerCode (8 chars), UUID id. Price calculation verified: Normal priority total=15.0 for qty=2, Eilig priority total=18.75 (exactly 25% more). Validation working: missing name or makerworldLink returns 400. No MongoDB _id in responses."

  - task: "Auftrag verfolgen (GET /api/orders/track?code=)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Oeffentlich per customerCode. 404 bei falschem Code."
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED: Valid customerCode returns order with status, orderNumber, price. Invalid code returns 404. Status updates reflected correctly (verified after PUT status change). Deleted orders return 404."

  - task: "Admin Login (POST /api/admin/login)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "admin/Admin123! -> token. Falsche Daten -> 401."
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED: Correct credentials (admin/Admin123!) return token (base64 encoded). Incorrect credentials return 401. Token format verified."

  - task: "Admin Auftraege auflisten (GET /api/orders, Auth)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Erfordert Bearer Token. Ohne Token -> 401."
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED: Without Authorization header returns 401. With Bearer token returns orders array. Created orders found in list. No MongoDB _id leak (only UUID id field)."

  - task: "Admin Auftrag aktualisieren (PUT /api/orders/:id, Auth)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Status/Notizen/Fotos/Groesse/Anzahl/Prioritaet aenderbar. Statusverlauf wird gepflegt. Preis wird bei preisrelevanten Aenderungen neu berechnet."
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED: Status update working (statusHistory properly maintained). Price recalculation verified (qty 2->4: price 15->30). Photos upload working (base64 data stored). Without auth returns 401. All update operations successful."

  - task: "Admin Auftrag loeschen (DELETE /api/orders/:id, Auth)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Loescht per id. 404 wenn nicht gefunden."
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED: With auth deletes successfully (200 OK). Without auth returns 401. Non-existent ID returns 404. Deleted order no longer trackable (404 on track endpoint)."

  - task: "Farben abrufen (GET /api/colors)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Oeffentlich, kein Auth. Liefert {colors:[{name,hex}]}. Ohne gespeicherte Farben werden DEFAULT_COLORS (10 Stueck) zurueckgegeben."
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED: Public endpoint returns 200. Returns 10 default colors when no colors saved. After saving colors, returns saved colors (not defaults). Color structure valid (name, hex). No MongoDB _id leak. All tests passed (5/5)."

  - task: "Farben speichern (PUT /api/settings/colors, Auth)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Admin (Bearer Token noetig). Body {colors:[{name,hex}]} -> speichert und liefert {ok:true, colors}. Leere/namenlose Eintraege werden herausgefiltert. Ohne Token 401."
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED: Without auth returns 401. With Bearer token and valid body returns 200 with ok:true. Empty names correctly filtered (3 colors sent, 2 saved). Saved colors persist and override defaults. Idempotency verified (can update colors multiple times). No MongoDB _id leak. All tests passed (5/5)."

  - task: "Warteschlangen-Position + Kundennachricht im Tracking (GET /api/orders/track)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "NEU: GET /api/orders/track?code= liefert jetzt zusaetzlich 'queueAhead' (Anzahl offener Auftraege die frueher erstellt wurden, exkl. Status Fertig/Abholbereit/Abgeschlossen) und 'customerMessage'. Bei abgeschlossenen Auftraegen soll queueAhead=0 sein. Bitte testen: mehrere Auftraege erstellen, ein aelterer offener Auftrag -> neuerer Auftrag zeigt queueAhead>=1. Nach Statuswechsel des aelteren auf 'Abgeschlossen' -> queueAhead des neueren sinkt."
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED: queueAhead logic working correctly. Created Order A, then Order B. Order B shows queueAhead=10 (10 orders ahead including A). After marking Order A as 'Abgeschlossen', Order B's queueAhead decreased to 9 (other orders still ahead). Order A (completed) shows queueAhead=0 as expected. customerMessage field present in all tracking responses. Logic verified: queueAhead counts only open orders (status NOT in [Fertig, Abholbereit, Abgeschlossen]) created earlier. Completed orders always show queueAhead=0."


  - task: "Kundennachricht speichern (PUT /api/orders/:id customerMessage, Auth)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED: customerMessage functionality working correctly. PUT /api/orders/:id without auth returns 401 as expected. With Bearer token, customerMessage 'Dein Druck ist fertig' was successfully saved. GET /api/orders/track correctly returns the saved customerMessage. All authentication checks working. Regression test passed: existing tracking fields (orderNumber, status, price) still work correctly, invalid code returns 404, no MongoDB _id leaks."

        -comment: "NEU: PUT /api/orders/:id akzeptiert Feld 'customerMessage'. Nach Update muss GET /api/orders/track?code= die gesetzte customerMessage zurueckgeben. Ohne Auth 401."

frontend:
  - task: "E-Mail-Benachrichtigungen via GMX SMTP (Bestätigung + Abholbereit)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js, lib/email.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: true
        -agent: "main"
        -comment: "NEU: nodemailer + GMX SMTP (mail.gmx.net:587 STARTTLS). Optionales E-Mail-Feld im Auftragsformular. Bei Auftragseingang -> Bestätigungsmail mit orderNumber+customerCode. Bei Statuswechsel auf 'Abholbereit' -> Abhol-Mail (nur beim Wechsel, nicht wiederholt). Versand ist best-effort (Fehler brechen Auftrag/Update nicht ab). SMTP-Verbindung + echter Mailversand manuell verifiziert (VERIFY_OK + SEND_OK an jannik-druck@gmx.de). Zu testen: (1) POST /api/orders mit 'email' -> 200, Feld gespeichert; (2) Admin GET /api/orders enthaelt 'email'; (3) PUT /api/orders/:id status='Abholbereit' -> 200; (4) Auftrag OHNE email funktioniert weiterhin. Fuer echte Sends bitte email=jannik-druck@gmx.de nutzen (Delivery bereits manuell bestaetigt)."
        -working: true
        -agent: "testing"
        -comment: "✅ TESTED (26/26 tests passed): (1) POST /api/orders WITH email (jannik-druck@gmx.de) -> 200 OK, ok:true, orderNumber (3D-XXXXXX), customerCode (8 chars), quick response (0.206s, email is async/non-blocking). (2) Admin GET /api/orders -> email field stored correctly (jannik-druck@gmx.de), no MongoDB _id leak. (3) POST /api/orders WITHOUT email -> 200 OK, email stored as empty string (''). (4) PUT /api/orders/:id status='Abholbereit' with auth -> 200 OK, status updated, quick response (0.178s, pickup email sent async). (5) PUT without auth -> 401 as expected. (6) GET /api/email-status without auth -> 401. (7) GET /api/email-status with auth -> 200 OK, ok:true (SMTP verified). (8) Regression: GET /api/orders/track does NOT expose email field (privacy maintained), all other fields (orderNumber, customerCode, status, queueAhead, customerMessage) work correctly. Email sending is fire-and-forget (best-effort with .catch), never blocks API responses. All scenarios from review request verified."

  - task: "Startseite + Auftragsformular + Live-Preis + Erfolgsdialog"
    implemented: true
    working: "NA"
    file: "app/page.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Formular ausfuellen und absenden -> Erfolgsdialog mit Auftragsnummer + Kundencode. Live-Preis aktualisiert sich bei Groesse/Anzahl/Prioritaet."

  - task: "Status-Tracking per Kundencode"
    implemented: true
    working: "NA"
    file: "app/page.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Code eingeben -> Statusanzeige mit Stepper. 'Status pruefen' Button im Erfolgsdialog uebernimmt den Code automatisch."

  - task: "Admin-Login + Dashboard (Status aendern, bearbeiten, loeschen, Fotos)"
    implemented: true
    working: "NA"
    file: "app/page.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Login admin/Admin123!. Dashboard zeigt Auftraege, Status per Dropdown aenderbar, Details-Dialog fuer Bearbeitung/Fotos/Notizen, Loeschen mit Bestaetigung."
        -working: "NA"
        -agent: "main"
        -comment: "UI-Umbau: Dashboard in zwei Tabs aufgeteilt (shadcn Tabs) - 'Auftraege' (Statistik + Auftragsliste) und 'Konfiguration' (Materialien + Farben). Visuell per Screenshot verifiziert: beide Tabs rendern und wechseln korrekt. Nur Frontend-Umstrukturierung, keine Backend-Aenderung."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 3
  run_ui: true

test_plan:
  current_focus:
    - "SMS-Benachrichtigungen via Android SMS-Gateway (Eingang/Druck startet/Abholbereit)"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    -agent: "main"
    -message: "Backend bereits vollstaendig getestet (39/39). Jetzt Frontend-Test gewuenscht. Admin-Login: admin/Admin123!."
    -agent: "testing"
    -message: "✅ ALL BACKEND TESTS PASSED (39/39). Comprehensive testing completed: Order creation (Normal/Eilig with price verification), validation, tracking, admin login, order listing, updates (status/quantity/photos with price recalculation), deletion, and MakerWorld preview. All authentication checks working. No MongoDB _id leaks. Price formula verified. Ready for user acceptance."
    -agent: "main"
    -message: "NEUE FUNKTION: Admin kann verfuegbare Farben verwalten. Bitte NUR die neuen Farb-Endpunkte testen: (1) GET /api/colors -> oeffentlich, liefert {colors:[{name,hex}]}. Ohne gespeicherte Farben werden DEFAULT_COLORS (10 Stueck) zurueckgegeben. (2) PUT /api/settings/colors -> Admin (Bearer Token noetig, ohne Token 401). Body {colors:[{name:'Test',hex:'#ff0000'}]} -> speichert und liefert {ok:true, colors}. Danach GET /api/colors muss die gespeicherten Farben liefern. Leere/namenlose Eintraege werden herausgefiltert. Admin-Login admin/Admin123!."
    -agent: "testing"
    -message: "✅ COLOR ENDPOINTS FULLY TESTED (5/5 tests passed). GET /api/colors: Returns 10 default colors when none saved, returns saved colors after PUT. PUT /api/settings/colors: Requires auth (401 without token), filters empty names correctly (sent 3, saved 2), supports idempotent updates. No MongoDB _id leaks. All functionality working as specified."
    -agent: "main"
    -message: "NEUE FUNKTIONEN: (1) queueAhead in GET /api/orders/track - zeigt Anzahl offener Auftraege die frueher erstellt wurden. (2) customerMessage in PUT /api/orders/:id - Admin kann Nachricht fuer Kunden setzen, die dann im Tracking erscheint. Bitte beide Features testen."
    -agent: "testing"
    -message: "✅ NEW FEATURES FULLY TESTED (11/11 tests passed). FEATURE 1 - queueAhead: Logic working correctly. Order B shows queueAhead=10 when 10 orders ahead. After marking Order A as 'Abgeschlossen', queueAhead decreased to 9. Completed orders show queueAhead=0. Counts only open orders (status NOT in [Fertig, Abholbereit, Abgeschlossen]) created earlier. FEATURE 2 - customerMessage: PUT without auth returns 401. With auth, message saved successfully. GET /api/orders/track returns saved message. Regression tests passed: existing tracking fields work, invalid code returns 404, no MongoDB _id leaks. All backend APIs working correctly."
    -agent: "main"
    -message: "NEUE FUNKTION: E-Mail-Benachrichtigungen via GMX SMTP. Optionales E-Mail-Feld im Auftragsformular. Bei Auftragseingang -> Bestätigungsmail. Bei Statuswechsel auf 'Abholbereit' -> Abhol-Mail. Versand ist best-effort (fire-and-forget). Bitte testen: (1) POST /api/orders mit email -> 200, schnelle Antwort; (2) Admin GET /api/orders zeigt email; (3) POST ohne email -> 200, email=''; (4) PUT status='Abholbereit' -> 200; (5) Auth-Check; (6) GET /api/email-status; (7) Regression: GET /api/orders/track darf email NICHT zeigen."
    -agent: "testing"
    -message: "✅ EMAIL NOTIFICATION FEATURE FULLY TESTED (26/26 tests passed). All scenarios from review request verified: (1) POST /api/orders WITH email (jannik-druck@gmx.de) -> 200 OK, ok:true, orderNumber (3D-XXXXXX), customerCode (8 chars), quick response (0.206s, email is async/non-blocking). (2) Admin GET /api/orders -> email field stored correctly, no MongoDB _id leak. (3) POST /api/orders WITHOUT email -> 200 OK, email stored as empty string (''). (4) PUT status='Abholbereit' with auth -> 200 OK, status updated, quick response (0.178s, pickup email sent async). (5) PUT without auth -> 401. (6) GET /api/email-status: without auth -> 401, with auth -> 200 OK, ok:true (SMTP verified). (7) Regression: GET /api/orders/track does NOT expose email field (privacy maintained), all other fields work correctly. Email sending is fire-and-forget (best-effort with .catch), never blocks API responses. All backend APIs working correctly."

    -agent: "main"
    -message: "NEUE FUNKTION: MakerWorld Vorschaubild laden. Beim Auftrag erstellen wird via Firecrawl NUR das Vorschaubild (og:image) + Modellname von der MakerWorld-URL geladen (max 12s, best effort - Gramm/Zeit bleiben manuell). Zusaetzlich Admin-Endpunkt POST /api/orders/:id/fetch-image (Bearer Auth) zum Nachladen/Aktualisieren des Bildes. Bitte testen: (1) POST /api/orders mit makerworldLink -> 200, danach Admin GET /api/orders: order.model.image ist eine URL. (2) POST /api/orders/:id/fetch-image mit Auth -> 200 ok:true. (3) ohne Auth -> 401. (4) ungueltige id -> 404. (5) Regression: Auftragserstellung schnell, kein _id leak, Tracking funktioniert."
    -agent: "testing"
    -message: "✅ MAKERWORLD IMAGE FEATURE FULLY TESTED (22/22 tests passed). SCENARIO 1 - Auto image fetch: POST /api/orders with makerworldLink (https://makerworld.com/en/models/1211525) -> 200 OK in 3.403s, order.model.image is valid URL (https://makerworld.bblmw.com/...), order.model.modelName exists, manual filamentGrams=45 and printHours=3 preserved. SCENARIO 2 - Manual fetch: POST /api/orders/:id/fetch-image with auth -> 200 OK, ok:true, image URL set. SCENARIO 3 - Auth: POST without auth -> 401. SCENARIO 4 - Not found: POST with nonexistent ID -> 404. SCENARIO 5 - Regression: Order creation quick (1.956s), no MongoDB _id leaks, tracking works, email NOT exposed. All backend APIs working correctly. Ready for user acceptance."
    -agent: "main"
    -message: "GEAENDERTE FUNKTION: Preis erst vom Admin. Auftraege werden jetzt OHNE Gramm/Zeit/Preis erstellt (order.price = null). Preis wird erst berechnet, wenn Admin via PUT /api/orders/:id die Felder model.filamentGrams/printHours (oder size/quantity/priority) setzt. Bitte testen: (1) POST /api/orders nur mit name+makerworldLink -> 200, danach Admin GET /api/orders: order.price === null (nicht ein Objekt). (2) Track vor Preis: price null, email NICHT sichtbar. (3) PUT /api/orders/:id mit {model:{filamentGrams:45,printHours:3}} + Auth -> 200, order.price.total > 0. Verify model.image preserved. (4) Track nach Preis: price.total ist numerisch. (5) PUT priority='Eilig' -> price ~25% hoeher. (6) PUT status='Abholbereit' -> 200 (email async). (7) Validation: POST ohne name/link -> 400. (8) Auth: PUT ohne Auth -> 401. (9) Regression: kein _id leak, GET /api/email-status funktioniert. Fuer Sends email=jannik-druck@gmx.de nutzen."
    -agent: "main"
    -message: "REGRESSION TEST: Email sending made Vercel-safe. Emails are now AWAITED with 12s timeout (instead of fire-and-forget) to prevent serverless freeze. Bitte testen: (1) POST /api/orders mit email (jannik-druck@gmx.de) -> 200, response time < 30s, price=null. (2) POST /api/orders OHNE email -> 200 (nur admin-info email awaited). (3) PUT /api/orders/:id status='Abholbereit' mit Auth -> 200, status updated (pickup email awaited). (4) GET /api/email-status mit Auth -> ok:true. (5) Validation (missing name/link -> 400) und Auth (PUT ohne token -> 401) funktionieren. (6) Kein MongoDB _id leak."
    -agent: "testing"
    -message: "✅ VERCEL-SAFE EMAIL REGRESSION FULLY TESTED (6/6 tests passed). CRITICAL CHANGE VERIFIED: Emails are now AWAITED with 12s timeout (instead of fire-and-forget) to prevent Vercel serverless freeze. All scenarios from review request verified successfully. TEST 1 - POST /api/orders WITH email (jannik-druck@gmx.de) -> 200 OK in 4.948s (image fetch + awaited confirmation + admin emails), ok:true, orderNumber (3D-633965), customerCode (4V8BJPLC), price=null. Response time well under 30s limit. TEST 2 - POST /api/orders WITHOUT email -> 200 OK in 0.768s (only admin email awaited), ok:true, orderNumber (3D-203677), customerCode (PHJPSS4X). TEST 3 - PUT /api/orders/:id status='Abholbereit' with auth -> 200 OK in 0.447s (pickup email awaited), status updated correctly, no _id leak. TEST 4 - GET /api/email-status with auth -> 200 OK, ok:true (SMTP verified). TEST 5 - Validation: missing name -> 400, missing makerworldLink -> 400. TEST 6 - Auth: PUT without Authorization -> 401. No MongoDB _id leaks in any response. All response times acceptable. Awaited email sending (with timeout) working correctly without blocking API responses. All backend APIs working correctly. Ready for production deployment on Vercel."

    -agent: "testing"
    -message: "✅ CHANGED PRICING FLOW FULLY TESTED (26/26 tests passed). All scenarios from review request verified successfully. TEST 1 - Create minimal order WITHOUT grams/hours: POST /api/orders with name+email+makerworldLink -> 200 OK, ok:true, orderNumber (3D-598398), customerCode (LUBHLYKX), price=null (as expected). Response does NOT require grams/hours. TEST 1b - Admin GET /api/orders: order.price is null (not an object), no MongoDB _id leak. TEST 2 - Track before pricing: price=null, email NOT exposed (privacy maintained). TEST 3 - Admin sets grams/time: PUT with {model:{filamentGrams:45,printHours:3}} + auth -> 200, order.price.total=6.67 (numeric > 0). CRITICAL FIX APPLIED: model.image and modelName now preserved after setting grams (was being wiped, now merged correctly). TEST 4 - Track after pricing: price.total=6.67. TEST 5 - Eilig recalculation: price.total=8.34 (exactly 25% higher, ratio 1.250). TEST 6 - Status to Abholbereit: 200, response quick (0.128s, email async). TEST 7-8 - Validation: missing name/link -> 400. TEST 9 - Auth: PUT without auth -> 401. TEST 10 - GET /api/email-status with auth -> 200, ok:true. TEST 11 - No MongoDB _id leaks. All backend APIs working correctly. Ready for user acceptance."
    -agent: "main"
    -message: "NEUE FUNKTION: Auftrags-Reihenfolge aendern (PUT /api/orders/reorder + sortIndex, Queue-Bezug). Auftraege haben jetzt ein Feld 'sortIndex' (Warteschlangen-Reihenfolge). (1) GET /api/orders (Admin) sortiert nach sortIndex aufsteigend; fehlender sortIndex wird lazy aus createdAt migriert. (2) POST /api/orders setzt sortIndex=Date.now() -> neue Auftraege ans Ende. (3) NEU PUT /api/orders/reorder (Bearer Auth) body {orderedIds:[...]} setzt sortIndex=Index (0,1,2...) fuer alle IDs -> ohne Auth 401, leere Liste 400. (4) queueAhead im Track-Endpoint zaehlt jetzt offene Auftraege mit KLEINEREM sortIndex (=weiter vorne in der manuellen Reihenfolge) statt nach createdAt. Bitte testen: 3 Auftraege anlegen, GET /api/orders Reihenfolge notieren, PUT reorder mit umgekehrter ID-Reihenfolge, erneut GET -> neue Reihenfolge; Track eines hinteren offenen Auftrags -> queueAhead entspricht Anzahl offener Auftraege davor; nach reorder aendert sich queueAhead entsprechend."
    -agent: "testing"
    -message: "✅ REORDER FEATURE FULLY TESTED (7/7 scenarios passed). All scenarios from review request verified successfully. SCENARIO 1 - Created 3 orders A, B, C: POST /api/orders -> 200 OK, each with sortIndex=Date.now() (A=1783955373120, B=1783955374497, C=1783955375643), orderNumber (3D-XXXXXX), customerCode (8 chars), status='Eingegangen'. SCENARIO 2 - GET /api/orders (admin): Returns orders sorted by sortIndex ascending, verified A < B < C. SCENARIO 3 - Reorder: PUT /api/orders/reorder with Bearer auth, body {orderedIds:[C.id, A.id, B.id]} -> 200 OK, ok:true. GET /api/orders again: sortIndex updated to reflect new order (C.sortIndex=0, A.sortIndex=1, B.sortIndex=2), verified C < A < B. SCENARIO 4 - Queue position reflects manual order: GET /api/orders/track for C -> queueAhead=0 (first in queue), A -> queueAhead=1 (one ahead), B -> queueAhead=3 (three ahead). Verified queueAhead_C < queueAhead_A < queueAhead_B. SCENARIO 5 - Queue shrinks when ahead-order completed: PUT /api/orders/C.id {status:'Abgeschlossen'} with auth -> 200 OK. Track B again -> queueAhead decreased from 3 to 2 (C no longer counts). Track C -> queueAhead=0 (completed orders always 0). SCENARIO 6 - Auth & validation: PUT /api/orders/reorder without Authorization -> 401. PUT with auth but empty body {} -> 400. PUT with auth but empty orderedIds [] -> 400. SCENARIO 7 - Regression: No MongoDB _id leaks in GET /api/orders. GET /api/orders/track does NOT expose email (privacy maintained). Existing PUT /api/orders/:id (status update) -> 200 OK, status updated. Existing PUT /api/orders/:id (model update with grams/hours) -> 200 OK, price calculated correctly. Reorder route does not clash with generic PUT /api/orders/:id. All backend APIs working correctly. Ready for user acceptance."
    -agent: "testing"
    -message: "✅ NEW/CHANGED BEHAVIORS FULLY TESTED (8/8 scenarios passed). CRITICAL CHANGES VERIFIED: Sorting direction REVERSED from previous implementation. CHANGE 1 - Newest orders on top: GET /api/orders now sorts by sortIndex DESCENDING (line 587: b.sortIndex - a.sortIndex). Created order X (sortIndex=1784009272279), then Y (sortIndex=1784009273602). Y appears at index 0, X at index 1 (Y before X). Verified: newest orders appear at TOP. CHANGE 2 - Reorder direction REVERSED: PUT /api/orders/reorder with orderedIds=[X.id, Y.id, ...] (28 orders) assigns sortIndex = (n - index), so first id gets HIGHEST sortIndex (line 601: sortIndex: n - i). After reorder: X.sortIndex=28, Y.sortIndex=27, X at index 0 (top). Verified: first id in array = highest sortIndex = top. CHANGE 3 - queueAhead direction REVERSED: Now counts orders with LARGER sortIndex (line 470: key(o) > myKey). Track X (top) -> queueAhead=0. Track Y (below X) -> queueAhead=1. Verified: topmost open order has queueAhead=0, orders below have more ahead. NEW FEATURE 4 - Edit email: PUT /api/orders/:id {email:'jannik-druck@gmx.de'} -> 200 OK, email updated. PUT {email:''} -> 200 OK, email cleared. NEW FEATURE 5 - Manual status mail WITH email: POST /api/orders/:id/send-status-mail with auth -> 200 OK, ok:true (mail sent to jannik-druck@gmx.de). NEW FEATURE 6 - Manual status mail WITHOUT email: POST with auth but no email -> 200 OK, ok:false, error:'Für diesen Auftrag ist keine E-Mail-Adresse hinterlegt.' (German error). Auth checks: POST without auth -> 401. POST with nonexistent id -> 404. Regression: No MongoDB _id leaks, track does NOT expose email, generic PUT still works (status update + model update with price calculation), reorder route does not clash with generic PUT. All backend APIs working correctly. Ready for user acceptance."
    -agent: "testing"
    -message: "✅ UPDATED queueAhead DIRECTION VERIFIED (7/7 tests passed). CRITICAL CHANGE: queueAhead logic FLIPPED AGAIN to count orders with SMALLER sortIndex (older, printed earlier). This is the OPPOSITE of the previous test. Created 3 orders P, Q, R in sequence (P oldest, R newest). Verified sortIndex order: P.sortIndex=1784305700685 < Q.sortIndex=1784305701936 < R.sortIndex=1784305703299. Admin list sorted DESCENDING: R at index 0, Q at index 1, P at index 2 (newest on top). Tracked all three orders: P.queueAhead=26 (smallest), Q.queueAhead=27, R.queueAhead=28 (largest). Verified queueAhead(P) < queueAhead(Q) < queueAhead(R) - older orders have FEWER ahead, newer orders have MORE ahead. Marked P as 'Abgeschlossen' -> Q.queueAhead decreased from 27 to 26 (P no longer counts). Completed order P has queueAhead=0 (as expected). Code verification: line 470 in route.js uses 'key(o) < myKey' to count orders with SMALLER sortIndex. Regression: No email exposure in tracking (privacy maintained), no MongoDB _id leaks (security maintained). All backend APIs working correctly. queueAhead direction now matches specification: BOTTOM of admin list (oldest/smallest sortIndex) = next to print, order with SMALLEST sortIndex among open orders has SMALLEST queueAhead."
    -agent: "main"
    -message: "NEUE FUNKTION: SMS-Benachrichtigungen via Android SMS-Gateway. Optionales 'phone'-Feld im Auftrag. SMS bei Auftragseingang, Statuswechsel 'Druck läuft' und 'Abholbereit' (idempotent via smsSent). GET /api/sms-status (Admin) prüft Gateway-Verbindung. Bitte testen: (1) GET /api/sms-status mit/ohne Auth. (2) POST /api/orders OHNE phone -> 200. (3) PUT /api/orders/:id {phone:'0151...'} -> gespeichert, KEIN SMS bei reinem Feld-Update. (4) PUT {phone:''} -> leer. (5) PUT {email:'...'} -> funktioniert parallel. (6) GET /api/orders/track -> phone/email NICHT sichtbar. (7) Regression: kein _id leak, generic PUT funktioniert, schnelle Erstellung. WICHTIG: KEINE echten SMS senden (kostet Geld), nur Feld-Speicherung testen."
    -agent: "testing"
    -message: "✅ SMS NOTIFICATION FEATURE FULLY TESTED (7/7 scenarios passed). All scenarios from review request verified successfully. NO REAL SMS SENT (only field storage, config check, auth, and privacy tested as requested). SCENARIO 1 - SMS config check: GET /api/sms-status WITHOUT auth -> 401, WITH admin Bearer -> 200 {ok:true} (gateway credentials valid). SCENARIO 2 - Order without phone: POST /api/orders (NO phone, NO email) -> 200 ok:true, orderNumber (3D-791839), customerCode (YPP69KUW). SCENARIO 3 - Phone stored via field update: PUT /api/orders/:id {phone:'0151 23456789'} with auth -> 200 ok:true, phone stored and verified in admin list. NO SMS triggered by plain field update (no status change). SCENARIO 4 - Clear phone: PUT {phone:''} -> 200, phone empty. SCENARIO 5 - Email alongside: PUT {email:'jannik-druck@gmx.de'} -> 200, email set (no status change). SCENARIO 6 - Privacy: GET /api/orders/track?code=YPP69KUW -> 200, response does NOT contain 'phone' or 'email' fields (privacy maintained). SCENARIO 7 - Regression: No MongoDB _id leaks, generic PUT {adminNotes:'test'} -> 200 ok:true, order creation quick (1.006s). All backend APIs working correctly. SMS feature ready for production use."

