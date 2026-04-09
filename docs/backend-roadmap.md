# Ristofy Backend Documentation

## 1. Purpose and Scope

This document defines the full backend implementation roadmap for Ristofy, based on the RMS specification for an Italian fiscal-compliant, cloud multi-tenant restaurant operating system.

The scope of this document covers:
- Django backend architecture
- Full domain model design
- API endpoint specification map
- Security and compliance controls
- Data consistency and integrity strategy
- Integration contracts with Go dispatcher and local bridge
- Phased delivery plan with quality gates

This is backend-first documentation. Flutter frontend, Go realtime dispatcher, and Go local bridge are covered only at their integration boundaries.

## 1.1 Current Implementation Status

- Phase 0: Completed
	- Environment-based settings, JWT baseline, CI checks, and git hygiene are in place.
- Phase 1: Completed
	- Tenant registration, branch management, role-aware user management, password/PIN login, logout, profile endpoint, session logging, and activity logs are implemented.
	- Automated tests cover key Phase 1 flows.
- Phase 2: Completed
	- Menu and dining layout foundations are implemented with CRUD endpoints for categories, items, floor plans, tables, reservations, and waitlist.
	- Allergen catalog, item-allergen mapping, and menu schedule windows are implemented.
	- Reservation and waitlist status actions are implemented with automatic table-state sync.
- Phase 3: Completed
	- Order and OrderItem models implemented with full status lifecycle.
	- POST/GET /api/v1/orders, GET/PATCH /api/v1/orders/{id}, POST /api/v1/orders/{id}/send-to-kitchen implemented.
	- POST /api/v1/orders/{id}/items, PATCH/DELETE /api/v1/orders/{id}/items/{item_id} implemented.
	- KitchenTicket model: auto-created on send-to-kitchen; GET /api/v1/kitchen/tickets, POST /api/v1/kitchen/tickets/{id}/prepared implemented.
	- Item snapshot (name/price/vat) captured at order creation time.
	- POST /orders/{id}/cancel and POST /orders/{id}/complete actions (OWNER/MANAGER only).
	- POST /orders/{id}/hold, /fire, /course/fire, /call-waiter, /request-bill implemented.
	- course field on OrderItem (STARTER, MAIN, DESSERT, DRINK, OTHER); one KitchenTicket per course on fire.
	- IsWaiterOrAbove permission applied to order create, list, detail, fire, and item endpoints.
	- order_no auto-incremented per branch with select_for_update concurrency safety.
	- Printer and PrintJob models in printers app; PrintJob queued per KitchenTicket on fire.
	- events.py stub publishes structured order events (Redis-ready, logs for now).
	- Tenant and branch isolation enforced. 66 tests passing.
- Phase 4: Completed
	- BuffetPlan CRUD: GET/POST /buffet/plans, GET/PATCH /buffet/plans/{id} (branch/is_active filters).
	- BuffetSession lifecycle: start (auto-computes ends_at), detail with nested rounds, end (auto-closes open round).
	- BuffetRound: new-round (enforces round limit and delay), close-round; end auto-closes open rounds.
	- WasteLog: POST /waste-logs with auto-penalty from buffet plan; marked_by set to caller.
	- GET /buffet/analytics with branch/date filters (sessions, guests, waste totals).
	- 98 tests passing (32 new buffet tests).

## 2. Target Tech Stack

- API and business backend: Django + Django REST Framework
- Database: PostgreSQL
- Queue and event backbone: Redis
- Async workers: Celery workers for long-running and retryable jobs
- Realtime dispatcher: Go service consuming Redis events and distributing realtime updates
- Local hardware bridge: Go service running on branch local PC for ESC/POS and fiscal RT communication

Why this combination:
- Django gives fast delivery of complex business logic and permissions
- PostgreSQL ensures strong relational consistency and reporting support
- Redis supports low-latency event distribution and queue semantics
- Go services isolate realtime and hardware concerns from core business APIs

## 3. High-Level Architecture

### 3.1 Core services
- Django API service
- PostgreSQL primary database
- Redis for pubsub and streams
- Celery worker and scheduler
- Go realtime dispatcher service
- Go local bridge service at each branch location

### 3.2 Responsibility boundaries
- Django owns source of truth, validation, permissions, billing, tenancy, and fiscal command lifecycle
- Go dispatcher owns websocket fan-out and durable delivery semantics for operational events
- Local bridge owns hardware adapters, offline local queues, printer and fiscal device communication

