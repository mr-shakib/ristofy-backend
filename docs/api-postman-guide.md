# API Testing Guide (Postman)

## Purpose

This is the living API testing document for the project. Update this file every time an endpoint, serializer, or permission changes.

## Base Information

- API base URL (local): http://127.0.0.1:8000/api/v1
- Current API version: v1
- Auth type: JWT Bearer token
- Token refresh: SimpleJWT refresh endpoint

## 1. Postman Setup

### 1.1 Create a Postman Environment

Create an environment named RMS Local with these variables:

- base_url = http://127.0.0.1:8000/api/v1
- access_token =
- refresh_token =
- user_id =
- branch_id =
- category_id =
- item_id =
- floor_plan_id =
- table_id =
- reservation_id =
- allergen_id =
- schedule_id =
- waitlist_id =
- ingredient_id =
- movement_id =
- recipe_id =
- takeaway_id =
- customer_phone =

### 1.2 Common Headers

For protected endpoints, add:

- Authorization: Bearer {{access_token}}
- Content-Type: application/json

For public endpoints:

- Content-Type: application/json

### 1.3 Recommended Collection Structure

- Auth
- Tenants
- Users
- Menu
- Tables
- Orders
- Billing + Fiscal
- Inventory

## 2. Quick End-to-End Test Flow in Postman

Run requests in this order:

1. Register tenant owner account
2. Login with username and password
3. Get profile (me)
4. Get branches
5. Create branch
6. Get users
7. Create user
8. Set PIN for a user
9. Login with PIN
10. Get activity logs
11. Refresh token
12. Logout
13. Create menu category
14. Create menu item
15. Create floor plan
16. Create table
17. Create reservation
18. Create allergen and attach to menu item
19. Create menu schedule window
20. Create waitlist entry
21. Call and seat waitlist entry

## 3. Endpoint Documentation

## 3.1 Register Tenant

- Method: POST
- URL: {{base_url}}/auth/register-tenant
- Auth: No

Request body:

```json
{
  "tenant_name": "Demo Tenant",
  "branch_name": "Main Branch",
  "username": "owner_demo",
  "email": "owner@example.com",
  "password": "StrongPass123",
  "first_name": "Demo",
  "last_name": "Owner"
}
```

Success response (201):

```json
{
  "tenant": {
    "id": 10,
    "name": "Demo Tenant",
    "created_at": "2026-04-08T09:43:36.266852Z",
    "updated_at": "2026-04-08T09:43:36.266859Z"
  },
  "branch": {
    "id": 20,
    "tenant": 10,
    "name": "Main Branch",
    "created_at": "2026-04-08T09:43:36.268053Z",
    "updated_at": "2026-04-08T09:43:36.268056Z"
  },
  "user": {
    "id": 30,
    "username": "owner_demo",
    "role": "OWNER"
  },
  "tokens": {
    "refresh": "<jwt_refresh_token>",
    "access": "<jwt_access_token>"
  }
}
```

Common errors:

- 400 when tenant name already exists
- 400 when username is already taken

Example 400:

```json
{
  "tenant_name": [
    "A tenant with this name already exists."
  ]
}
```

## 3.2 Login (Username/Password)

- Method: POST
- URL: {{base_url}}/auth/login
- Auth: No

Request body:

```json
{
  "username": "owner_demo",
  "password": "StrongPass123"
}
```

Success response (200):

```json
{
  "tokens": {
    "refresh": "<jwt_refresh_token>",
    "access": "<jwt_access_token>"
  },
  "user": {
    "id": 30,
    "username": "owner_demo",
    "email": "owner@example.com",
    "first_name": "Demo",
    "last_name": "Owner",
    "role": "OWNER",
    "tenant": 10,
    "tenant_name": "Demo Tenant",
    "branch": 20,
    "branch_name": "Main Branch",
    "is_active": true,
    "date_joined": "2026-04-08T09:43:36.268519Z"
  }
}
```

Common errors:

- 401 invalid credentials

```json
{
  "detail": "Invalid credentials."
}
```

## 3.3 Login with PIN

- Method: POST
- URL: {{base_url}}/auth/login-pin
- Auth: No

Request body:

```json
{
  "username": "owner_demo",
  "pin": "1234"
}
```

Success response (200):

```json
{
  "tokens": {
    "refresh": "<jwt_refresh_token>",
    "access": "<jwt_access_token>"
  },
  "user": {
    "id": 30,
    "username": "owner_demo",
    "email": "owner@example.com",
    "first_name": "Demo",
    "last_name": "Owner",
    "role": "OWNER",
    "tenant": 10,
    "tenant_name": "Demo Tenant",
    "branch": 20,
    "branch_name": "Main Branch",
    "is_active": true,
    "date_joined": "2026-04-08T09:43:36.268519Z"
  }
}
```

Common errors:

- 401 invalid credentials
- 403 PIN not configured
- 423 PIN temporarily locked after repeated failed attempts

```json
{
  "detail": "PIN is not configured for this account."
}
```

## 3.4 Refresh Token

- Method: POST
- URL: {{base_url}}/auth/refresh
- Auth: No

Request body:

```json
{
  "refresh": "{{refresh_token}}"
}
```

Success response (200):

```json
{
  "access": "<new_jwt_access_token>",
  "refresh": "<new_jwt_refresh_token_when_rotation_enabled>"
}
```

Possible error (401):

```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

## 3.5 Get Branches

- Method: GET
- URL: {{base_url}}/branches
- Auth: Yes (OWNER or MANAGER)

Success response (200):

```json
[
  {
    "id": 20,
    "tenant": 10,
    "name": "Main Branch",
    "created_at": "2026-04-08T09:43:36.268053Z",
    "updated_at": "2026-04-08T09:43:36.268056Z"
  }
]
```

Common errors:

- 401 missing/invalid token
- 403 insufficient role

## 3.6 Create Branch

- Method: POST
- URL: {{base_url}}/branches
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "name": "Second Branch"
}
```

Success response (201):

```json
{
  "id": 21,
  "tenant": 10,
  "name": "Second Branch",
  "created_at": "2026-04-08T09:43:36.656588Z",
  "updated_at": "2026-04-08T09:43:36.656591Z"
}
```

## 3.7 Get Users

- Method: GET
- URL: {{base_url}}/users
- Auth: Yes (OWNER or MANAGER)

Success response (200):

```json
[
  {
    "id": 30,
    "username": "owner_demo",
    "email": "owner@example.com",
    "first_name": "Demo",
    "last_name": "Owner",
    "role": "OWNER",
    "tenant": 10,
    "tenant_name": "Demo Tenant",
    "branch": 20,
    "branch_name": "Main Branch",
    "is_active": true,
    "date_joined": "2026-04-08T09:43:36.268519Z"
  }
]
```

## 3.8 Create User

