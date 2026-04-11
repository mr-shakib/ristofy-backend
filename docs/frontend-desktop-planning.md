# Frontend Desktop Planning (Restaurant Side)

Last updated: 2026-04-11

## 1) Goal

Build a production-ready restaurant desktop app that covers service operations end-to-end:
- staff login and session handling
- table and floor operations
- dine-in and takeaway order execution
- kitchen workflow
- cashier and billing/fiscal actions
- manager reporting and administration
- offline-safe sync behavior for unstable networks

This document is the implementation plan for frontend scope and API consumption.

## 2) Recommended Product Scope

## 2.1 Personas and role-based app surfaces

1. Owner/Manager
- Branch setup and configuration
- Menu, pricing, variants, addons, schedules
- Floor/table setup and reservation policy
- Reports and shift oversight
- Users, feature flags, subscription visibility

2. Waiter
- Table live status and seating flow
- Open order, add/edit items, hold/fire/request bill
- Reservation/waitlist handling
- Takeaway intake and ready marking (if enabled)

3. Cashier
- Bill creation from order
- Coperto, discount, split, payment collection
- Fiscal send/reprint/refund operations
- Loyalty visit recording and eligibility checks

4. Kitchen
- Kitchen ticket queue
- Mark ticket prepared
- No access to billing/admin surfaces

## 2.2 Functional modules

1. Auth and session
- Login, PIN login, token refresh, logout, profile

2. Service floor
- Floor plans, table states, open/close sessions, merge/split, reservations, waitlist

3. Menu and ordering
- Categories/items/variants/addons/allergens/schedules
- Dine-in order lifecycle + course fire
- Takeaway workflows

4. Kitchen production
- Ticket board and prepared actions

5. Billing and fiscal
- Bill actions, split, payment, receipt lifecycle, z-report endpoints

6. Inventory and purchasing
- Ingredients, stock movements, receiving, suppliers, purchase orders

7. Reporting and analytics
- Snapshot list/refresh and sales aggregations

8. Device sync and reliability
- Device register/heartbeat + push/pull delta sync

9. Operations and diagnostics
- Health checks and throttling-aware error UX

## 3) API Domain Map for Frontend

All endpoints are mounted under /api/v1.

1. Tenant and branch administration
- auth/register-tenant
- tenant
- branches (+ detail)
- subscription-plans
- subscription
- feature-flags (+ detail)

2. User and authentication
- auth/login
- auth/login-pin
- auth/logout
- auth/refresh
- me
- users (+ detail)
- users/{id}/set-pin
- activity-logs

3. Menu
- menu/categories (+ detail)
- menu/items (+ detail)
- menu/items/{id}/variants, menu/variants/{id}
- menu/items/{id}/addon-groups, menu/addon-groups/{id}
- menu/addon-groups/{id}/items, menu/addon-items/{id}
- menu/allergens (+ detail)
- menu/schedules (+ detail)
- customer/menu (public read)

4. Tables and seating
- floor-plans (+ detail)
- tables (+ detail)
- tables/live-status
- tables/{id}/open-session
- tables/{id}/close-session
- tables/merge
- tables/split/{id}
- table-sessions
- reservations (+ detail + arrived/cancel)
- waitlist (+ detail + call/seat/cancel)

5. Orders and kitchen
- orders (+ detail)
- orders/{id}/hold, fire, course/fire, send-to-kitchen, cancel, complete
- orders/{id}/call-waiter, request-bill, events
- orders/{id}/items (+ item detail update/delete)
- kitchen/tickets
- kitchen/tickets/{id}/prepared
- buffet/plans and buffet/sessions endpoints
- waste-logs
- buffet/analytics
- takeaway/orders (+ detail + ready)
- loyalty/customers/{phone}
- loyalty/visits
- loyalty/eligibility

6. Billing and fiscal
- bills/create-from-order
- bills/{id}
- bills/{id}/apply-coperto
- bills/{id}/apply-discount
- bills/{id}/finalize
- bills/{id}/pay
- bills/{id}/send-to-fiscal
- bills/{id}/split
- receipts/{id}
- receipts/{id}/reprint
- receipts/{id}/refund
- fiscal/z-report/status
- fiscal/z-report/sync
- integrations/bridge/fiscal-ack

7. Inventory and purchasing
- inventory/ingredients (+ detail)
- inventory/recipes (+ detail)
- inventory/movements
- inventory/receivings
- inventory/suppliers (+ detail)
- inventory/purchase-orders (+ detail + receive)
- inventory/reports/low-stock
- inventory/reports/usage

8. Reports
- reports/snapshots
- reports/snapshots/refresh
- reports/sales/by-category
- reports/sales/by-table
- reports/sales/by-waiter
- reports/sales/by-vat
- reports/buffet/branch-comparison
- reports/cache/invalidate

9. Printers and sync
- printers (+ detail)
- printer-routes (+ detail)
- print-jobs (+ detail)
- print-jobs/reprint-ticket
- devices/register
- devices/heartbeat
- sync/push
- sync/pull

