# Session Handoff (Low-Token Starter)

Last updated: 2026-04-08

## 1) What Is Done

### Phase 0 (Completed)
- Environment-based configuration and security baseline in settings.
- CI checks and migration drift checks are active.
- Repo hygiene in place (.gitignore, docs flow, env template).

### Phase 1 (Completed)
- Tenant registration and branch creation.
- Role-aware user management.
- Password and PIN login.
- Token refresh/logout.
- Current-user profile endpoint.
- Session and activity logging.
- Test coverage for key auth/account flows.

### Phase 2 (Advanced / Near Complete)
- Menu:
  - Categories and items CRUD.
  - Allergen catalog CRUD.
  - Item-allergen mapping.
  - Menu schedule windows CRUD.
  - Filtering + pagination on list APIs.
- Dining layout:
  - Floor plans and tables CRUD.
  - Reservations CRUD.
  - Reservation status actions (arrived/cancel).
  - Overlap protection for active reservations.
  - Waitlist CRUD + status actions (call/seat/cancel).
  - Table state sync (reservation/waitlist aware).
- Test suite currently green (16 tests passing).

## 2) New Migrations In This Session

- menu/migrations/0002_allergen_menuitemallergen_menuitem_allergens_and_more.py
- tables/migrations/0003_waitlistentry.py

## 3) Current API Surface Added Recently

- /api/v1/menu/allergens
- /api/v1/menu/allergens/{id}
- /api/v1/menu/schedules
- /api/v1/menu/schedules/{id}
- /api/v1/waitlist
- /api/v1/waitlist/{id}
- /api/v1/waitlist/{id}/call
- /api/v1/waitlist/{id}/seat
- /api/v1/waitlist/{id}/cancel

For payloads and responses, use docs/api-postman-guide.md.

## 4) Known Open Item

- JWT warning about short HMAC key can appear in tests when env key is too short.
- Recommendation: keep signing key >= 32 chars in local and CI env.

## 5) Where To Start Next (Phase 3)

Start Phase 3: Order Core in the orders app.

Reason:
- orders app is still scaffold-only (models/views/tests placeholders).
- It is the highest-impact dependency for later billing, kitchen, and fiscal phases.

## 6) Exact Next Implementation Plan (Phase 3 - Slice 1)

### Step A: Create Order Domain Models
Implement in orders/models.py:
- Order
- OrderItem

Minimum fields for first slice:
- tenant, branch, table (nullable), waiter_user (nullable)
- status lifecycle: OPEN, SENT_TO_KITCHEN, PARTIALLY_SERVED, COMPLETED, CANCELED
- channel: DINE_IN, TAKEAWAY
- timestamps and notes
- OrderItem: order, menu_item snapshot name/price/vat, qty, status

### Step B: Add DRF Layer
- Create orders/serializers.py and orders/permissions.py (if needed).
- Create orders/views.py endpoints:
  - POST/GET /api/v1/orders
  - GET/PATCH /api/v1/orders/{id}
  - POST /api/v1/orders/{id}/send-to-kitchen
- Tenant-scoped querysets and branch validation are mandatory.

### Step C: Wire Routing
- Add orders/urls.py.
- Include orders URLs in core/urls.py under /api/v1/.

### Step D: Add Tests
- Create orders/tests.py API tests:
  - create order with items
  - list/filter by branch/status
  - send-to-kitchen action
  - tenant isolation and permission checks

### Step E: Keep Docs In Sync
- Update docs/api-postman-guide.md with new order endpoints.
- Update docs/backend-roadmap.md status notes for Phase 3 kickoff.

## 7) Next Session Quick Commands

Run at session start:

```bash
./venv/bin/python manage.py check
./venv/bin/python manage.py makemigrations --check --dry-run
./venv/bin/python manage.py test
```

During Phase 3 coding:

```bash
./venv/bin/python manage.py makemigrations orders
./venv/bin/python manage.py migrate
./venv/bin/python manage.py test orders
./venv/bin/python manage.py test
```

## 8) Copy-Paste Prompt For Next Session

Use this to start quickly with minimal token overhead:

"Continue from docs/session-handoff.md. Start Phase 3 Slice 1 (orders core) exactly as documented there. Implement models, serializers, views, urls, tests, migrations, and docs updates. Keep tenant/branch data isolation strict. Run check + makemigrations --check --dry-run + tests and report changed files and endpoint list."

## 9) Definition Of Done For Next Session

- Order core endpoints functional and tested.
- No pending migrations.
- All tests passing.
- Postman and roadmap docs updated in same change.