- Method: POST
- URL: {{base_url}}/users
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "username": "manager_demo",
  "email": "manager@example.com",
  "password": "StrongPass123",
  "first_name": "Demo",
  "last_name": "Manager",
  "role": "MANAGER",
  "branch": 21
}
```

Success response (201):

```json
{
  "username": "manager_demo",
  "email": "manager@example.com",
  "first_name": "Demo",
  "last_name": "Manager",
  "role": "MANAGER",
  "branch": 21
}
```

Common errors:

- 400 manager cannot create owner or manager accounts
- 400 branch does not belong to caller tenant

Example 400:

```json
{
  "role": [
    "Managers cannot create owner or manager accounts."
  ]
}
```

## 3.9 Set User PIN

- Method: POST
- URL: {{base_url}}/users/{{user_id}}/set-pin
- Auth: Yes (self or OWNER/MANAGER)

Request body:

```json
{
  "pin": "1234"
}
```

Success response (200):

```json
{
  "detail": "PIN updated successfully."
}
```

Common errors:

- 400 invalid pin format (must be 4-8 digits)
- 404 user not found in your tenant
- 403 permission denied for setting another user pin

## 3.10 Logout

- Method: POST
- URL: {{base_url}}/auth/logout
- Auth: Yes

Request body:

```json
{
  "refresh": "{{refresh_token}}"
}
```

Success response (200):

```json
{
  "detail": "Logged out successfully."
}
```

Common errors:

- 400 invalid refresh token
- 403 trying to logout another user's session

## 3.11 Get/Update Current User

- Method: GET
- URL: {{base_url}}/me
- Auth: Yes

Success response (200):

```json
{
  "id": 30,
  "username": "owner_demo",
  "email": "owner@example.com",
  "first_name": "Demo",
  "last_name": "Owner",
  "role": "OWNER",
  "tenant": 10,
  "tenant_name": "Demo Tenant",
  "branch": 20,
  "branch_name": "Main Branch",
  "is_active": true,
  "date_joined": "2026-04-08T09:43:36.268519Z"
}
```

- Method: PATCH
- URL: {{base_url}}/me
- Auth: Yes

Request body:

```json
{
  "first_name": "Updated",
  "last_name": "Owner"
}
```

Success response (200): same shape as GET `/me`.

## 3.12 Activity Logs

- Method: GET
- URL: {{base_url}}/activity-logs
- Auth: Yes (OWNER or MANAGER)

Optional query params:

- limit (example: `?limit=25`)

Success response (200):

```json
[
  {
    "id": 11,
    "action": "user_created",
    "entity_type": "user",
    "entity_id": "42",
    "metadata_json": {},
    "created_at": "2026-04-08T10:33:15.110000Z",
    "actor_user": 30,
    "actor_username": "owner_demo",
    "branch": 20,
    "branch_name": "Main Branch"
  }
]
```

## 3.13 Menu Categories (Phase 2 Start)

- Method: GET
- URL: {{base_url}}/menu/categories
- Auth: Yes (OWNER or MANAGER)

- Method: POST
- URL: {{base_url}}/menu/categories
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "branch": 20,
  "name": "Pizza",
  "sort_order": 1,
  "is_active": true
}
```

Success response (201):

```json
{
  "id": 1,
  "tenant": 10,
  "branch": 20,
  "name": "Pizza",
  "sort_order": 1,
  "is_active": true,
  "created_at": "2026-04-08T10:33:15.110000Z",
  "updated_at": "2026-04-08T10:33:15.110000Z"
}
```

Category detail endpoints:

- Method: GET
- URL: {{base_url}}/menu/categories/{{category_id}}
- Auth: Yes (OWNER or MANAGER)

- Method: PATCH
- URL: {{base_url}}/menu/categories/{{category_id}}
- Auth: Yes (OWNER or MANAGER)

PATCH request body example:

```json
{
  "name": "Fresh Pasta",
  "sort_order": 2,
  "is_active": true
}
```

- Method: DELETE
- URL: {{base_url}}/menu/categories/{{category_id}}
- Auth: Yes (OWNER or MANAGER)

DELETE success response: 204 No Content

## 3.14 Menu Items (Phase 2 Start)

- Method: GET
- URL: {{base_url}}/menu/items
- Auth: Yes (OWNER or MANAGER)

- Method: POST
- URL: {{base_url}}/menu/items
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "branch": 20,
  "category": 1,
  "name": "Margherita",
  "description": "Classic tomato and mozzarella",
  "base_price": "10.00",
  "vat_rate": "10.00",
  "is_active": true
}
```

Success response (201):

```json
{
  "id": 1,
  "tenant": 10,
  "branch": 20,
  "category": 1,
  "name": "Margherita",
  "description": "Classic tomato and mozzarella",
  "base_price": "10.00",
  "vat_rate": "10.00",
  "is_active": true,
  "created_at": "2026-04-08T10:33:15.110000Z",
  "updated_at": "2026-04-08T10:33:15.110000Z"
}
```

Menu item detail endpoints:

- Method: GET
- URL: {{base_url}}/menu/items/{{item_id}}
- Auth: Yes (OWNER or MANAGER)

- Method: PATCH
- URL: {{base_url}}/menu/items/{{item_id}}
- Auth: Yes (OWNER or MANAGER)

PATCH request body example:

```json
{
  "description": "Updated description",
  "base_price": "11.50",
  "is_active": true
}
```

- Method: DELETE
- URL: {{base_url}}/menu/items/{{item_id}}
- Auth: Yes (OWNER or MANAGER)

DELETE success response: 204 No Content

## 3.15 Floor Plans (Phase 2 Start)

- Method: GET
- URL: {{base_url}}/floor-plans
- Auth: Yes (OWNER or MANAGER)

- Method: POST
- URL: {{base_url}}/floor-plans
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "branch": 20,
  "name": "Main Hall",
  "layout_json": {
    "w": 100,
    "h": 60
  },
  "is_active": true
}
```

Success response (201):

```json
{
  "id": 1,
  "branch": 20,
  "name": "Main Hall",
  "layout_json": {
    "w": 100,
    "h": 60
  },
  "is_active": true,
  "created_at": "2026-04-08T10:33:15.110000Z",
  "updated_at": "2026-04-08T10:33:15.110000Z"
}
```

Floor plan detail endpoints:

- Method: GET
- URL: {{base_url}}/floor-plans/{{floor_plan_id}}
- Auth: Yes (OWNER or MANAGER)

- Method: PATCH
- URL: {{base_url}}/floor-plans/{{floor_plan_id}}
- Auth: Yes (OWNER or MANAGER)

PATCH request body example:

```json
{
  "name": "Main Hall Updated",
  "layout_json": {
    "w": 120,
    "h": 70
  }
}
```

- Method: DELETE
- URL: {{base_url}}/floor-plans/{{floor_plan_id}}
- Auth: Yes (OWNER or MANAGER)

