# Frontend API Contract Catalog (LLM Ready)

Last updated: 2026-04-11
Base URL: /api/v1
Auth: Bearer JWT unless marked AllowAny

## 1. Contract Rules

1. All write endpoints must surface field-level 400 validation messages in UI.
2. Treat 401 as refresh-then-retry-once.
3. Treat 403 as capability denial and hide action controls.
4. For list endpoints, support branch filters where documented.
5. For sync push, preserve idempotency_key per mutation.

## 2. Auth and Tenant

| Domain | Method | Path | Access | Request Minimum | Success Shape | Common Errors |
|---|---|---|---|---|---|---|
| Auth | POST | /auth/register-tenant | AllowAny | tenant_name, branch_name, username, password | tenant + branch + user + tokens | 400 duplicate tenant/username |
| Auth | POST | /auth/login | AllowAny | username, password | tokens + user | 401 invalid credentials |
| Auth | POST | /auth/login-pin | AllowAny | username, pin | tokens + user | 401 invalid, 403 pin missing, 423 locked |
| Auth | POST | /auth/refresh | AllowAny | refresh | access (and rotated refresh) | 401 token invalid |
| Auth | POST | /auth/logout | Authenticated | refresh | detail | 400 invalid token |
| User | GET/PATCH | /me | Authenticated | PATCH partial profile fields | user payload | 400 invalid values |
| Tenant | GET/PATCH | /tenant | Owner or Manager | PATCH tenant fields | tenant payload | 403 forbidden |
| Branch | GET/POST | /branches | Owner or Manager | POST name | branch payload/list | 403 forbidden |
| Branch | GET/PATCH/DELETE | /branches/{id} | Owner or Manager | PATCH name, active fields | branch payload | 404 missing |
| Subscriptions | GET | /subscription-plans | Authenticated | none | plan list | 401 unauthorized |
| Subscriptions | GET/PATCH | /subscription | Owner or Manager | PATCH plan/status fields | subscription payload | 403 forbidden |
| Feature Flags | GET/POST | /feature-flags | Owner or Manager | key, enabled | flag payload/list | 403 forbidden |
| Feature Flags | GET/PATCH/DELETE | /feature-flags/{id} | Owner or Manager | PATCH enabled/config | flag payload | 404 missing |
| Users | GET/POST | /users | Owner or Manager | create user fields | user payload/list | 400 role/branch, 403 |
| Users | GET/PATCH/DELETE | /users/{id} | Authenticated with tenant constraints | partial user fields | user payload | 403/404 |
| Users | POST | /users/{id}/set-pin | Authenticated (self or owner/manager) | pin | detail | 400 invalid format |
| Audit | GET | /activity-logs | Owner or Manager | optional limit | activity list | 403 forbidden |

## 3. Menu

| Method | Path | Access | Notes |
|---|---|---|---|
| GET/POST | /menu/categories | Owner or Manager | branch-scoped catalog |
| GET/PATCH/DELETE | /menu/categories/{id} | Owner or Manager | maintains category ordering |
| GET/POST | /menu/items | Owner or Manager | base item create |
| GET/PATCH/DELETE | /menu/items/{id} | Owner or Manager | active flag used in service flows |
| GET/POST | /menu/items/{item_id}/variants | Owner or Manager | size/version pricing |
| GET/PATCH/DELETE | /menu/variants/{id} | Owner or Manager | variant edit |
| GET/POST | /menu/items/{item_id}/addon-groups | Owner or Manager | grouped modifiers |
| GET/PATCH/DELETE | /menu/addon-groups/{id} | Owner or Manager | group config |
| GET/POST | /menu/addon-groups/{group_id}/items | Owner or Manager | selectable addons |
| GET/PATCH/DELETE | /menu/addon-items/{id} | Owner or Manager | addon edit |
| GET/POST | /menu/allergens | Owner or Manager | allergen dictionary |
| GET/PATCH/DELETE | /menu/allergens/{id} | Owner or Manager | allergen maintenance |
| GET/POST | /menu/schedules | Owner or Manager | time windows |
| GET/PATCH/DELETE | /menu/schedules/{id} | Owner or Manager | schedule update |
| GET | /customer/menu | AllowAny | customer-facing read model |

## 4. Tables and Seating

| Method | Path | Access | Notes |
|---|---|---|---|
| GET/POST | /floor-plans | Owner or Manager | visual floor map models |
| GET/PATCH/DELETE | /floor-plans/{id} | Owner or Manager | |
| GET/POST | /tables | Owner or Manager | table assets |
| GET/PATCH/DELETE | /tables/{id} | Owner or Manager | table metadata/state |
| GET | /tables/live-status | Owner or Manager | operational dashboard list |
| POST | /tables/{id}/open-session | Owner or Manager | shift/service session start |
| POST | /tables/{id}/close-session | Owner or Manager | close with consistency checks |
| POST | /tables/merge | Owner or Manager | merge table set |
| POST | /tables/split/{id} | Owner or Manager | split merged session |
| GET | /table-sessions | Owner or Manager | active/previous sessions |
| GET/POST | /reservations | Owner or Manager | reservation create/list |
| GET/PATCH/DELETE | /reservations/{id} | Owner or Manager | reservation detail |
| POST | /reservations/{id}/arrived | Owner or Manager | status transition |
| POST | /reservations/{id}/cancel | Owner or Manager | status transition |
| GET/POST | /waitlist | Owner or Manager | waitlist queue |
| GET/PATCH/DELETE | /waitlist/{id} | Owner or Manager | queue entry update |
| POST | /waitlist/{id}/call | Owner or Manager | notify guest |
| POST | /waitlist/{id}/seat | Owner or Manager | convert to seated state |
| POST | /waitlist/{id}/cancel | Owner or Manager | close entry |

