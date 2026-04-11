# Free Deployment Guide: Render + Neon

Last updated: 2026-04-11

This is the recommended free deployment path for this backend.

## 1. Why this stack

1. Render free web service is simple and stable for Django APIs.
2. Neon provides a free managed PostgreSQL tier.
3. Setup is fast and requires minimal infrastructure management.

## 2. Important free-tier realities

1. Render free web services can sleep on inactivity.
2. First request after sleep has cold start latency.
3. Free tiers can change quotas over time.

## 3. Prerequisites

1. GitHub repo with this backend.
2. Render account.
3. Neon account.

## 4. Create free Postgres on Neon

1. Create a new Neon project.
2. Copy connection details:
- host
- database name
- user
- password
- port (usually 5432)

## 5. Deploy to Render

1. In Render, choose New + Blueprint.
2. Connect your GitHub repo.
3. Render detects render.yaml automatically.
4. Create the web service.

## 6. Set required environment values in Render

From Neon:
1. DB_NAME
2. DB_USER
3. DB_PASSWORD
4. DB_HOST
5. DB_PORT

From your frontend domain:
6. CORS_ALLOWED_ORIGINS
7. CSRF_TRUSTED_ORIGINS

From your Render URL:
8. ALLOWED_HOSTS should include your actual Render domain and custom domain if any.

## 7. First boot commands

After first deploy, open Render Shell and run:

1. python manage.py migrate --noinput
2. python manage.py check

Optional admin user:
3. python manage.py createsuperuser

## 8. Verify deployment

1. GET /api/v1/health should return 200.
2. GET /api/v1/health/db should return 200.
3. GET /api/docs/swagger/ should load.
4. POST /api/v1/auth/login with smoke user should return token payload.

## 9. Production safety settings checklist

1. DEBUG=False
2. SECRET_KEY strong and secret
3. HTTPS-only frontend origins
4. Explicit ALLOWED_HOSTS
5. Secure cookies and SSL redirect enabled

Reference hardening checklist:
- docs/runbooks/production-checklist.md

## 10. Troubleshooting

1. App boots but DB fails:
- verify DB_HOST and credentials from Neon
- ensure Neon IP/access settings allow Render

2. 400 bad request from frontend:
- verify CORS_ALLOWED_ORIGINS and CSRF_TRUSTED_ORIGINS

3. 502/503 on Render:
- check deploy logs
- confirm gunicorn start command and module path

4. Sleep latency on free plan:
- expected behavior for inactive free services

## 11. Upgrade path when traffic grows

1. Move Render web service to paid always-on plan.
2. Upgrade Neon tier and enable stronger backup/retention.
3. Add Redis and worker process when async jobs are introduced.
