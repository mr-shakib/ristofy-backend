# Frontend Screen Contracts (Desktop)

Last updated: 2026-04-11

This file defines per-screen contracts for LLM-driven implementation.

## 1. Login Screen

Inputs:
- username
- password
- optional PIN login mode

Actions:
- POST /auth/login
- POST /auth/login-pin

States:
- idle
- loading
- invalid credentials
- pin locked (423)
- success

Success output:
- tokens stored
- navigate to session bootstrap

## 2. Session Bootstrap Screen

Actions (sequence):
1. GET /me
2. POST /devices/register
3. POST /devices/heartbeat
4. POST /sync/pull

States:
- bootstrap loading
- partial degraded mode
- ready

Output:
- role-specific home route

## 3. Waiter Floor Home

Data sources:
- GET /tables/live-status
- GET /table-sessions
- GET /waitlist
- GET /reservations

Actions:
- open table workspace
- seat waitlist entry
- call waitlist entry

UI requirements:
- color-coded table state
- fast refresh button
- branch filter (if multi-branch context)

## 4. Table Workspace

Data sources:
- GET /tables/{id}
- GET /orders?table={id} (if supported filter, otherwise client filter)

Actions:
- POST /tables/{id}/open-session
- POST /tables/{id}/close-session
- POST /tables/merge
- POST /tables/split/{id}

Guardrails:
- prevent duplicate open-session attempts
- confirm destructive actions

## 5. Order Composer

Data sources:
- GET /menu/categories
- GET /menu/items
- GET /orders/{id}
- GET /orders/{id}/events

Actions:
- POST /orders
- POST /orders/{id}/items
- PATCH/DELETE /orders/{id}/items/{item_id}
- POST /orders/{id}/hold
- POST /orders/{id}/fire
- POST /orders/{id}/course/fire
- POST /orders/{id}/send-to-kitchen
- POST /orders/{id}/request-bill

UI requirements:
- optimistic add item experience
- event timeline panel
- status-based action enable/disable

## 6. Kitchen Board

Data source:
- GET /kitchen/tickets

Actions:
- POST /kitchen/tickets/{id}/prepared

UI requirements:
- grouped by course/time priority
- quick prepared action
- auto-refresh interval with manual refresh

## 7. Cashier Billing Screen

Data sources:
- GET /bills/{id}
- GET /receipts/{id} when available

Actions:
- POST /bills/create-from-order
- POST /bills/{id}/apply-coperto
- POST /bills/{id}/apply-discount
- POST /bills/{id}/split
- POST /bills/{id}/finalize
- POST /bills/{id}/pay
- POST /bills/{id}/send-to-fiscal
- POST /receipts/{id}/reprint
- POST /receipts/{id}/refund

UI requirements:
- immutable view after finalize where applicable
- payment progress vs grand total
- fiscal submission status banner

## 8. Takeaway and Loyalty Screen

Data sources:
- GET /loyalty/customers/{phone}
- GET /loyalty/eligibility?phone=

Actions:
- POST /takeaway/orders
- GET /takeaway/orders/{id}
- POST /takeaway/orders/{id}/ready
- POST /loyalty/visits

UI requirements:
- fast phone lookup
- clear ready-state transition

## 9. Inventory Quick Ops Screen

Data sources:
- GET /inventory/reports/low-stock
- GET /inventory/ingredients
- GET /inventory/purchase-orders

Actions:
- POST /inventory/receivings
- POST /inventory/purchase-orders/{id}/receive

UI requirements:
- low-stock alerts first
- quick receive modal

## 10. Manager Reports Screen

Data sources:
- GET /reports/snapshots
- GET /reports/sales/by-category
- GET /reports/sales/by-table
- GET /reports/sales/by-waiter
- GET /reports/sales/by-vat
- GET /reports/buffet/branch-comparison

Actions:
- POST /reports/snapshots/refresh
- POST /reports/cache/invalidate

UI requirements:
- date range controls
- export-ready table views

## 11. Sync Health Screen

Data sources:
- GET /health
- GET /health/db
- local outbox metrics

Actions:
- POST /devices/heartbeat
- POST /sync/push
- POST /sync/pull

UI requirements:
- show online/offline status
- conflict count and drilldown
- last successful sync timestamp
