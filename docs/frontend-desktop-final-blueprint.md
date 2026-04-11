# Ristofy Frontend Desktop Final Blueprint

Last updated: 2026-04-11

## 1. Objective

Deliver a production-grade restaurant desktop app for branch operations, fully aligned with completed backend APIs and role permissions.

This document is the final implementation blueprint. It is designed so frontend development can start in a separate repository/workspace (not inside backend).

## 2. Mandatory Constraint

Frontend source code must be created outside this backend repository.

Recommended location examples:
- ../ristofy-frontend-desktop
- ~/projects/ristofy-frontend-desktop

## 3. Product Scope (Restaurant Side)

## 3.1 Roles

1. OWNER
- Tenant and branch administration
- Users and permissions
- Menu and pricing governance
- Financial and fiscal oversight
- Reports and operational monitoring

2. MANAGER
- Day-to-day branch operations
- Menu, tables, staffing activities
- Billing oversight and reporting

3. WAITER
- Table status management
- Reservation/waitlist seating actions
- Dine-in/takeaway order creation and lifecycle actions

4. CASHIER
- Bill creation and payment actions
- Coperto, discount, split bills
- Fiscal send/reprint/refund operations

5. KITCHEN
- Kitchen ticket queue
- Prepared actions only

## 3.2 Feature Modules

1. Authentication and session
2. Floor and table operations
3. Menu and ordering (dine-in + takeaway)
4. Kitchen production board
5. Billing and fiscal operations
6. Inventory quick operations (receiving, low stock visibility)
7. Reporting dashboard
8. Device registration and offline sync
9. System health and operations status

## 4. Recommended Tech Stack

For desktop with strong UX and maintainability:

1. App framework
- Flutter desktop (Windows + macOS)

2. Networking
- Dio HTTP client
- Strongly typed DTO models

3. State management
- Riverpod (or Bloc if your team standard is Bloc)

4. Local storage
- SQLite (drift/sqflite) for sync queue and cache

5. Routing
- go_router with role-aware guards

6. Observability
- Structured logs in app
- Error reporting integration (Sentry or equivalent)

## 5. Frontend Repository Structure (Target)

Suggested structure in the new frontend repo:

- lib/
  - app/
    - app.dart
    - router.dart
    - theme/
  - core/
    - api/
      - api_client.dart
      - auth_interceptor.dart
      - error_mapper.dart
    - storage/
      - local_db.dart
      - key_value_store.dart
    - sync/
      - outbox_queue.dart
      - sync_engine.dart
      - conflict_resolver.dart
    - models/
      - common pagination and response wrappers
  - features/
    - auth/
    - floor/
    - menu/
    - orders/
    - kitchen/
    - billing/
    - inventory/
    - reports/
    - settings/
  - shared/
    - widgets/
    - utils/

## 6. Screen Map (Desktop)

## 6.1 Entry and session

1. Login screen
- Username/password login
- PIN login option
- Remember last branch context

2. Session bootstrap
- Fetch me profile
- Device register (if first run)
- Device heartbeat
- Initial sync pull

## 6.2 Role home screens

1. Waiter Home
- Floor map with live table status
- Active orders list
- Reservation and waitlist panel

2. Kitchen Home
- Kitchen ticket board grouped by state and course
- Mark prepared action

3. Cashier Home
- Bills queue
- Payment panel
- Fiscal actions panel

4. Manager Home
- Operational metrics
- Alerts (low stock, sync conflicts, stuck print jobs)
- Reporting quick links

## 6.3 Primary workspaces

1. Table workspace
- Open/close table session
- Merge/split tables
- Create/edit order

2. Order composer
- Categories, items, variants, addons
- Hold/fire/course fire/send to kitchen
- Request bill and order event timeline

3. Billing workspace
- Create bill from order
- Apply coperto/discount
- Finalize, pay, split
- Send to fiscal, receipt reprint/refund

4. Takeaway workspace
- Customer lookup by phone
- Create takeaway order
- Mark ready
- Loyalty visit and eligibility check

5. Inventory mini workspace
- Receive stock quickly
- Low-stock alerts

6. Reports workspace
- Snapshots and sales dimensions
- Buffet branch comparison

## 7. End-to-End Flows with API Sequence

## 7.1 Opening shift flow

1. auth/login OR auth/login-pin
2. me
3. devices/register
4. devices/heartbeat
5. sync/pull
6. tables/live-status and startup datasets

## 7.2 Dine-in service flow

1. waitlist seat or direct table selection
2. tables/{id}/open-session
3. orders (create)
4. orders/{id}/items (add/update/remove)
5. orders/{id}/hold or fire or course/fire
6. kitchen/tickets and kitchen/tickets/{id}/prepared
7. orders/{id}/request-bill
8. bills/create-from-order
9. bills/{id}/apply-coperto and apply-discount (optional)
10. bills/{id}/finalize
11. bills/{id}/pay
12. bills/{id}/send-to-fiscal
13. tables/{id}/close-session

## 7.3 Takeaway flow

