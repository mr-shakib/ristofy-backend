# Swagger/OpenAPI Enablement (Implemented)

Last updated: 2026-04-11

Swagger has been enabled with drf-spectacular for machine-readable API contracts and interactive docs.

## 1. Package Choice

Recommended: drf-spectacular

Why:
1. Active maintenance
2. Strong DRF integration
3. Easy Swagger + ReDoc support

## 2. Implemented Steps

1. Package installed:
- drf-spectacular==0.28.0

2. App added in settings INSTALLED_APPS:
- drf_spectacular

3. Schema class configured in REST_FRAMEWORK:
- DEFAULT_SCHEMA_CLASS = drf_spectacular.openapi.AutoSchema

4. SPECTACULAR_SETTINGS configured:
- TITLE, DESCRIPTION, VERSION
- SERVE_INCLUDE_SCHEMA=False
- SCHEMA_PATH_PREFIX=/api/v1

5. URLs wired:
- /api/schema/
- /api/docs/swagger/
- /api/docs/redoc/

6. Django checks validated successfully after configuration.

## 3. Live Endpoints

1. Schema: `/api/schema/`
2. Swagger UI: `/api/docs/swagger/`
3. ReDoc: `/api/docs/redoc/`

## 4. CI Gates

1. Generate schema in CI and fail on command errors.
2. Keep schema artifact versioned for frontend contract checks.
3. Validate that new endpoints appear after backend merges.

## 5. Frontend LLM Benefit

1. Single source of truth for endpoint models.
2. Better type-safe client generation.
3. Reduced hallucinated payload fields.
4. Faster iteration and fewer integration bugs.