DELETE success response: 204 No Content

## 3.16 Tables (Phase 2 Start)

- Method: GET
- URL: {{base_url}}/tables
- Auth: Yes (OWNER or MANAGER)

- Method: POST
- URL: {{base_url}}/tables
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "branch": 20,
  "floor_plan": 1,
  "code": "T1",
  "seats": 4,
  "state": "FREE",
  "x": 10,
  "y": 20
}
```

Success response (201):

```json
{
  "id": 1,
  "branch": 20,
  "floor_plan": 1,
  "code": "T1",
  "seats": 4,
  "state": "FREE",
  "x": 10,
  "y": 20,
  "created_at": "2026-04-08T10:33:15.110000Z",
  "updated_at": "2026-04-08T10:33:15.110000Z"
}
```

Table detail endpoints:

- Method: GET
- URL: {{base_url}}/tables/{{table_id}}
- Auth: Yes (OWNER or MANAGER)

- Method: PATCH
- URL: {{base_url}}/tables/{{table_id}}
- Auth: Yes (OWNER or MANAGER)

PATCH request body example:

```json
{
  "state": "RESERVED",
  "seats": 6
}
```

- Method: DELETE
- URL: {{base_url}}/tables/{{table_id}}
- Auth: Yes (OWNER or MANAGER)

DELETE success response: 204 No Content

## 3.17 Reservations (Phase 2 Start)

- Method: GET
- URL: {{base_url}}/reservations
- Auth: Yes (OWNER or MANAGER)

- Method: POST
- URL: {{base_url}}/reservations
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "branch": 20,
  "table": 1,
  "customer_name": "Mario Rossi",
  "customer_phone": "+390000000",
  "party_size": 2,
  "reserved_for": "2026-04-08T20:30:00Z",
  "status": "CONFIRMED",
  "notes": "Window seat"
}
```

Success response (201):

```json
{
  "id": 1,
  "branch": 20,
  "table": 1,
  "customer_name": "Mario Rossi",
  "customer_phone": "+390000000",
  "party_size": 2,
  "reserved_for": "2026-04-08T20:30:00Z",
  "status": "CONFIRMED",
  "notes": "Window seat",
  "created_at": "2026-04-08T10:33:15.110000Z",
  "updated_at": "2026-04-08T10:33:15.110000Z"
}
```

Reservation detail endpoints:

- Method: GET
- URL: {{base_url}}/reservations/{{reservation_id}}
- Auth: Yes (OWNER or MANAGER)

- Method: PATCH
- URL: {{base_url}}/reservations/{{reservation_id}}
- Auth: Yes (OWNER or MANAGER)

PATCH request body example:

```json
{
  "status": "ARRIVED",
  "notes": "Guests have arrived"
}
```

- Method: DELETE
- URL: {{base_url}}/reservations/{{reservation_id}}
- Auth: Yes (OWNER or MANAGER)

DELETE success response: 204 No Content

Common errors:

- 400 when trying to reserve the same table and time slot twice (active reservation overlap)

Example 400:

```json
{
  "reserved_for": [
    "This table is already reserved for the selected time slot."
  ]
}
```

## 3.18 Reservation Status Actions

- Method: POST
- URL: {{base_url}}/reservations/{{reservation_id}}/arrived
- Auth: Yes (OWNER or MANAGER)

Success response (200):

```json
{
  "id": 1,
  "branch": 20,
  "table": 1,
  "customer_name": "Mario Rossi",
  "customer_phone": "+390000000",
  "party_size": 2,
  "reserved_for": "2026-04-08T20:30:00Z",
  "status": "ARRIVED",
  "notes": "Window seat",
  "created_at": "2026-04-08T10:33:15.110000Z",
  "updated_at": "2026-04-08T10:36:00.000000Z"
}
```

- Method: POST
- URL: {{base_url}}/reservations/{{reservation_id}}/cancel
- Auth: Yes (OWNER or MANAGER)

Success response (200): same shape as reservation response with `status: "CANCELED"`.

## 3.19 Filtering and Pagination (Phase 2 Lists)

These list endpoints are paginated:

- GET {{base_url}}/menu/allergens
- GET {{base_url}}/menu/categories
- GET {{base_url}}/menu/items
- GET {{base_url}}/menu/schedules
- GET {{base_url}}/floor-plans
- GET {{base_url}}/tables
- GET {{base_url}}/reservations
- GET {{base_url}}/waitlist

Pagination query params:

- page (default 1)
- page_size (max 100)

Paginated response shape:

```json
{
  "count": 12,
  "next": "http://127.0.0.1:8000/api/v1/menu/items?page=2&page_size=5",
  "previous": null,
  "results": [
    {
      "id": 1
    }
  ]
}
```

Supported filters:

- Menu allergens: `q`
- Menu categories: `branch`, `is_active`, `q`
- Menu items: `branch`, `category`, `is_active`, `min_price`, `max_price`, `q`
- Menu schedules: `branch`, `menu_item`, `day_of_week`, `is_active`
- Floor plans: `branch`, `is_active`, `q`
- Tables: `branch`, `floor_plan`, `state`, `q`
- Reservations: `branch`, `table`, `status`, `reserved_from`, `reserved_to`, `q`
- Waitlist: `branch`, `table`, `status`, `q`

## 3.20 Allergens and Item Mapping

- Method: POST
- URL: {{base_url}}/menu/allergens
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "code": "GLUTEN",
  "name_it": "Glutine",
  "name_en": "Gluten",
  "name_de": "Gluten",
  "name_fr": "Gluten"
}
```

Success response (201):

```json
{
  "id": 1,
  "code": "GLUTEN",
  "name_it": "Glutine",
  "name_en": "Gluten",
  "name_de": "Gluten",
  "name_fr": "Gluten",
  "created_at": "2026-04-08T12:01:10.000000Z",
  "updated_at": "2026-04-08T12:01:10.000000Z"
}
```

Attach allergens to item on create/update:

- Method: POST
- URL: {{base_url}}/menu/items

```json
{
  "branch": 20,
  "category": 12,
  "name": "Spaghetti",
  "description": "Classic",
  "base_price": "12.00",
  "vat_rate": "10.00",
  "allergens": [1]
}
```

## 3.21 Menu Schedule Windows

- Method: POST
- URL: {{base_url}}/menu/schedules
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "branch": 20,
  "menu_item": 33,
  "day_of_week": 5,
  "start_time": "18:00:00",
  "end_time": "22:00:00",
  "is_active": true
}
```

Success response (201):

```json
{
  "id": 9,
  "tenant": 10,
  "branch": 20,
  "menu_item": 33,
  "day_of_week": 5,
  "start_time": "18:00:00",
  "end_time": "22:00:00",
  "is_active": true,
  "created_at": "2026-04-08T12:02:50.000000Z",
  "updated_at": "2026-04-08T12:02:50.000000Z"
}
```