## 5. Orders and Kitchen

| Method | Path | Access | Notes |
|---|---|---|---|
| GET/POST | /orders | Waiter or Above | waiter/cashier/manager/owner |
| GET/PATCH | /orders/{id} | Waiter or Above | order detail and mutable fields |
| POST | /orders/{id}/hold | Waiter or Above | OPEN -> HELD |
| POST | /orders/{id}/fire | Waiter or Above | creates kitchen tickets |
| POST | /orders/{id}/course/fire | Waiter or Above | course-level fire |
| POST | /orders/{id}/send-to-kitchen | Waiter or Above | explicit send action |
| POST | /orders/{id}/cancel | Owner or Manager | terminal action |
| POST | /orders/{id}/complete | Owner or Manager | terminal action |
| POST | /orders/{id}/call-waiter | Waiter or Above | service signal |
| POST | /orders/{id}/request-bill | Waiter or Above | billing handoff |
| GET | /orders/{id}/events | Waiter or Above | order timeline |
| POST | /orders/{id}/items | Waiter or Above | add line |
| PATCH/DELETE | /orders/{id}/items/{item_id} | Waiter or Above | update/remove line |
| GET | /kitchen/tickets | Waiter or Above | kitchen board source |
| POST | /kitchen/tickets/{id}/prepared | Waiter or Above | ticket transition |

## 6. Buffet, Takeaway, Loyalty

| Method | Path | Access | Notes |
|---|---|---|---|
| GET/POST | /buffet/plans | Owner or Manager | plan config |
| GET/PATCH | /buffet/plans/{id} | Owner or Manager | |
| POST | /buffet/sessions/start | Waiter or Above | starts buffet session |
| GET | /buffet/sessions/{id} | Waiter or Above | detail with rounds |
| POST | /buffet/sessions/{id}/new-round | Waiter or Above | round progression |
| POST | /buffet/sessions/{id}/close-round | Waiter or Above | close active round |
| POST | /buffet/sessions/{id}/end | Owner or Manager | terminal |
| POST | /waste-logs | Waiter or Above | penalty tracking |
| GET | /buffet/analytics | Owner or Manager | aggregated metrics |
| POST | /takeaway/orders | Waiter or Above | create takeaway flow |
| GET | /takeaway/orders/{id} | Waiter or Above | detail |
| POST | /takeaway/orders/{id}/ready | Waiter or Above | ready transition |
| GET | /loyalty/customers/{phone} | Waiter or Above | customer lookup |
| POST | /loyalty/visits | Waiter or Above | create visit |
| GET | /loyalty/eligibility | Waiter or Above | evaluate reward rules |

## 7. Billing and Fiscal

All billing and fiscal endpoints are Owner or Manager in current backend permission wiring.

| Method | Path |
|---|---|
| POST | /bills/create-from-order |
| GET | /bills/{id} |
| POST | /bills/{id}/apply-coperto |
| POST | /bills/{id}/apply-discount |
| POST | /bills/{id}/finalize |
| POST | /bills/{id}/pay |
| POST | /bills/{id}/send-to-fiscal |
| POST | /bills/{id}/split |
| GET | /receipts/{id} |
| POST | /receipts/{id}/reprint |
| POST | /receipts/{id}/refund |
| GET | /fiscal/z-report/status |
| POST | /fiscal/z-report/sync |
| POST | /integrations/bridge/fiscal-ack |

## 8. Inventory, Reports, Printers

All inventory/report/printer endpoints are Owner or Manager.

Inventory:
- /inventory/ingredients (+ detail)
- /inventory/recipes (+ detail)
- /inventory/movements
- /inventory/receivings
- /inventory/suppliers (+ detail)
- /inventory/purchase-orders (+ detail + /receive)
- /inventory/reports/low-stock
- /inventory/reports/usage

Reports:
- /reports/snapshots
- /reports/snapshots/refresh
- /reports/sales/by-category
- /reports/sales/by-table
- /reports/sales/by-waiter
- /reports/sales/by-vat
- /reports/buffet/branch-comparison
- /reports/cache/invalidate

Printers:
- /printers (+ detail)
- /printer-routes (+ detail)
- /print-jobs (+ detail)
- /print-jobs/reprint-ticket

## 9. Sync and Health

| Method | Path | Access | Notes |
|---|---|---|---|
| POST | /devices/register | Authenticated | any role |
| POST | /devices/heartbeat | Authenticated | any role |
| POST | /sync/push | Authenticated | idempotency_key required per item |
| POST | /sync/pull | Authenticated | cursor + limit paging |
| GET | /health | AllowAny | liveness |
| GET | /health/db | AllowAny | readiness |

## 10. Implementation Notes for LLMs

1. Generate typed request/response models per endpoint group.
2. Centralize auth retry and domain-specific error mapping.
3. Use one endpoint registry file and never hardcode paths in widgets.
4. Keep role guard checks mirrored in route guards and action-level UI disable rules.
5. For sync writes, always generate and store idempotency_key client-side before network call.
