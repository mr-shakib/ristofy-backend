# Swagger and OpenAPI Status

Last verified: 2026-04-11

## 1. Current Status

Swagger UI and OpenAPI schema are available in this backend project.

Verification summary:
1. Swagger/OpenAPI package is installed and pinned in requirements.
- `drf-spectacular==0.28.0`

2. Schema and docs routes are wired in URL config.
- `/api/schema/`
- `/api/docs/swagger/`
- `/api/docs/redoc/`

3. Schema generation settings are configured in Django settings.
- `DEFAULT_SCHEMA_CLASS = drf_spectacular.openapi.AutoSchema`
- `SPECTACULAR_SETTINGS` configured with title, description, and version.

## 2. Impact

1. LLMs and frontend tools can consume a machine-readable API schema.
2. Interactive docs are available for faster backend/frontend integration.

## 3. Access Endpoints

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/swagger/`
- ReDoc: `/api/docs/redoc/`

## 4. Recommended Next Step

1. Generate and archive schema in CI for contract checks.
2. Add explicit schema annotations where custom serializers/actions are ambiguous.
3. Keep docs endpoints available in non-production and restricted as needed in production.

## 5. Minimal Acceptance Criteria

1. All existing endpoints appear in schema.
2. Auth bearer token security scheme is defined.
3. Key serializers for request/response are represented.
4. CI validates schema generation success.