Common error:

- 400 when end_time is not after start_time

## 3.22 Waitlist Basics

- Method: POST
- URL: {{base_url}}/waitlist
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "branch": 20,
  "table": 5,
  "customer_name": "Walk In Guest",
  "customer_phone": "+39000111222",
  "party_size": 3,
  "quoted_wait_minutes": 20,
  "status": "WAITING",
  "notes": "Prefers patio"
}
```

Success response (201):

```json
{
  "id": 4,
  "branch": 20,
  "table": 5,
  "customer_name": "Walk In Guest",
  "customer_phone": "+39000111222",
  "party_size": 3,
  "quoted_wait_minutes": 20,
  "status": "WAITING",
  "notes": "Prefers patio",
  "seated_at": null,
  "created_at": "2026-04-08T12:05:20.000000Z",
  "updated_at": "2026-04-08T12:05:20.000000Z"
}
```

Status actions:

- POST {{base_url}}/waitlist/{{waitlist_id}}/call
- POST {{base_url}}/waitlist/{{waitlist_id}}/seat
- POST {{base_url}}/waitlist/{{waitlist_id}}/cancel

Common errors:

- 400 when trying to seat without assigning a table
- 400 when trying to call/seat a canceled waitlist entry

## 3.23 Orders (Phase 3)

### Create Order

- Method: POST
- URL: {{base_url}}/orders
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "branch": 20,
  "channel": "DINE_IN",
  "table": 1,
  "notes": "Extra napkins",
  "items": [
    {
      "menu_item": 1,
      "quantity": 2,
      "notes": "No onions"
    }
  ]
}
```

Success response (201):

```json
{
  "id": 1,
  "tenant": 10,
  "branch": 20,
  "table": 1,
  "waiter_user": null,
  "status": "OPEN",
  "channel": "DINE_IN",
  "notes": "Extra napkins",
  "items": [
    {
      "id": 1,
      "menu_item": 1,
      "item_name": "Margherita",
      "unit_price": "10.00",
      "vat_rate": "10.00",
      "quantity": 2,
      "status": "PENDING",
      "notes": "No onions",
      "created_at": "2026-04-09T10:00:00.000000Z",
      "updated_at": "2026-04-09T10:00:00.000000Z"
    }
  ],
  "created_at": "2026-04-09T10:00:00.000000Z",
  "updated_at": "2026-04-09T10:00:00.000000Z"
}
```

### List Orders

- Method: GET
- URL: {{base_url}}/orders
- Auth: Yes (OWNER or MANAGER)

Supported filters:

- `branch` — filter by branch ID
- `status` — OPEN | SENT_TO_KITCHEN | PARTIALLY_SERVED | COMPLETED | CANCELED
- `channel` — DINE_IN | TAKEAWAY

Paginated response shape (same as other list endpoints).

### Get Order Detail

- Method: GET
- URL: {{base_url}}/orders/{{order_id}}
- Auth: Yes (OWNER or MANAGER)

### Update Order

- Method: PATCH
- URL: {{base_url}}/orders/{{order_id}}
- Auth: Yes (OWNER or MANAGER)

Request body example:

```json
{
  "status": "CANCELED",
  "notes": "Customer left"
}
```

### Send to Kitchen

- Method: POST
- URL: {{base_url}}/orders/{{order_id}}/send-to-kitchen
- Auth: Yes (OWNER or MANAGER)

No request body. Transitions order status to `SENT_TO_KITCHEN` and all `PENDING` items to `SENT`.

Success response (200): full order object with updated status.

Common errors:

- 400 when order is already CANCELED or COMPLETED
- 404 when order not found in caller's tenant

## 3.24 Order Hold, Fire, and Course Fire (Phase 3 Complete)

### Hold Order

- Method: POST
- URL: {{base_url}}/orders/{{order_id}}/hold
- Auth: Yes (WAITER or above)

No request body. Transitions OPEN → HELD (order taken, not yet sent to kitchen).

### Fire Order (All Courses)

- Method: POST
- URL: {{base_url}}/orders/{{order_id}}/fire
- Auth: Yes (WAITER or above)

No request body. Fires all PENDING items to kitchen — creates one `KitchenTicket` per distinct course and queues a `PrintJob` per ticket.

### Fire Specific Course

- Method: POST
- URL: {{base_url}}/orders/{{order_id}}/course/fire
- Auth: Yes (WAITER or above)

Request body:

```json
{ "course": "STARTER" }
```

Valid courses: `STARTER`, `MAIN`, `DESSERT`, `DRINK`, `OTHER`.

Fires only PENDING items for the given course. Creates one `KitchenTicket` for that course.

Common errors:
- 400 when no pending items exist for the specified course
- 400 when course value is invalid

### Call Waiter

- Method: POST
- URL: {{base_url}}/orders/{{order_id}}/call-waiter
- Auth: Yes (WAITER or above)

No request body. Logs the event and returns 200. No order state change. Will trigger a realtime notification when the dispatcher is integrated.

### Request Bill

- Method: POST
- URL: {{base_url}}/orders/{{order_id}}/request-bill
- Auth: Yes (WAITER or above)

No request body. Logs the event and sets the linked table's state to `WAITING_BILL` if a table is assigned.

## 3.25 Order Cancel and Complete Actions (Phase 3 Slice 3)

### Cancel Order

- Method: POST
- URL: {{base_url}}/orders/{{order_id}}/cancel
- Auth: Yes (OWNER or MANAGER only)

No request body. Transitions order to `CANCELED`.

Success response (200): full order object with `status: "CANCELED"`.

Common errors:
- 400 when order is already CANCELED or COMPLETED
- 403 when caller is WAITER or CASHIER

### Complete Order

- Method: POST
- URL: {{base_url}}/orders/{{order_id}}/complete
- Auth: Yes (OWNER or MANAGER only)

No request body. Transitions order to `COMPLETED`.

Success response (200): full order object with `status: "COMPLETED"`.

Common errors:
- 400 when order is already COMPLETED or CANCELED
- 403 when caller is WAITER or CASHIER

## 3.26 Order Item Sub-endpoints (Phase 3 Slice 2)

### Add Item to Existing Order