### 3.3 Tenant and branch isolation model
- Every business table includes tenant_id
- Operational tables also include branch_id where applicable
- All querysets are tenant-scoped by default
- Branch access is filtered through role policy
- Cross-tenant joins are forbidden by application constraints and review policy

## 4. Django App Structure

Recommended app ownership by domain:
- tenants: tenant, branch, subscription, feature flags
- users: users, roles, PIN auth, staff activity logs
- menu: categories, items, variants, allergens, schedules, add-ons
- tables: floor plans, tables, sessions, reservations, waitlist
- orders: orders, order items, courses, kitchen tickets, buffet sessions, waste logs
- billing: bills, discounts, payments, receipts, refunds, fiscal transactions
- printers: printers, route rules, print jobs, print audits
- inventory: ingredients, recipes, stock movements, suppliers, purchase flows
- reports: snapshots, KPI aggregates, report cache
- integrations (new): bridge callbacks, dispatcher hooks, event outbox

## 5. Domain Model Blueprint

Use UUID primary keys, created_at, updated_at, and optional deleted_at for soft deletable entities.

### 5.1 Tenancy and SaaS

#### Tenant
- id
- name
- legal_name
- vat_number
- tax_code
- timezone
- locale
- status

Constraints:
- unique vat_number
- status in active, suspended, closed

#### Branch
- id
- tenant_id
- name
- code
- address_line
- city
- province
- postal_code
- country
- phone
- email
- is_active

Constraints:
- unique tenant_id + code

#### SubscriptionPlan
- id
- code
- name
- monthly_price
- branch_limit
- device_limit
- feature_flags_json

#### TenantSubscription
- id
- tenant_id
- plan_id
- status
- starts_at
- ends_at
- billing_cycle
- trial_ends_at

#### FeatureFlag
- id
- tenant_id
- key
- enabled
- config_json

### 5.2 Users and Access Control

#### User
- id
- tenant_id
- branch_id nullable
- email
- phone
- username
- full_name
- role
- is_active
- last_login

Roles:
- owner
- manager
- cashier
- waiter
- kitchen

#### UserPinCredential
- id
- user_id
- pin_hash
- pin_rotated_at
- failed_attempts
- locked_until

#### RolePermission
- id
- tenant_id
- role
- permission_key
- is_allowed

#### UserSession
- id
- user_id
- refresh_jti
- device_id
- ip_address
- user_agent
- expires_at
- revoked_at

#### ActivityLog
- id
- tenant_id
- branch_id
- actor_user_id
- action
- entity_type
- entity_id
- before_json
- after_json
- created_at

### 5.3 Menu and Compliance

#### MenuCategory
- id
- tenant_id
- branch_id nullable
- name
- sort_order
- printer_target
- is_active

#### MenuItem
- id
- tenant_id
- branch_id nullable
- category_id
- sku
- name
- description
- base_price
- vat_rate
- is_buffet_included
- is_active

#### MenuVariant
- id
- menu_item_id
- name
- price_delta
- is_default

#### AddonGroup
- id
- menu_item_id
- name
- min_select
- max_select
- required

#### AddonItem
- id
- addon_group_id
- name
- price_delta
- vat_rate

#### Allergen
- id
- code
- name_it
- name_en
- name_de
- name_fr

#### MenuItemAllergen
- id
- menu_item_id
- allergen_id

#### MenuSchedule
- id
- branch_id
- category_id nullable
- menu_item_id nullable
- days_mask
- start_time
- end_time

### 5.4 Tables, Floor Plans, Reservations

#### FloorPlan
- id
- branch_id
- name
- width
- height
- layout_json
- is_active

#### DiningTable
- id
- branch_id
- floor_plan_id
- code
- seats
- x
- y
- state
- is_active

States:
- free
- occupied
- waiting_bill
- reserved

#### TableSession
- id
- branch_id
- table_id
- opened_by
- opened_at
- closed_at
- seat_map_json

#### TableMergeSession
- id
- branch_id
- primary_table_id
- merged_table_ids_json
- started_at
- ended_at

#### Reservation
- id
- branch_id
- customer_id
- table_id nullable
- party_size
- reserved_for
- status
- notes

#### WaitlistEntry
- id
- branch_id
- customer_id
- party_size
- quoted_wait_minutes
- status

### 5.5 Customers and Loyalty

