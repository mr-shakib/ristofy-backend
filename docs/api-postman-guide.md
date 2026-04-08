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

## 2. Quick End-to-End Test Flow in Postman

Run requests in this order:

1. Register tenant owner account
2. Login with username and password
3. Get branches
4. Create branch
5. Get users
6. Create user
7. Set PIN for a user
8. Login with PIN
9. Refresh token

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
```

Add this to refresh request Tests tab:

```javascript
const json = pm.response.json();
if (json.access) pm.environment.set("access_token", json.access);
if (json.refresh) pm.environment.set("refresh_token", json.refresh);
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
