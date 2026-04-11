# Frontend Role Capability Matrix

Last updated: 2026-04-11

This matrix is based on backend permission classes currently implemented in view files.

Roles:
- OWNER
- MANAGER
- WAITER
- CASHIER
- KITCHEN

## 1. Capability Matrix

| Capability Group | OWNER | MANAGER | WAITER | CASHIER | KITCHEN |
|---|---|---|---|---|---|
| Login/password/PIN/me/logout | Yes | Yes | Yes | Yes | Yes |
| User management and activity logs | Yes | Yes | No | No | No |
| Tenant/branch/subscription/feature flags | Yes | Yes | No | No | No |
| Menu management (categories/items/variants/addons/allergens/schedules) | Yes | Yes | No | No | No |
| Customer menu read model | Yes | Yes | Yes | Yes | Yes |
| Floor plans/tables/reservation/waitlist/table sessions | Yes | Yes | No | No | No |
| Order create/edit/fire/send/request-bill | Yes | Yes | Yes | Yes | No |
| Order cancel/complete | Yes | Yes | No | No | No |
| Kitchen tickets list/prepared (current backend) | Yes | Yes | Yes | Yes | No |
| Buffet plans/analytics | Yes | Yes | No | No | No |
| Buffet sessions/rounds/waste logs | Yes | Yes | Yes | Yes | No |
| Takeaway and loyalty | Yes | Yes | Yes | Yes | No |
| Billing/fiscal/splits/receipts | Yes | Yes | No | No | No |
| Inventory and purchasing | Yes | Yes | No | No | No |
| Reports and report cache ops | Yes | Yes | No | No | No |
| Printers/print routes/print jobs | Yes | Yes | No | No | No |
| Device register/heartbeat/sync push-pull | Yes | Yes | Yes | Yes | Yes |
| Health endpoints | Yes | Yes | Yes | Yes | Yes |

## 2. Important Product Decision

Current backend wiring does not expose dedicated KITCHEN-only permissions for kitchen ticket actions. KITCHEN role is currently excluded from IsWaiterOrAbove endpoints.

If the product requires KITCHEN users to handle /kitchen/tickets endpoints directly, backend permission classes must be adjusted before production rollout.

## 3. Frontend Guard Rules

1. Route-level guards
- Block entire modules by role before screen load.

2. Action-level guards
- Hide buttons for disallowed actions even when detail screen is visible.

3. Defensive handling
- Keep server-side 403 handling with user feedback because role policies can change.

## 4. Suggested Role Home Dashboards

1. OWNER
- Reports + billing monitor + branch admin shortcuts

2. MANAGER
- Floor operations + kitchen + cashier oversight + alerts

3. WAITER
- Floor live status + order composer + takeaway panel

4. CASHIER
- Bills queue + payment/fiscal + loyalty quick actions

5. KITCHEN
- For current backend permissions, kitchen users should use non-ticket operational surfaces only or permissions must be extended.
