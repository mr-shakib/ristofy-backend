# Ristofy Backend — Claude Code Guide

## Project Overview

Multi-tenant restaurant management system (RMS). Italian fiscal-compliant SaaS.
Stack: Django + DRF, PostgreSQL, Redis (future), Celery (future).
All business data is tenant-scoped. Branch-level isolation where applicable.

## Quick Start

```bash
./venv/bin/python manage.py check
./venv/bin/python manage.py makemigrations --check --dry-run
./venv/bin/python manage.py test
```

Run server:
```bash
./venv/bin/python manage.py runserver
```

## App Map

| App | Domain |
|-----|--------|
| `tenants` | Tenant, Branch, Subscription |
| `users` | User, PIN auth, session, activity logs |
| `menu` | Category, Item, Allergen, Schedule |
| `tables` | FloorPlan, DiningTable, Reservation, Waitlist |
| `orders` | Order lifecycle, OrderItem, KitchenTicket, Buffet flows |
| `billing` | Bill, Payment, Receipt, FiscalTransaction, Refund |
| `printers` | Printer, PrintJob (Phase 6+) |
| `inventory` | Ingredient, RecipeComponent, StockMovement, receiving + usage analytics |
| `reports` | Snapshots, KPIs (Phase 9+) |

## Implementation Status

- **Phase 0** — Complete: env config, CI, git hygiene
- **Phase 1** — Complete: auth (JWT + PIN), users, sessions, activity logs
- **Phase 2** — Complete: menu CRUD, allergens, schedules, floor plans, tables, reservations, waitlist
- **Phase 3** — Complete: order lifecycle, item sub-endpoints, kitchen tickets, course fire, waiter flows, printer job queueing
- **Phase 4** — Complete: buffet plans/sessions/rounds, waste logging, buffet analytics
- **Phase 5** — Complete: billing core (bill creation from order, coperto/discount/finalize/pay)
- **Phase 6** — Complete: fiscal integration API (send-to-fiscal, receipt actions, z-report, bridge fiscal ack)
- **Phase 7** — Complete: inventory core + recipe mapping + receiving flow + usage analytics + fire-flow auto-deduction
- **Phase 8** — Next: takeaway and loyalty

## Coding Conventions

### Tenant/Branch Isolation (Mandatory)
Every queryset must be scoped to `request.user.tenant`:
```python
MyModel.objects.filter(branch__tenant=request.user.tenant)
# or for tenant-level models:
MyModel.objects.filter(tenant=request.user.tenant)
```

Cross-tenant joins are forbidden.

### Serializer Validation Pattern
Always validate branch belongs to caller's tenant:
```python
def validate(self, attrs):
    request = self.context["request"]
    branch = attrs.get("branch", getattr(self.instance, "branch", None))
    if branch and branch.tenant_id != request.user.tenant_id:
        raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})
    return attrs
```

### View Pattern
- List/Create: `generics.ListCreateAPIView` with `pagination_class = StandardResultsSetPagination`
- Detail: `generics.RetrieveUpdateDestroyAPIView`
- Actions: `APIView` with explicit `post(self, request, pk)`
- Always `permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]`
- Always call `log_activity(...)` on create/update/delete

### Permissions
- `IsOwnerOrManager` — in `users/permissions.py` — roles: `OWNER`, `MANAGER`
- Future: waiter-level endpoints will need a separate permission class

### Pagination
Use `core.pagination.StandardResultsSetPagination` on all list views.

### Activity Logging
```python
from users.audit import log_activity

log_activity(
    actor_user=self.request.user,
    action="order_created",
    entity_type="order",
    entity_id=str(instance.id),
    tenant=self.request.user.tenant,
    branch=instance.branch,
)
```

### URL Wiring
Add app URLs in `core/urls.py`:
```python
path('api/v1/', include('orders.urls')),
```

## File Naming Conventions
Each app has: `models.py`, `serializers.py`, `views.py`, `urls.py`, `tests.py`, `migrations/`

## Documentation Rules (Non-Negotiable)
Every endpoint change must update **all three** in the same task:
1. `docs/api-postman-guide.md` — payload + response examples
2. `docs/backend-roadmap.md` — phase status
3. `docs/session-handoff.md` — next session context

See `docs/README.md` for the rule.

## Testing
Tests use Django `TestCase`. Pattern:
- Create tenant + branch + owner user via `RegisterTenantView` or direct model creation
- Login to get JWT
- Use `self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")`
- Test happy path, permission checks, and tenant isolation

Run a specific app: `./venv/bin/python manage.py test orders`

## Known Issues
- JWT HMAC key warning in tests when `SECRET_KEY` < 32 chars (env-only, not a code bug)
- Default project `.venv` is Python 3.11, while pinned `Django==6.0.4` requires Python 3.12+
- PrintJob transport is still pending; jobs are queued but not yet delivered through real bridge/device integration

## Next Phase Plan (Phase 8)
See `docs/session-handoff.md` §5 for current implementation priority.

Targets for next implementation slice:
- Takeaway order lifecycle endpoints
- Packaging/extra fee application rules
- Customer loyalty profile and visit tracking
- Loyalty eligibility endpoint with tenant/branch isolation tests