#### Customer
- id
- tenant_id
- full_name
- phone
- email
- preferred_language
- marketing_consent

#### CustomerVisit
- id
- tenant_id
- branch_id
- customer_id
- visit_at
- order_id nullable
- spend_total

#### LoyaltyRule
- id
- tenant_id
- name
- rule_type
- threshold_value
- reward_type
- reward_value
- is_active

### 5.6 Orders, Courses, Buffet, Waste

#### Order
- id
- tenant_id
- branch_id
- order_no
- source
- mode
- table_session_id nullable
- customer_id nullable
- status
- notes

Source:
- waiter
- qr
- ipad
- takeaway

Mode:
- a_la_carte
- buffet
- hybrid

#### OrderItem
- id
- order_id
- seat_no nullable
- menu_item_id
- menu_variant_id nullable
- quantity
- unit_price
- vat_rate
- course
- status
- note

#### OrderItemAddon
- id
- order_item_id
- addon_item_id
- quantity
- unit_price

#### OrderEvent
- id
- order_id
- event_type
- payload_json
- actor_user_id nullable
- created_at

#### KitchenTicket
- id
- tenant_id
- branch_id
- order_id
- printer_id
- course
- status
- printed_at
- reprint_count

#### BuffetPlan
- id
- branch_id
- name
- base_price
- kids_price
- time_limit_minutes
- waste_penalty_amount
- round_limit_per_person
- round_delay_seconds
- include_rules_json
- exclude_rules_json
- active_from
- active_to

#### BuffetSession
- id
- tenant_id
- branch_id
- table_session_id
- buffet_plan_id
- adults_count
- kids_count
- started_at
- ends_at
- status

#### BuffetRound
- id
- buffet_session_id
- round_number
- opened_at
- closed_at
- item_count

#### WasteLog
- id
- tenant_id
- branch_id
- order_item_id
- quantity_wasted
- penalty_applied
- marked_by
- reason

### 5.7 Billing, Receipts, Fiscal

#### Bill
- id
- tenant_id
- branch_id
- bill_no
- order_id
- status
- subtotal
- vat_total
- coperto_total
- service_charge_total
- waste_total
- discount_total
- grand_total

#### BillLine
- id
- bill_id
- source_type
- source_id
- description
- quantity
- unit_price
- vat_rate
- line_total

#### BillSplit
- id
- bill_id
- split_type
- split_key
- amount

#### Discount
- id
- branch_id
- name
- discount_type
- value
- rules_json
- is_active

#### Payment
- id
- bill_id
- method
- amount
- currency
- status
- reference
- paid_at

#### Receipt
- id
- bill_id
- fiscal_receipt_no
- z_report_no nullable
- issued_at
- reprint_count

#### FiscalTransaction
- id
- branch_id
- bill_id nullable
- transaction_type
- request_json
- response_json
- status
- external_id
- error_code
- created_at

#### Refund
- id
- receipt_id
- amount
- reason
- status
- fiscal_refund_no
- created_at

### 5.8 Printers and Routing

#### Printer
- id
- branch_id
- name
- type
- target
- connection_mode
- ip
- port
- is_active

#### PrinterRouteRule
- id
- branch_id
- category_id nullable
- menu_item_id nullable
- course nullable
- printer_id
- priority

#### PrintJob
- id
- tenant_id
- branch_id
- printer_id
- job_type
- payload_json
- status
- attempts
- last_error
- queued_at
- sent_at
- acked_at

#### PrintJobAudit
- id
- print_job_id
- event
- details_json
- created_at

### 5.9 Inventory

#### Ingredient
- id
- tenant_id
- name
- unit
- reorder_level
- is_active

#### RecipeComponent
- id
- menu_item_id nullable
- menu_variant_id nullable
- ingredient_id
- quantity

#### StockLocation
- id
- branch_id
- name
- location_type

#### StockBatch
- id
- ingredient_id
- location_id
- quantity_on_hand
- unit_cost
- expires_at nullable

#### InventoryMovement
- id
- tenant_id
- branch_id
- ingredient_id
- location_id
- movement_type
- quantity
- reference_type
- reference_id
- before_qty
- after_qty
- reason
- created_at

#### Supplier
- id
- tenant_id
- name
- phone
- email

#### PurchaseOrder
- id
- branch_id
- supplier_id
- status
- ordered_at
- received_at

### 5.10 Reporting

#### ReportSnapshotDaily
- id
- tenant_id
- branch_id
- business_date
- totals_json

