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