- Method: POST
- URL: {{base_url}}/orders/{{order_id}}/items
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "menu_item": 1,
  "quantity": 2,
  "notes": "No onions"
}
```

Success response (201): OrderItem object with snapshot fields populated from menu item.

Common errors:
- 400 when order is CANCELED
- 404 when order not found in caller's tenant

### Update Order Item

- Method: PATCH
- URL: {{base_url}}/orders/{{order_id}}/items/{{item_id}}
- Auth: Yes (OWNER or MANAGER)

Request body (all fields optional):

```json
{
  "quantity": 3,
  "notes": "Extra sauce",
  "status": "SERVED"
}
```

Success response (200): full OrderItem object.

### Delete Order Item

- Method: DELETE
- URL: {{base_url}}/orders/{{order_id}}/items/{{item_id}}
- Auth: Yes (OWNER or MANAGER)

Success response: 204 No Content.

## 3.26 Kitchen Tickets (Phase 3 Slice 2)

A `KitchenTicket` is auto-created when `send-to-kitchen` is called on an order.

### List Kitchen Tickets

- Method: GET
- URL: {{base_url}}/kitchen/tickets
- Auth: Yes (OWNER or MANAGER)

Supported filters:
- `branch` — filter by branch ID
- `status` — PENDING | PREPARED

Paginated response shape (same as other list endpoints).

Success response results item:

```json
{
  "id": 1,
  "tenant": 10,
  "branch": 20,
  "order": 1,
  "status": "PENDING",
  "created_at": "2026-04-09T10:05:00.000000Z",
  "updated_at": "2026-04-09T10:05:00.000000Z"
}
```

### Mark Ticket Prepared

- Method: POST
- URL: {{base_url}}/kitchen/tickets/{{ticket_id}}/prepared
- Auth: Yes (OWNER or MANAGER)

No request body. Transitions ticket status from `PENDING` to `PREPARED`.

Success response (200): full KitchenTicket object with `status: "PREPARED"`.

Common errors:
- 400 when ticket is already PREPARED
- 404 when ticket not found in caller's tenant

## 4. Postman Tests Script Snippets

Add this to login and register requests Tests tab to store tokens:

```javascript
const json = pm.response.json();
if (json.tokens) {
  pm.environment.set("access_token", json.tokens.access);
  pm.environment.set("refresh_token", json.tokens.refresh);
}
if (json.user && json.user.id) {
  pm.environment.set("user_id", json.user.id);
}
if (json.branch && json.branch.id) {
  pm.environment.set("branch_id", json.branch.id);
}
if (json.id && pm.request.url.toString().includes('/menu/categories')) {
  pm.environment.set("category_id", json.id);
}
if (json.id && pm.request.url.toString().includes('/menu/items')) {
  pm.environment.set("item_id", json.id);
}
if (json.id && pm.request.url.toString().includes('/menu/allergens')) {
  pm.environment.set("allergen_id", json.id);
}
if (json.id && pm.request.url.toString().includes('/menu/schedules')) {
  pm.environment.set("schedule_id", json.id);
}
if (json.id && pm.request.url.toString().includes('/floor-plans')) {
  pm.environment.set("floor_plan_id", json.id);
}
if (json.id && pm.request.url.toString().includes('/tables')) {
  pm.environment.set("table_id", json.id);
}
if (json.id && pm.request.url.toString().includes('/reservations')) {
  pm.environment.set("reservation_id", json.id);
}
if (json.id && pm.request.url.toString().includes('/waitlist')) {
  pm.environment.set("waitlist_id", json.id);
}
```

Add this to refresh request Tests tab:

```javascript
const json = pm.response.json();
if (json.access) pm.environment.set("access_token", json.access);
if (json.refresh) pm.environment.set("refresh_token", json.refresh);
```

## 3.27 Buffet Plans (Phase 4)

- Method: GET / POST
- URL: {{base_url}}/buffet/plans
- Auth: Yes (OWNER or MANAGER)

POST request body:

```json
{
  "branch": 20,
  "name": "Sunday Buffet",
  "base_price": "25.00",
  "kids_price": "12.00",
  "time_limit_minutes": 90,
  "waste_penalty_amount": "5.00",
  "round_limit_per_person": 3,
  "round_delay_seconds": 300,
  "active_from": "2026-05-01",
  "active_to": "2026-08-31",
  "is_active": true
}
```

- Method: GET / PATCH
- URL: {{base_url}}/buffet/plans/{{plan_id}}

Supported list filters: `branch`, `is_active`

## 3.28 Buffet Sessions (Phase 4)

### Start Session

- Method: POST
- URL: {{base_url}}/buffet/sessions/start
- Auth: Yes (WAITER or above)

```json
{
  "branch": 20,
  "buffet_plan": 1,
  "order": 5,
  "adults_count": 4,
  "kids_count": 1
}
```

`order` is optional. `ends_at` is auto-computed from `buffet_plan.time_limit_minutes`.

### Get Session

- Method: GET
- URL: {{base_url}}/buffet/sessions/{{session_id}}

Response includes nested `rounds` array and `is_expired` flag.

### End Session

- Method: POST
- URL: {{base_url}}/buffet/sessions/{{session_id}}/end
- Auth: Yes (OWNER or MANAGER)

Auto-closes any open round. Transitions status to `ENDED`.

### New Round

- Method: POST
- URL: {{base_url}}/buffet/sessions/{{session_id}}/new-round
- Auth: Yes (WAITER or above)

No body. Creates next round. Errors if:
- A round is already open
- Round limit per person reached
- Round delay seconds not elapsed since last closed round

### Close Round

- Method: POST
- URL: {{base_url}}/buffet/sessions/{{session_id}}/close-round
- Auth: Yes (WAITER or above)

No body. Closes the current open round.

## 3.29 Waste Logs (Phase 4)

- Method: POST
- URL: {{base_url}}/waste-logs
- Auth: Yes (OWNER or MANAGER)

```json
{
  "branch": 20,
  "order_item": 7,
  "quantity_wasted": 2,
  "reason": "Left on plate"
}
```

`penalty_applied` is auto-calculated from the linked buffet session plan (`waste_penalty_amount × quantity_wasted`). Zero if no buffet session.

## 3.30 Buffet Analytics (Phase 4)

- Method: GET
- URL: {{base_url}}/buffet/analytics
- Auth: Yes (OWNER or MANAGER)

Supported filters: `branch`, `date_from`, `date_to`

Success response:

```json
{
  "total_sessions": 12,
  "total_adults": 48,
  "total_kids": 10,
  "total_waste_logs": 5,
  "total_penalty": "25.00"
}
```

## 3.31 Billing (Phase 5 Step A-D - Implemented)

### Create Bill from Order

- Method: POST
- URL: {{base_url}}/bills/create-from-order
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "order": 5
}
```

Behavior:

- Creates one `Bill` per order (duplicate creation is rejected).
- Builds `BillLine` rows from non-canceled order items.
- Captures totals:
  - `subtotal`: sum of line totals
  - `vat_total`: sum of VAT per line (`line_total * vat_rate / 100`)
  - `grand_total`: `subtotal + vat_total + coperto_total + service_charge_total + waste_total - discount_total`

Success response (201):