#### KpiHourly
- id
- tenant_id
- branch_id
- hour_bucket
- sales_amount
- order_count
- avg_ticket

#### ReportCache
- id
- tenant_id
- branch_id nullable
- report_key
- params_hash
- data_json
- expires_at

## 6. API Endpoint Map

All endpoints are under /api/v1 and require tenant-scoped auth unless explicitly public.

### 6.1 Auth and profile
- POST /api/v1/auth/register-tenant
- POST /api/v1/auth/login
- POST /api/v1/auth/login-pin
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- GET /api/v1/me
- PATCH /api/v1/me

### 6.2 Tenant, branch, subscriptions
- GET /api/v1/tenant
- PATCH /api/v1/tenant
- GET /api/v1/branches
- POST /api/v1/branches
- GET /api/v1/branches/{id}
- PATCH /api/v1/branches/{id}
- GET /api/v1/subscription
- POST /api/v1/subscription/change-plan
- GET /api/v1/feature-flags

### 6.3 Users, staff, permissions
- GET /api/v1/users
- POST /api/v1/users
- GET /api/v1/users/{id}
- PATCH /api/v1/users/{id}
- POST /api/v1/users/{id}/reset-pin
- GET /api/v1/roles/permissions
- PATCH /api/v1/roles/permissions
- GET /api/v1/activity-logs

### 6.4 Menu
- GET /api/v1/menu/categories
- POST /api/v1/menu/categories
- PATCH /api/v1/menu/categories/{id}
- GET /api/v1/menu/items
- POST /api/v1/menu/items
- GET /api/v1/menu/items/{id}
- PATCH /api/v1/menu/items/{id}
- POST /api/v1/menu/items/{id}/variants
- POST /api/v1/menu/items/{id}/addons/groups
- POST /api/v1/menu/items/{id}/allergens
- POST /api/v1/menu/items/{id}/recipe
- POST /api/v1/menu/schedules
- GET /api/v1/customer/menu

### 6.5 Tables and reservations
- GET /api/v1/floor-plans
- POST /api/v1/floor-plans
- PATCH /api/v1/floor-plans/{id}
- GET /api/v1/tables
- POST /api/v1/tables
- PATCH /api/v1/tables/{id}
- POST /api/v1/tables/{id}/open-session
- POST /api/v1/tables/{id}/close-session
- POST /api/v1/tables/merge
- POST /api/v1/tables/split
- GET /api/v1/tables/live-status
- GET /api/v1/reservations
- POST /api/v1/reservations
- PATCH /api/v1/reservations/{id}
- POST /api/v1/reservations/{id}/arrived
- POST /api/v1/reservations/{id}/cancel
- GET /api/v1/waitlist
- POST /api/v1/waitlist

### 6.6 Orders and kitchen flow
- GET /api/v1/orders
- POST /api/v1/orders
- GET /api/v1/orders/{id}
- PATCH /api/v1/orders/{id}
- POST /api/v1/orders/{id}/items
- PATCH /api/v1/orders/{id}/items/{item_id}
- DELETE /api/v1/orders/{id}/items/{item_id}
- POST /api/v1/orders/{id}/hold
- POST /api/v1/orders/{id}/fire
- POST /api/v1/orders/{id}/course/fire
- POST /api/v1/orders/{id}/call-waiter
- POST /api/v1/orders/{id}/request-bill
- GET /api/v1/kitchen/tickets
- POST /api/v1/kitchen/tickets/{id}/prepared

### 6.7 Buffet and waste
- GET /api/v1/buffet/plans
- POST /api/v1/buffet/plans
- PATCH /api/v1/buffet/plans/{id}
- POST /api/v1/buffet/sessions/start
- GET /api/v1/buffet/sessions/{id}
- POST /api/v1/buffet/sessions/{id}/new-round
- POST /api/v1/buffet/sessions/{id}/close-round
- POST /api/v1/buffet/sessions/{id}/end
- POST /api/v1/waste-logs
- GET /api/v1/buffet/analytics

### 6.8 Billing and fiscal
- POST /api/v1/bills/create-from-order
- GET /api/v1/bills/{id}
- POST /api/v1/bills/{id}/split
- POST /api/v1/bills/{id}/apply-discount
- POST /api/v1/bills/{id}/apply-coperto
- POST /api/v1/bills/{id}/finalize
- POST /api/v1/bills/{id}/send-to-fiscal
- GET /api/v1/receipts/{id}
- POST /api/v1/receipts/{id}/reprint
- POST /api/v1/receipts/{id}/refund
- GET /api/v1/fiscal/z-report/status
- POST /api/v1/fiscal/z-report/sync

