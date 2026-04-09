# Session Handoff (Low-Token Starter)

Last updated: 2026-04-09

## 1) What Is Done

### Phase 0 (Completed)
- Environment-based configuration and security baseline in settings.
- CI checks and migration drift checks are active.

### Phase 1 (Completed)
- Tenant registration, branch creation, role-aware user management.
- Password and PIN login, token refresh/logout, profile endpoint.
- Session and activity logging.

### Phase 2 (Completed)
- Menu: Categories and items CRUD, allergens, schedules, filtering + pagination.
- Dining layout: Floor plans, tables, reservations + status actions, waitlist + status actions, table state sync.

### Phase 3 (Completed)
- Order and OrderItem models with full status lifecycle (OPEN → HELD → SENT_TO_KITCHEN → PARTIALLY_SERVED → COMPLETED → CANCELED).
- OrderItem course field: STARTER, MAIN, DESSERT, DRINK, OTHER.
- order_no: auto-incremented per branch (select_for_update safe), unique constraint.
- POST /api/v1/orders — create with items.
- GET /api/v1/orders — list with branch/status/channel filters + pagination.
- GET/PATCH /api/v1/orders/{id}.
- POST /api/v1/orders/{id}/hold — OPEN → HELD.
- POST /api/v1/orders/{id}/fire — fires all PENDING items, one KitchenTicket + PrintJob per course.
- POST /api/v1/orders/{id}/course/fire — fires PENDING items for one course only.
- POST /api/v1/orders/{id}/send-to-kitchen — legacy alias for fire (backward compat).
- POST /api/v1/orders/{id}/cancel — OWNER/MANAGER only.
- POST /api/v1/orders/{id}/complete — OWNER/MANAGER only.
- POST /api/v1/orders/{id}/call-waiter — logs event, realtime-ready stub.
- POST /api/v1/orders/{id}/request-bill — logs event, sets table to WAITING_BILL.
- POST /api/v1/orders/{id}/items, PATCH/DELETE /api/v1/orders/{id}/items/{item_id}.
- GET /api/v1/kitchen/tickets (filters: branch, status, course).
- POST /api/v1/kitchen/tickets/{id}/prepared.
- Printer + PrintJob models in printers app (foundation for Phase 6 printer management API).
- orders/events.py: publish_order_event() stub — structured envelope, Redis-ready.
- IsWaiterOrAbove permission class in users/permissions.py.
- 66 tests passing.

## 2) All Migrations

- orders/migrations/0001_initial.py
- orders/migrations/0002_kitchenticket.py
- orders/migrations/0003_order_order_no_order_uniq_order_no_per_branch.py
- orders/migrations/0004_alter_orderitem_options_kitchenticket_course_and_more.py
- printers/migrations/0001_initial.py

## 3) Full Orders API Surface

- GET/POST /api/v1/orders
- GET/PATCH /api/v1/orders/{id}
- POST /api/v1/orders/{id}/hold
- POST /api/v1/orders/{id}/fire
- POST /api/v1/orders/{id}/course/fire  — body: `{"course": "MAIN"}`
- POST /api/v1/orders/{id}/send-to-kitchen  (legacy)
- POST /api/v1/orders/{id}/cancel
- POST /api/v1/orders/{id}/complete
- POST /api/v1/orders/{id}/call-waiter
- POST /api/v1/orders/{id}/request-bill
- POST /api/v1/orders/{id}/items
- PATCH/DELETE /api/v1/orders/{id}/items/{item_id}
- GET /api/v1/kitchen/tickets
- POST /api/v1/kitchen/tickets/{id}/prepared

## 4) Known Open Item

- JWT HMAC key warning in tests when SECRET_KEY < 32 chars (env-only, not a code issue).
- publish_order_event() currently logs only — wire to Redis XADD when dispatcher is ready.
- PrintJob.status stays QUEUED — Go bridge will PATCH to SENT/FAILED via /api/v1/integrations/bridge/print-ack (Phase 6).

## 5) Where To Start Next (Phase 4 — Buffet)

### Step A: BuffetPlan model
- Fields: branch, name, base_price, kids_price, time_limit_minutes, waste_penalty_amount, round_limit_per_person, round_delay_seconds, active_from, active_to, is_active
- CRUD: GET/POST /api/v1/buffet/plans, GET/PATCH /api/v1/buffet/plans/{id}

### Step B: BuffetSession model
- Fields: tenant, branch, order (FK), buffet_plan, adults_count, kids_count, started_at, ends_at, status (ACTIVE/ENDED)
- POST /api/v1/buffet/sessions/start
- GET /api/v1/buffet/sessions/{id}
- POST /api/v1/buffet/sessions/{id}/end

### Step C: BuffetRound model
- Fields: buffet_session, round_number, opened_at, closed_at
- POST /api/v1/buffet/sessions/{id}/new-round
- POST /api/v1/buffet/sessions/{id}/close-round

### Step D: WasteLog model
- Fields: tenant, branch, order_item, quantity_wasted, penalty_applied, marked_by, reason
- POST /api/v1/waste-logs
- GET /api/v1/buffet/analytics

## 6) Next Session Quick Commands

```bash
./venv/bin/python manage.py check
./venv/bin/python manage.py makemigrations --check --dry-run
./venv/bin/python manage.py test
```

## 7) Copy-Paste Prompt For Next Session

"Continue from docs/session-handoff.md. Phase 3 is complete. Implement Phase 4: BuffetPlan CRUD, BuffetSession lifecycle (start/end), BuffetRound (new-round/close-round), and WasteLog. Keep tenant/branch isolation strict. Run check + makemigrations --check --dry-run + tests and report changed files and endpoint list."

## 8) Definition Of Done For Phase 4

- Buffet plan CRUD, session start/end, round new/close, waste log functional and tested.
- No pending migrations.
- All tests passing.
- Postman and roadmap docs updated.