```json
{
  "id": 1,
  "tenant": 10,
  "branch": 20,
  "order": 5,
  "bill_no": 1,
  "status": "DRAFT",
  "subtotal": "34.00",
  "vat_total": "4.60",
  "coperto_total": "0.00",
  "service_charge_total": "0.00",
  "waste_total": "0.00",
  "discount_total": "0.00",
  "grand_total": "38.60",
  "lines": [
    {
      "id": 1,
      "source_type": "ORDER_ITEM",
      "source_id": "11",
      "description": "Carbonara",
      "quantity": "2.00",
      "unit_price": "12.00",
      "vat_rate": "10.00",
      "line_total": "24.00",
      "created_at": "2026-04-10T10:00:00.000000Z"
    }
  ],
  "created_at": "2026-04-10T10:00:00.000000Z",
  "updated_at": "2026-04-10T10:00:00.000000Z"
}
```

Common errors:

- 400 when the order is outside your tenant
- 400 when a bill already exists for the order
- 403 when caller role is not OWNER/MANAGER

### Get Bill Detail

- Method: GET
- URL: {{base_url}}/bills/{{bill_id}}
- Auth: Yes (OWNER or MANAGER)

Success response (200): same shape as create response.

Tenant isolation:

- Returns 404 when bill does not belong to caller tenant.

### Apply Coperto

- Method: POST
- URL: {{base_url}}/bills/{{bill_id}}/apply-coperto
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "amount": "2.00",
  "covers": 4
}
```

Behavior:

- Adds a `COPERTO` line (`amount * covers`).
- Recalculates bill totals.
- Allowed only when bill is `DRAFT`.

### Apply Discount

- Method: POST
- URL: {{base_url}}/bills/{{bill_id}}/apply-discount
- Auth: Yes (OWNER or MANAGER)

Request body (PERCENT):

```json
{
  "type": "PERCENT",
  "value": "10.00"
}
```

Request body (FIXED):

```json
{
  "type": "FIXED",
  "value": "5.00"
}
```

Behavior:

- Adds a `DISCOUNT` line.
- For `PERCENT`, applies discount to current payable amount.
- Caps discount to avoid negative totals.
- Allowed only when bill is `DRAFT`.

### Finalize Bill

- Method: POST
- URL: {{base_url}}/bills/{{bill_id}}/finalize
- Auth: Yes (OWNER or MANAGER)

No request body.

Behavior:

- Transitions bill `DRAFT -> FINALIZED`.
- Once finalized, bill modifications are rejected.

### Record Payment

- Method: POST
- URL: {{base_url}}/bills/{{bill_id}}/pay
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "method": "CASH",
  "amount": "20.00",
  "reference": "POS-1"
}
```

Behavior:

- Records a payment row.
- Requires bill to be `FINALIZED`.
- When cumulative `amount_paid >= grand_total`, bill transitions to `PAID`.

Common action errors:

- 400 when modifying a non-draft bill (`apply-coperto`, `apply-discount`, `finalize`)
- 400 when paying a draft bill
- 400 when paying an already paid bill

## 3.32 Fiscal Integration (Phase 6 - Implemented)

### Send Bill to Fiscal

- Method: POST
- URL: {{base_url}}/bills/{{bill_id}}/send-to-fiscal
- Auth: Yes (OWNER or MANAGER)

Behavior:

- Requires bill status `FINALIZED` or `PAID`.
- Creates a fiscal transaction (`ISSUE_RECEIPT`) and a receipt record.
- Rejects duplicate issuance if receipt already exists.

Success response (200):

```json
{
  "receipt": {
    "id": 1,
    "bill": 1,
    "fiscal_receipt_no": "FR-20-000001",
    "z_report_no": null,
    "issued_at": "2026-04-10T13:30:00.000000Z",
    "reprint_count": 0,
    "refunded_total": "0.00",
    "refunds": [],
    "created_at": "2026-04-10T13:30:00.000000Z"
  },
  "fiscal_transaction": {
    "id": 10,
    "transaction_type": "ISSUE_RECEIPT",
    "status": "COMPLETED",
    "external_id": "fiscal-abc123",
    "request_json": {
      "bill_id": 1,
      "bill_no": 1,
      "grand_total": "38.60"
    },
    "response_json": {
      "receipt_id": 1,
      "fiscal_receipt_no": "FR-20-000001"
    }
  }
}
```

### Get Receipt Detail

- Method: GET
- URL: {{base_url}}/receipts/{{receipt_id}}
- Auth: Yes (OWNER or MANAGER)

Tenant isolation enforced (404 outside tenant scope).

### Reprint Receipt

- Method: POST
- URL: {{base_url}}/receipts/{{receipt_id}}/reprint
- Auth: Yes (OWNER or MANAGER)

Behavior:

- Increments `reprint_count`.
- Writes fiscal transaction (`REPRINT_RECEIPT`).

### Refund Receipt

- Method: POST
- URL: {{base_url}}/receipts/{{receipt_id}}/refund
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "amount": "5.00",
  "reason": "Customer complaint"
}
```

Behavior:

- Creates refund row and fiscal transaction (`REFUND_RECEIPT`).
- Rejects refund amount above remaining refundable total.

### Z Report Sync

- Method: POST
- URL: {{base_url}}/fiscal/z-report/sync
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "branch": 20,
  "business_date": "2026-04-10",
  "z_report_no": "Z-2026-04-10-001"
}
```

Behavior:

- Creates fiscal transaction (`Z_REPORT_SYNC`).
- If `z_report_no` provided, updates receipts for the branch with that number.

### Z Report Status

- Method: GET
- URL: {{base_url}}/fiscal/z-report/status?branch={{branch_id}}
- Auth: Yes (OWNER or MANAGER)

Success response (200):

```json
{
  "last_sync": {
    "id": 15,
    "transaction_type": "Z_REPORT_SYNC",
    "status": "COMPLETED"
  },
  "total_syncs": 1
}
```

### Bridge Fiscal Ack

