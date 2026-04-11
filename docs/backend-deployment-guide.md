# Backend Deployment Guide

Last updated: 2026-04-11

## 1. Recommended Production Architecture

Use this baseline for reliability and maintainability:

1. Platform
- AWS ECS Fargate (or GKE/AKS equivalent) for stateless API containers

2. Database
- Managed PostgreSQL (Amazon RDS or Cloud SQL) with PITR enabled

3. Edge and TLS
- Application Load Balancer with HTTPS termination
- Enforce redirect HTTP to HTTPS

4. Secrets
- AWS Secrets Manager or equivalent
- No secret values in repository

5. Logging and Monitoring
- Centralized logs (CloudWatch, Datadog, Loki)
- APM and alerts for latency, 5xx, DB failures, missing device heartbeat

6. Background workers
- Keep worker service slot ready for Celery when async jobs are enabled

## 2. Why this is best for your project

1. Your backend is already stateless API-first and container-friendly.
2. Health endpoints exist and map directly to orchestrator liveness/readiness probes.
3. PostgreSQL is required and managed DB simplifies backups and failover.
4. Sync and operational endpoints need stable uptime and observability.

## 3. Environment Configuration

Set production env values at deploy runtime:

- ENVIRONMENT=production
- DEBUG=False
- SECRET_KEY=<50+ chars>
- ALLOWED_HOSTS=<exact domains>
- CORS_ALLOWED_ORIGINS=<frontend domains only>
- CSRF_TRUSTED_ORIGINS=<frontend https origins>
- DB_ENGINE=django.db.backends.postgresql
- DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
- LOG_LEVEL=INFO
- SECURE_SSL_REDIRECT=True
- SECURE_HSTS_SECONDS=31536000
- THROTTLE_AUTH_LOGIN, THROTTLE_PIN_LOGIN, THROTTLE_BURST, THROTTLE_SUSTAINED

Reference:
- docs/runbooks/production-checklist.md
- .env.example

## 4. Build and Release Strategy

## 4.1 CI pipeline stages

1. Install dependencies
2. Django checks
3. Migration checks
4. Test suite
5. Build container image
6. Push image to registry
7. Deploy to staging
8. Smoke tests
9. Manual approval
10. Deploy to production

## 4.2 Required quality gates

1. manage.py check passes
2. manage.py makemigrations --check --dry-run passes
3. manage.py test passes
4. No critical vulnerabilities in dependency scan

## 5. Runtime Process Model

API process:
- gunicorn core.wsgi:application

Recommended starting config:
- workers: 2 x CPU cores + 1
- timeout: 60
- graceful timeout: 30
- keep-alive: 5

Tune with staging load tests from load_tests/locustfile.py.

## 6. Zero-Downtime Deployment Flow

1. Deploy image to staging
2. Run migrations in staging and smoke test
3. Run Locust baseline on staging
4. Approve production rollout window
5. Run production migrations
6. Roll out new API tasks with rolling strategy
7. Verify health and auth smoke tests
8. Monitor 15 minutes before closing window

## 7. Health and Smoke Tests

After each deployment validate:

1. GET /api/v1/health returns 200
2. GET /api/v1/health/db returns 200
3. POST /api/v1/auth/login with smoke user returns token payload

Use the post-deploy checklist in docs/runbooks/production-checklist.md.

## 8. Database and Migration Safety

1. Enable backups and PITR
2. Rehearse migrations on production-like clone
3. Schedule heavy migrations during low traffic
4. Keep rollback plan per release

Operational rollback references:
- docs/runbooks/operations.md

## 9. Security Hardening

1. Restrict /admin/ by IP at load balancer
2. Enforce secure cookie and HSTS settings
3. Rotate secrets periodically
4. Keep dependency audits in CI
5. Ensure CORS allowlist is explicit

## 10. Observability and Alerts

Minimum alerts:

1. 5xx rate over 1 percent for 5 minutes
2. p95 latency over 500 ms for 5 minutes
3. DB readiness failures
4. Device heartbeat stale over 5 minutes

## 11. Recommended Deployment Order by Environments

1. Local
2. Shared development
3. Staging with production-like DB size
4. Production canary or rolling deploy

## 12. If you need fastest initial launch

For a simpler first production launch:

1. Use a single VM with Docker Compose
2. Place Nginx in front of Gunicorn
3. Use managed PostgreSQL outside VM
4. Set up daily backups and log shipping
5. Migrate to ECS/Kubernetes when traffic grows

This is acceptable for early stage but not ideal long-term for HA.