1. loyalty/customers/{phone} (optional lookup)
2. takeaway/orders (create)
3. orders/{id}/fire or send-to-kitchen
4. takeaway/orders/{id}/ready
5. bills/create-from-order and payment flow
6. loyalty/visits

## 7.4 Offline recovery flow

1. On network failure, write action to local outbox queue
2. sync/push retries with idempotency keys
3. sync/pull applies deltas by cursor
4. Conflict records shown in conflict queue panel
5. User resolves manually where required

## 8. API Domains to Implement

All routes are under /api/v1.

1. Auth/users/tenant
- auth/login, auth/login-pin, auth/refresh, auth/logout, me, users, activity-logs, branches, tenant, feature-flags, subscription

2. Menu
- menu/categories, menu/items, variants, addons, allergens, schedules, customer/menu

3. Floor and seating
- floor-plans, tables, tables/live-status, open-session, close-session, merge, split, table-sessions, reservations, waitlist

4. Orders and kitchen
- orders and all lifecycle actions, order items, order events, kitchen tickets, buffet and waste logs, takeaway and loyalty

5. Billing/fiscal
- bills and actions, receipts, fiscal z-report, bridge ack

6. Inventory/purchasing
- ingredients, recipes, movements, receivings, suppliers, purchase orders, reports

7. Reports
- snapshots, sales dimensions, buffet comparison, cache invalidate

8. Printers and sync
- printers, printer-routes, print-jobs, print-jobs/reprint-ticket, devices/register, devices/heartbeat, sync/push, sync/pull

9. Health
- health, health/db

## 9. Sync and Offline Design

## 9.1 Local data classes

1. Cached entities
- menu, tables, open orders, kitchen tickets, current shift reports

2. Outbox actions
- pending mutation requests with:
  - local_action_id
  - endpoint
  - method
  - payload
  - idempotency_key
  - created_at
  - retry_count
  - last_error

3. Cursor state
- per device and branch cursor for sync/pull

## 9.2 Retry policy

1. Retry classes
- immediate retry for transient failures
- exponential backoff for repeated failures
- hard stop and UI intervention after max attempts

2. Conflict behavior
- do not auto-overwrite server state on conflict
- show conflict details and comparison to user
- require explicit user action

## 10. Security and Session Handling

1. JWT access token in secure local storage
2. Refresh flow on 401 once, then force relogin if refresh fails
3. Never keep plain PIN in local storage
4. Logout should revoke refresh token and wipe secure session storage
5. Role-based guards on routes and action buttons

## 11. Error Handling Matrix

1. 400 Validation
- inline field-level error rendering
- preserve user form state

2. 401 Unauthorized
- attempt token refresh then retry once
- redirect to login when refresh fails

3. 403 Forbidden
- show permission message and hide unavailable action surfaces

4. 404 Not Found
- stale entity handling, refresh lists, navigate back safely

5. 423 PIN Locked
- clear lock countdown messaging and fallback to password login

6. 429 Rate Limited
- surface retry time and disable rapid action spam

7. 5xx Server errors
- retry when safe, otherwise queue mutation if offline strategy applies

## 12. Performance Targets

1. App startup to role dashboard under 3 seconds (warm cache)
2. Table live view refresh under 2 seconds perceived update
3. Order item add action UI response under 300 ms optimistic feedback
4. Sync push batch completion under 5 seconds for normal shift load

## 13. Testing Strategy

## 13.1 Automated

1. Unit tests
- serializers, mappers, sync engine logic, role guards

2. Widget/integration tests
- login flow, table open/order/fire, billing pay flow, kitchen prepared flow

3. Contract tests
- request/response schema checks against backend docs

## 13.2 Manual UAT

1. Peak-hour dine-in scenario
2. Takeaway burst scenario
3. Network drop and restore scenario
4. Fiscal send/reprint/refund scenario
5. End-of-day closure scenario

## 14. Release Plan

## Phase 1 (MVP Operations)

- Auth + role home
- Tables live status
- Dine-in order lifecycle
- Kitchen prepared flow
- Bill create/finalize/pay

Definition of done:
- A full dine-in cycle works without manual backend intervention.

## Phase 2 (Cashier + advanced operations)

- Discounts, coperto, split
- Fiscal flow
- Reservation/waitlist
- Takeaway + loyalty

Definition of done:
- Front-of-house daily operation complete.

## Phase 3 (Manager reliability)

- Reports dashboards
- Inventory quick operations
- Sync conflict panel
- Printer monitoring panel

Definition of done:
- App remains operational during unstable network and supports manager oversight.

## 15. Build Checklist for Frontend Team

1. Create new external repository for desktop app
2. Add CI with lint, test, and build targets for desktop platforms
3. Implement API client and auth interceptors first
4. Implement device registration and sync foundation before heavy feature modules
5. Deliver vertical slice: seat table to paid bill
6. Run staged UAT in a pilot branch

## 16. Final Notes

- Backend is complete and ready for frontend integration.
- This blueprint is the execution contract for the desktop frontend.
- Build frontend outside backend workspace as requested.