- Method: POST
- URL: {{base_url}}/integrations/bridge/fiscal-ack
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "external_id": "fiscal-abc123",
  "status": "ACKED",
  "response_json": {
    "bridge": "ok"
  }
}
```

Behavior:

- Updates existing fiscal transaction status and optional response payload.

## 3.33 Inventory (Phase 7 - Implemented)

### Ingredient List/Create

- Method: GET, POST
- URL: {{base_url}}/inventory/ingredients
- Auth: Yes (OWNER or MANAGER)

Create request body:

```json
{
  "branch": 20,
  "name": "Flour",
  "sku": "FLR-001",
  "unit": "KG",
  "current_stock": "10.000",
  "min_stock_level": "3.000",
  "is_active": true
}
```

Create success response (201):

```json
{
  "id": 1,
  "tenant": 10,
  "branch": 20,
  "name": "Flour",
  "sku": "FLR-001",
  "unit": "KG",
  "current_stock": "10.000",
  "min_stock_level": "3.000",
  "is_active": true,
  "created_at": "2026-04-10T17:00:00.000000Z",
  "updated_at": "2026-04-10T17:00:00.000000Z"
}
```

Supported list filters:

- `branch`
- `is_active`
- `q` (ingredient name contains)

### Ingredient Detail/Update/Delete

- Method: GET, PATCH, DELETE
- URL: {{base_url}}/inventory/ingredients/{{ingredient_id}}
- Auth: Yes (OWNER or MANAGER)

Tenant isolation:

- Returns 404 when ingredient does not belong to caller tenant.

### Stock Movement Ledger List/Create

- Method: GET, POST
- URL: {{base_url}}/inventory/movements
- Auth: Yes (OWNER or MANAGER)

Create request body:

```json
{
  "ingredient": 1,
  "movement_type": "STOCK_OUT",
  "quantity": "2.000",
  "reason": "Kitchen usage",
  "reference": "ORD-1042"
}
```

Create success response (201):

```json
{
  "id": 5,
  "tenant": 10,
  "branch": 20,
  "ingredient": 1,
  "movement_type": "STOCK_OUT",
  "quantity": "2.000",
  "stock_before": "10.000",
  "stock_after": "8.000",
  "reason": "Kitchen usage",
  "reference": "ORD-1042",
  "created_by": 30,
  "created_at": "2026-04-10T17:10:00.000000Z"
}
```

Rules:

- `quantity` must be greater than zero.
- Movement write is atomic.
- Resulting stock cannot go below zero (400).

Supported list filters:

- `branch`
- `ingredient`
- `movement_type`

### Low-Stock Report

- Method: GET
- URL: {{base_url}}/inventory/reports/low-stock
- Auth: Yes (OWNER or MANAGER)

Optional filters:

- `branch`

Success response (200, paginated):

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "tenant": 10,
      "branch": 20,
      "name": "Flour",
      "sku": "FLR-001",
      "unit": "KG",
      "current_stock": "2.000",
      "min_stock_level": "3.000",
      "shortage": "1.000",
      "updated_at": "2026-04-10T17:12:00.000000Z"
    }
  ]
}
```

Common inventory errors:

- 400 when branch or ingredient belongs to another tenant.
- 400 when stock movement would make stock negative.
- 403 when caller role is not OWNER/MANAGER.

### Recipe Components List/Create

- Method: GET, POST
- URL: {{base_url}}/inventory/recipes
- Auth: Yes (OWNER or MANAGER)

Create request body:

```json
{
  "branch": 20,
  "menu_item": 11,
  "ingredient": 1,
  "quantity": "0.250",
  "is_active": true
}
```

Create success response (201):

```json
{
  "id": 1,
  "tenant": 10,
  "branch": 20,
  "menu_item": 11,
  "ingredient": 1,
  "quantity": "0.250",
  "is_active": true,
  "created_at": "2026-04-11T10:00:00.000000Z",
  "updated_at": "2026-04-11T10:00:00.000000Z"
}
```

### Recipe Component Detail/Update/Delete

- Method: GET, PATCH, DELETE
- URL: {{base_url}}/inventory/recipes/{{recipe_id}}
- Auth: Yes (OWNER or MANAGER)

Rules:

- Branch, menu item, and ingredient must belong to the caller tenant.
- Ingredient branch must match the selected branch.

### Receiving Flow (Stock In)

- Method: POST
- URL: {{base_url}}/inventory/receivings
- Auth: Yes (OWNER or MANAGER)

Request body:

```json
{
  "ingredient": 1,
  "quantity": "5.000",
  "supplier_name": "Main Supplier",
  "document_no": "RCV-1001",
  "notes": "Weekly delivery"
}
```

Behavior:

- Creates `RECEIVING` stock movement.
- Updates ingredient stock atomically.

### Inventory Usage Report

- Method: GET
- URL: {{base_url}}/inventory/reports/usage
- Auth: Yes (OWNER or MANAGER)

Optional filters:

- `branch`
- `ingredient`
- `date_from`
- `date_to`

Success response (200):

```json
{
  "count": 1,
  "total_consumed": "6.000",
  "total_received": "5.000",
  "results": [
    {
      "ingredient": 1,
      "ingredient_name": "Flour",
      "unit": "KG",
      "movement_count": 3,
      "consumed_quantity": "6.000",
      "received_quantity": "5.000",
      "net_quantity": "-1.000"
    }
  ]
}
```

### Auto Deduction On Order Fire

When recipe components are configured, these endpoints automatically deduct inventory:

- POST {{base_url}}/orders/{{order_id}}/fire
- POST {{base_url}}/orders/{{order_id}}/send-to-kitchen

Rules:

- Deduction is based on `recipe_component.quantity * order_item.quantity` aggregated per ingredient.
- Stock deduction and item status update run in one transaction.
- If stock is insufficient, request returns 400 and no item status/ticket side effects are committed.

## 3.34 Takeaway and Loyalty (Phase 8 - Implemented)

### Create Takeaway Order

- Method: POST
- URL: {{base_url}}/takeaway/orders
- Auth: Yes (WAITER/CASHIER/MANAGER/OWNER)

Request body:

```json
{
  "branch": 20,
  "pickup_name": "Mario Rossi",
  "pickup_phone": "+39000111",
  "customer_name": "Mario Rossi",
  "customer_phone": "+39000111",
  "packaging_fee": "1.50",
  "extra_fee": "0.50",
  "items": [
    {
      "menu_item": 11,
      "quantity": 2
    }
  ]
}
```

Behavior:

- Creates underlying `Order` with channel `TAKEAWAY`.
- Adds packaging/extra fees as non-kitchen order lines.
- Creates/updates customer record by phone when provided.

### Get Takeaway Detail

- Method: GET
- URL: {{base_url}}/takeaway/orders/{{takeaway_id}}
- Auth: Yes (WAITER/CASHIER/MANAGER/OWNER)

Tenant isolation:

- Returns 404 outside tenant scope.

### Mark Takeaway Ready

- Method: POST
- URL: {{base_url}}/takeaway/orders/{{takeaway_id}}/ready
- Auth: Yes (WAITER/CASHIER/MANAGER/OWNER)

Rules:

- Allowed only from `PREPARING` status.
- Rejects when order still has `PENDING` items.

### Loyalty Customer Lookup By Phone

- Method: GET
- URL: {{base_url}}/loyalty/customers/{{customer_phone}}
- Auth: Yes (WAITER/CASHIER/MANAGER/OWNER)

Success response includes customer profile, aggregate stats, and recent visits.

### Record Loyalty Visit

- Method: POST
- URL: {{base_url}}/loyalty/visits
- Auth: Yes (WAITER/CASHIER/MANAGER/OWNER)

Request body:

```json
{
  "branch": 20,
  "phone": "+39000111",
  "full_name": "Mario Rossi",
  "spend_total": "18.00"
}
```

Behavior:

- Creates customer automatically when `customer_id` is not supplied.
- Records visit event for loyalty statistics.

### Loyalty Eligibility