### 6.9 Printers and jobs
- GET /api/v1/printers
- POST /api/v1/printers
- PATCH /api/v1/printers/{id}
- GET /api/v1/printer-routes
- POST /api/v1/printer-routes
- POST /api/v1/print-jobs/reprint-ticket
- GET /api/v1/print-jobs/{id}

### 6.10 Inventory and reports
- GET /api/v1/ingredients
- POST /api/v1/ingredients
- PATCH /api/v1/ingredients/{id}
- GET /api/v1/inventory/movements
- POST /api/v1/inventory/adjust
- POST /api/v1/inventory/receive
- GET /api/v1/inventory/low-stock
- GET /api/v1/reports/daily-sales
- GET /api/v1/reports/sales-by-category
- GET /api/v1/reports/sales-by-table
- GET /api/v1/reports/sales-by-waiter
- GET /api/v1/reports/vat
- GET /api/v1/reports/buffet
- GET /api/v1/reports/branch-comparison

### 6.11 Takeaway, loyalty, sync
- POST /api/v1/takeaway/orders
- GET /api/v1/takeaway/orders/{id}
- POST /api/v1/takeaway/orders/{id}/ready
- GET /api/v1/loyalty/customers/{phone}
- POST /api/v1/loyalty/visits
- GET /api/v1/loyalty/eligibility
- POST /api/v1/sync/push
- POST /api/v1/sync/pull
- POST /api/v1/devices/register
- POST /api/v1/devices/heartbeat

## 7. Security Architecture

### 7.1 Authentication and session security
- JWT access tokens with short expiry
- Rotating refresh tokens and JTI denylist
- Waiter PIN login with Argon2 hash
- PIN lockout after configurable failed attempts
- Device-aware sessions and forced logout support

### 7.2 Authorization
- Role-based access control with deny-by-default policy
- Endpoint-level and action-level permission checks
- Tenant and branch scope checks in every protected query
- Field-level masking for sensitive fiscal and audit fields

### 7.3 Transport and secrets
- TLS only, HSTS enabled in production
- CORS and CSRF rules by client type
- No hardcoded secrets in source code
- Environment-based secret loading and rotation policy

### 7.4 Abuse prevention
- Rate limits per IP, user, and tenant
- Brute force protection on password and PIN endpoints
- Idempotency key required for fiscal and billing finalize operations

### 7.5 Audit and compliance
- Immutable activity logs for critical actions
- Full trace of bill lifecycle and fiscal commands
- Receipt and refund auditability with user attribution

## 8. Data Consistency and Integrity Strategy

### 8.1 Transaction boundaries
- Use atomic transaction for each business command
- Use select_for_update on stock, table session, and bill finalize paths
- Ensure exactly-once semantics for external fiscal and print operations

### 8.2 Critical uniqueness constraints
- unique tenant_id + branch_id + order_no
- unique branch_id + bill_no
- unique branch_id + table code
- unique fiscal external_id

### 8.3 Check constraints
- quantity values greater than zero for order lines
- monetary totals not negative
- buffet time limits and round rules validated at write time

### 8.4 Concurrency handling
- Optimistic locking version field for editable order documents
- Retry-safe command handlers
- Idempotency key table for duplicate client retries

### 8.5 Ledger model
- Inventory movement is append-only
- Financial lines become immutable after fiscal issue
- Soft delete allowed only for non-fiscal configuration entities

## 9. Redis Event and Integration Contract

### 9.1 Event channels
- order.created
- order.updated
- order.fired
- ticket.print.requested
- fiscal.receipt.requested
- fiscal.receipt.completed
- table.status.changed

### 9.2 Event envelope
- event_id
- event_type
- tenant_id
- branch_id
- aggregate_id
- occurred_at
- schema_version
- payload

### 9.3 Bridge callback endpoints
- POST /api/v1/integrations/bridge/print-ack
- POST /api/v1/integrations/bridge/fiscal-ack
- POST /api/v1/integrations/bridge/health

### 9.4 Bridge trust model
- Signed HMAC headers or mTLS
- Clock-skew tolerant nonce validation
- Replay protection with one-time request IDs

## 10. Implementation Roadmap (16 Weeks)

