# Production Readiness Checklist

Complete every item before promoting a build to production.

## 1. Environment and Secrets

- [ ] `SECRET_KEY` is at least 50 characters and not committed to source control
- [ ] `DEBUG=False` in the production environment
- [ ] `ALLOWED_HOSTS` set to the exact production domain(s) — no wildcards
- [ ] `CORS_ALLOWED_ORIGINS` lists only trusted frontend origins
- [ ] `DATABASE_URL` / `DB_*` variables point to the production database
- [ ] No `.env` files committed; secrets loaded from a secret manager or environment injection
- [ ] JWT keys rotated from any dev/staging values

## 2. Database

- [ ] All migrations applied: `manage.py migrate --check`
- [ ] No unapplied migrations: `manage.py makemigrations --check --dry-run`
- [ ] Point-in-time recovery (PITR) enabled on the PostgreSQL cluster
- [ ] Automated daily backup verified with a restore test
- [ ] Connection pooler (PgBouncer or RDS proxy) configured for production traffic

## 3. Security

- [ ] `SECURE_SSL_REDIRECT=True` and HSTS headers enabled
- [ ] `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`
- [ ] `SECURE_HSTS_SECONDS >= 31536000` (1 year)
- [ ] Rate limiting active — confirm `THROTTLE_AUTH_LOGIN`, `THROTTLE_PIN_LOGIN` env vars are set
- [ ] Dependency audit run: `pip-audit` or `safety check` returns no critical CVEs
- [ ] Admin endpoint (`/admin/`) restricted to trusted IP ranges at the load balancer

## 4. Static Files and Media

- [ ] `collectstatic` run and output served via CDN or object storage (not Django)
- [ ] `STATIC_ROOT` and `MEDIA_ROOT` are writable and backed up

## 5. Observability

- [ ] `LOG_LEVEL=INFO` (or `WARNING`) in production — never `DEBUG`
- [ ] Logs are shipped to a central log aggregator (Datadog, Loki, CloudWatch, etc.)
- [ ] APM / distributed tracing enabled on the API process
- [ ] Alerts configured for:
  - HTTP 5xx rate > 1% over 5 minutes
  - p95 response time > 500 ms over 5 minutes
  - Database connection errors
  - Missing heartbeat from any registered device for > 5 minutes

## 6. Health Probes

- [ ] Liveness probe: `GET /api/v1/health` — used by the container orchestrator restart policy
- [ ] Readiness probe: `GET /api/v1/health/db` — gates traffic until DB is reachable
- [ ] Both probes respond in under 100 ms under zero load

## 7. Load and Performance

- [ ] Locust baseline run completed against staging: `load_tests/locustfile.py`
- [ ] p95 latency for read endpoints < 250 ms at 50 concurrent users
- [ ] p95 latency for order-fire endpoint < 1 second at 50 concurrent users
- [ ] No database N+1 queries on hot paths (profiled with Django Debug Toolbar or pgBadger)
- [ ] DB indexes verified on: `order(tenant, branch, status)`, `bill(branch, bill_no)`,
  `outbox_event(tenant, branch, id)`, `sync_push_record(idempotency_key)`

## 8. Migrations Rehearsal

- [ ] Forward migration rehearsed on a clone of production data
- [ ] Rollback path documented for every migration in the release
- [ ] Long-running migrations (table rewrites on large tables) scheduled during low-traffic window
- [ ] `select_for_update` paths reviewed for lock duration under production row counts

## 9. Release Process

- [ ] Release branch cut from `main`; no direct pushes to `main`
- [ ] CI pipeline green (tests, lint, migration check)
- [ ] Deployment plan reviewed by at least one other engineer
- [ ] Rollback plan documented: which commit to revert to, how to reverse migrations
- [ ] On-call engineer designated and paged into the deployment window

## 10. Post-Deployment Smoke Tests

Run within 5 minutes of deploying:

```bash
# Liveness
curl -sf https://<host>/api/v1/health

# Readiness
curl -sf https://<host>/api/v1/health/db

# Auth round-trip
curl -sf -X POST https://<host>/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"<smoke_user>","password":"<smoke_pass>"}'
```

Monitor error rates and latency for 15 minutes post-deploy before closing the deployment window.