10. Health and readiness
- health
- health/db

## 4) Core Operational Flows (Desktop UX)

## 4.1 Opening shift flow

1. Staff login (password or PIN)
2. Device registration + heartbeat bootstrap
3. Pull latest deltas (menu, table state, open orders)
4. Load role-specific home dashboard

## 4.2 Dine-in service flow

1. Host seats guest from waitlist or direct table assign
2. Waiter opens table session (if not open)
3. Waiter creates order and adds items
4. Waiter holds or fires items by course
5. Kitchen marks tickets prepared
6. Waiter requests bill when guest asks
7. Cashier creates bill from order and applies pricing rules
8. Cashier finalizes, collects payment, and sends fiscal receipt
9. Table session closed and table released

## 4.3 Takeaway flow

1. Search customer by phone (or create on first order)
2. Create takeaway order with packaging/extra fees
3. Fire to kitchen
4. Mark takeaway ready
5. Bill, pay, and optionally log loyalty visit

## 4.4 Offline and recovery flow

1. Local action queue stores pending writes with idempotency keys
2. Background sync push sends queued updates
3. Pull brings server-side deltas
4. Conflict items marked for manual review (server-wins)
5. UI surfaces clear conflict resolution panel per entity

## 4.5 End-of-day flow

1. Ensure all active orders are completed or canceled
2. Run z-report status/sync checks
3. Refresh snapshots and manager report views
4. Confirm no stuck print jobs and no unsynced local actions

## 5) Frontend Architecture Plan

## 5.1 App shell and technical baseline

Recommended baseline for desktop:
- Flutter desktop app (macOS/Windows) with strongly typed API client
- Local persistence (SQLite or Isar) for offline queue and cache
- Background sync engine with retry/backoff
- Role-gated route guards and feature-flag aware navigation

## 5.2 State boundaries

1. Session state
- user, role, branch, token status

2. Operational state
- live tables, active orders, kitchen queue

3. Catalog state
- menu, variants, addons, allergens, schedule windows

4. Financial state
- bills, receipts, payment attempts, fiscal statuses

5. Sync state
- outbox queue, cursor, heartbeat status, conflict count

## 5.3 Reliability rules

- Every write operation should include dedupe-safe local tracking key.
- All retryable failures should be queued, not dropped.
- Unauthorized responses should trigger refresh flow, then forced relogin when refresh fails.
- Conflict responses should not be auto-overwritten silently.

## 6) API Documentation Completion Plan (Frontend-First)

Current backend docs are strong, but frontend delivery requires a strict endpoint contract pack.

Create and maintain these four artifacts:

1. Endpoint catalog spreadsheet
Columns:
- Domain
- Method
- Path
- Role access
- Required request fields
- Response shape summary
- Pagination/filter params
- Error codes
- Idempotent? (yes/no)

2. State transition catalog
- Order status transitions
- Table state transitions
- Bill status transitions
- Ticket status transitions
- Device sync statuses (accepted/conflict)

3. Error handling matrix
- 400 validation (field-specific)
- 401/403 auth-role handling
- 404 stale UI references
- 409/400 conflict semantics for sync
- 423 PIN lock behavior
- 429 throttle handling and retry UX

4. Role capability matrix
- OWNER
- MANAGER
- WAITER
- CASHIER
- KITCHEN

## 7) Delivery Phases for Desktop App

## Phase A (2-3 weeks): Operations MVP

- Auth (password/PIN), session bootstrap
- Floor + tables live status
- Order create/edit/fire
- Kitchen board prepared flow
- Basic bill create/pay

Exit criteria:
- One dine-in order can complete from seating to payment without manual backend calls.

## Phase B (2-3 weeks): Cashier and controls

- Discount/coperto/finalize/fiscal send
- Reservation/waitlist integration
- Takeaway + loyalty flows
- Error and retry UX hardening

Exit criteria:
- Full front-of-house operations covered for peak-hour simulation.

## Phase C (2-3 weeks): Manager and reliability

- Reports dashboard
- Inventory receiving and low-stock visibility
- Printer queue visibility and reprint action
- Offline sync queue + conflict panel

Exit criteria:
- Branch can continue operations through short network interruptions.

## 8) Immediate Next Actions (This Week)

1. Freeze MVP scope to Phase A only.
2. Build endpoint catalog and role matrix from backend routes.
3. Define typed API contracts for all Phase A endpoints.
4. Design wireframes for:
- login and branch selection
- live floor map
- order composer
- kitchen ticket board
- cashier payment panel
5. Implement one vertical slice: seat table -> open order -> fire -> prepared -> bill -> pay.

## 9) Success Metrics

- Service speed: first order creation in less than 20 seconds from table click.
- Reliability: zero lost write actions during transient network failures.
- Financial correctness: billed total equals backend grand total in all payment scenarios.
- Operational clarity: staff can complete shift workflows without using Postman/admin panel.