### Phase 0 (Week 1): Platform foundation
- Environment separation and secrets baseline
- CI pipeline with tests, lint, migration checks
- API versioning and OpenAPI setup
- Base tenant middleware and audit utilities

### Phase 1 (Week 2-3): Tenant and identity
- Tenant registration and branch creation
- Role-based user management
- JWT and PIN login
- Session and activity logging

### Phase 2 (Week 4-5): Menu and dining layout
- Category and item management
- Allergens and schedule windows
- Floor plan and table lifecycle
- Reservation and waitlist basics

### Phase 3 (Week 6-7): Order core
- Order create and item lifecycle
- Hold and fire operations by course
- Kitchen ticket generation and printer routing requests
- Order status streams to realtime dispatcher

### Phase 4 (Week 8): Buffet and hybrid mode
- Buffet plan setup
- Session timers and round constraints
- Mixed buffet and a la carte per table support
- Waste logging and penalty calculations

### Phase 5 (Week 9): Billing engine
- Bill build from order
- Split by person and item
- Discount, coperto, service charge, waste penalties
- VAT-safe line and total calculations

### Phase 6 (Week 10): Fiscal integration
- Fiscal command orchestration model
- Local bridge callbacks and acknowledgement lifecycle
- Receipt ID storage and reprint/refund commands
- Z report sync structure

### Phase 7 (Week 11): Inventory integration
- Ingredient and recipe mapping
- Auto-deduction on accepted order items
- Manual adjustments and receiving flows
- Low stock alerts and movement history

### Phase 8 (Week 12): Takeaway and loyalty
- Takeaway order path and packaging fees
- Customer profile and visit history
- Loyalty eligibility endpoint

### Phase 9 (Week 13): Reporting
- Daily report snapshots
- Sales views by category, table, waiter, and VAT
- Buffet analytics and branch comparison
- Caching and refresh strategy

### Phase 10 (Week 14): Offline sync protocol
- Device registration and heartbeat
- Push and pull delta sync endpoints
- Conflict resolution policy and replay safety

### Phase 11 (Week 15-16): Hardening and release readiness
- Load and resilience tests
- Security scans and penetration test fixes
- Migration rehearsals and rollback plans
- Operational runbooks and production readiness review

## 11. Quality Gates and Definition of Done

For every phase:
- Unit and integration tests pass
- Migration is reversible or safely forward-fixable
- API contract tests green
- Security checks green
- Performance targets met for touched endpoints
- Observability includes logs, metrics, traces for new domain paths

Minimum quality thresholds:
- Core domain test coverage target: 85 percent
- p95 read APIs under 250 ms in staging baseline
- Order to print event under 1 second in normal operating load

## 12. Operations, Observability, and Reliability

### 12.1 Logging
- Structured JSON logs with request_id, tenant_id, branch_id, user_id
- Domain event logs for order and fiscal lifecycle transitions

### 12.2 Metrics
- API latency and error rates
- Queue lag and worker retry counts
- Printer and fiscal command success rate
- Inventory adjustment anomalies

### 12.3 Alerts
- Fiscal callback failures
- Queue backlog threshold breaches
- Elevated 5xx rates
- Missing branch heartbeat

### 12.4 Backup and recovery
- Daily snapshots and point-in-time recovery for PostgreSQL
- Disaster recovery runbook with RTO and RPO targets

## 13. Immediate Build Order for This Repository

Suggested next coding sequence in this repository:
1. Stabilize settings and environment strategy for local and production
2. Implement tenants app complete schema and migrations
3. Implement users app with role and PIN auth extension
4. Implement menu and tables apps with complete CRUD and validation
5. Implement orders domain with transactional command handlers
6. Implement billing and fiscal integration models and endpoints
7. Add printers and inventory integration
8. Finalize reports and sync endpoints

## 14. Open Decisions to Finalize Before Coding Deep

- Final role matrix per endpoint and per action
- Exact fiscal device protocol set supported at launch
- Whether tenant-level shared menu is allowed across branches
- How offline conflict resolution prioritizes device timestamps versus server timestamps
- Pricing policy for hybrid buffet plus a la carte at seat level

## 15. Notes for Production Safety

- Keep DEBUG false in production
- Do not commit credentials or static secret keys
- Keep database credentials in environment variables
- Restrict direct database access by network and credentials

---

Document status: Draft v1 for backend implementation
Source basis: RMS_Specification.pdf and agreed stack direction