- Method: GET
- URL: {{base_url}}/loyalty/eligibility?phone={{customer_phone}}
- Auth: Yes (WAITER/CASHIER/MANAGER/OWNER)

Behavior:

- Evaluates active loyalty rules (`VISIT_COUNT`, `SPEND_TOTAL`).
- Returns `eligible`, reason, customer stats, and matched reward rule.

Common Phase 8 errors:

- 400 when takeaway is marked ready with pending items.
- 400 when branch/order/customer is outside tenant scope.
- 403 when caller role is `KITCHEN`.

## 3.35 Reporting (Phase 9 - Implemented)

All reporting endpoints require OWNER or MANAGER role.

### Refresh Daily Snapshots

- Method: POST
- URL: {{base_url}}/reports/snapshots/refresh
- Auth: Yes (OWNER/MANAGER)

Request body (single branch):

```json
{
  "branch": 20,
  "business_date": "2026-04-11"
}
```

Request body (all branches in tenant):

```json
{
  "business_date": "2026-04-11"
}
```

Behavior:

- Recomputes KPI snapshots for the target date.
- Invalidates tenant report cache keys after refresh.

### List Daily Snapshots

- Method: GET
- URL: {{base_url}}/reports/snapshots?branch={{branch_id}}&date_from=2026-04-01&date_to=2026-04-30
- Auth: Yes (OWNER/MANAGER)

Response is paginated with KPI fields per branch/day.

### Sales By Category

- Method: GET
- URL: {{base_url}}/reports/sales/by-category?branch={{branch_id}}&date_from=2026-04-01&date_to=2026-04-30
- Auth: Yes (OWNER/MANAGER)

### Sales By Table

- Method: GET
- URL: {{base_url}}/reports/sales/by-table?branch={{branch_id}}
- Auth: Yes (OWNER/MANAGER)

### Sales By Waiter

- Method: GET
- URL: {{base_url}}/reports/sales/by-waiter?branch={{branch_id}}
- Auth: Yes (OWNER/MANAGER)

### Sales By VAT

- Method: GET
- URL: {{base_url}}/reports/sales/by-vat?branch={{branch_id}}
- Auth: Yes (OWNER/MANAGER)

### Buffet Branch Comparison

- Method: GET
- URL: {{base_url}}/reports/buffet/branch-comparison?date_from=2026-04-01&date_to=2026-04-30
- Auth: Yes (OWNER/MANAGER)

### Invalidate Report Cache

- Method: POST
- URL: {{base_url}}/reports/cache/invalidate
- Auth: Yes (OWNER/MANAGER)

Behavior:

- Clears all tenant-scoped cached report payloads.

Common Phase 9 errors:

- 403 when caller is not OWNER/MANAGER.
- 400 when `date_to < date_from`.

---

## 4.10 Phase 10 — Offline Sync Protocol

Postman variables to add: `device_uuid`, `device_id`.

### Register Device

- Method: POST
- URL: {{base_url}}/devices/register
- Auth: Yes (any authenticated role)

Request body:

```json
{
  "device_uuid": "pos-branch1-001",
  "name": "POS Terminal 1",
  "device_type": "POS",
  "app_version": "1.2.0",
  "branch_id": {{branch_id}}
}
```

Success response (201 on first registration, 200 on update):

```json
{
  "id": 1,
  "device_uuid": "pos-branch1-001",
  "name": "POS Terminal 1",
  "device_type": "POS",
  "app_version": "1.2.0",
  "is_active": true,
  "registered_at": "2026-04-11T10:00:00Z",
  "last_seen_at": null
}
```

### Device Heartbeat

- Method: POST
- URL: {{base_url}}/devices/heartbeat
- Auth: Yes (any authenticated role)

Request body:

```json
{
  "device_uuid": "pos-branch1-001",
  "app_version": "1.2.1"
}
```

Success response (200):

```json
{
  "device_uuid": "pos-branch1-001",
  "last_seen_at": "2026-04-11T10:05:00Z",
  "status": "ok"
}
```

### Sync Push

- Method: POST
- URL: {{base_url}}/sync/push
- Auth: Yes (any authenticated role)

Request body:

```json
{
  "device_uuid": "pos-branch1-001",
  "items": [
    {
      "idempotency_key": "device-001-order-99-v1",
      "entity_type": "order",
      "entity_id": "99",
      "device_updated_at": "2026-04-11T09:55:00Z",
      "payload": {
        "note": "extra napkins",
        "status": "OPEN"
      }
    }
  ]
}
```

Success response (200):

```json
{
  "device_uuid": "pos-branch1-001",
  "results": [
    {
      "idempotency_key": "device-001-order-99-v1",
      "entity_type": "order",
      "entity_id": "99",
      "status": "ACCEPTED",
      "conflict_detail": ""
    }
  ]
}
```

Conflict response (status field = "CONFLICT"):

```json
{
  "device_uuid": "pos-branch1-001",
  "results": [
    {
      "idempotency_key": "device-001-order-99-v1",
      "entity_type": "order",
      "entity_id": "99",
      "status": "CONFLICT",
      "conflict_detail": "Server version updated at 2026-04-11T10:00:00Z is newer than device version at 2026-04-11T09:55:00Z."
    }
  ]
}
```

Conflict policy: server timestamp always wins. Re-submitting the same `idempotency_key` returns the stored result without re-processing.

### Sync Pull

- Method: POST
- URL: {{base_url}}/sync/pull
- Auth: Yes (any authenticated role)

Request body:

```json
{
  "device_uuid": "pos-branch1-001",
  "cursor": 0,
  "branch_id": {{branch_id}},
  "limit": 100
}
```

Success response (200):

```json
{
  "device_uuid": "pos-branch1-001",
  "cursor": 0,
  "next_cursor": 42,
  "has_more": false,
  "events": [
    {
      "id": 1,
      "entity_type": "order",
      "entity_id": "10",
      "event_type": "created",
      "payload_json": {"order_no": 10},
      "created_at": "2026-04-11T10:01:00Z"
    }
  ]
}
```

Cursor usage: on next pull, pass `next_cursor` as `cursor` to receive only new events.

Common Phase 10 errors:

- 400 when `device_uuid` is not registered or belongs to a different tenant.
- 400 when `branch_id` does not belong to the caller's tenant.
- 401 when no auth token is provided.

## 5. Common Troubleshooting

- 401 Unauthorized:
  - Access token missing or expired
  - Use refresh endpoint and retry
- 403 Forbidden:
  - Logged-in user role does not have required permission
- 423 Locked on PIN login:
  - Too many failed PIN attempts, wait for lock timeout
- 400 Validation errors:
  - Check exact field names and value formats in payload

## 6. Documentation Update Rules

When adding or changing any API:

1. Update route and method in this file
2. Add or update request payload sample
3. Add or update success response sample
4. Add known error response samples
5. Add auth and role requirements

Keeping this file up to date is part of done criteria for every backend feature.
