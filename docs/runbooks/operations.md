# Operations Runbook

Reference for on-call engineers. Each section describes a scenario, its symptoms,
diagnosis steps, and remediation.

---

## 1. Elevated 5xx Rate

**Symptoms:** Alerts fire on HTTP 5xx rate > 1%.

**Diagnosis:**
```bash
# Tail application logs for tracebacks
journalctl -u ristofy-api -n 200 --no-pager | grep ERROR

# Check DB connectivity
curl -sf https://<host>/api/v1/health/db
```

**Remediation:**
- If DB unreachable: check PostgreSQL service and connection pool saturation.
- If Django traceback: identify failing view from log `request_id`, redeploy previous release if needed.
- If OOM: increase worker memory limits or reduce `--workers` count in Gunicorn config.

---

## 2. High Response Latency (p95 > 500 ms)

**Symptoms:** APM alert or user reports.

**Diagnosis:**
```bash
# Identify slow queries (requires pg_stat_statements enabled)
psql $DATABASE_URL -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;"
```

**Remediation:**
- Add missing index (see production checklist §7 for known hot-path indexes).
- Check for N+1 via Django Debug Toolbar on staging with production data clone.
- Scale API replicas horizontally if CPU-bound.

---

## 3. Fiscal Callback Failures

**Symptoms:** `FiscalTransaction` records stuck in `SENT` status; no `ACKED` or `COMPLETED`.

**Diagnosis:**
```bash
# Count stuck transactions (run in Django shell or psql)
# SELECT COUNT(*) FROM billing_fiscaltransaction WHERE status = 'SENT'
#   AND created_at < NOW() - INTERVAL '10 minutes';
```

**Remediation:**
1. Check bridge device connectivity at the branch.
2. Manually call `POST /api/v1/integrations/bridge/fiscal-ack` with the `external_id` once bridge is restored.
3. If bridge is offline indefinitely, escalate to fiscal support team — do not auto-complete without bridge confirmation.

---

## 4. Inventory Stock Goes Negative (Edge Case)

**Symptoms:** `ValueError: Stock cannot go below zero` appearing in logs during order fire.

**Diagnosis:**
- Indicates concurrent orders firing the same recipe component without enough stock.
- Check `StockMovement` ledger for the ingredient.

**Remediation:**
- `select_for_update()` is already in place; this should not occur under normal load.
- If it does, verify the lock is not being skipped (e.g., raw SQL or admin direct edits).
- Manually create a `STOCK_IN` movement to restore positive stock, then re-fire the order.

---

## 5. Missing Device Heartbeat Alert

**Symptoms:** Monitoring alerts that a device `last_seen_at` is stale (> 5 min).

**Diagnosis:**
- Device may be offline, app may have crashed, or network connectivity lost at branch.

**Remediation:**
1. Contact the branch to check device power and connectivity.
2. If device is online, restart the POS app — it will re-register on next launch.
3. If persistent, check `Device.is_active` flag; deactivate and re-register if hardware replaced.

---

## 6. Rate Limit False Positives (429 for Legitimate Users)

**Symptoms:** Users report being blocked on login.

**Diagnosis:**
- Check if the IP is shared (NAT, proxy) causing multiple users to share a throttle bucket.

**Remediation:**
- Temporarily raise `THROTTLE_AUTH_LOGIN` env var (e.g., `30/minute`) and restart the API.
- For shared IP environments, consider switching to user-based throttle scope for authenticated endpoints.
- The throttle uses Django's default cache backend — if Redis is down it falls back to in-memory (per process), which may not rate-limit correctly across replicas.

---

## 7. Django Migration Rollback

**To roll back the last migration for an app:**
```bash
./venv/bin/python manage.py migrate <app_name> <previous_migration_name>
# Example: roll sync back to zero
./venv/bin/python manage.py migrate sync zero
```

**To list applied migrations:**
```bash
./venv/bin/python manage.py showmigrations
```

Always test rollback on a staging DB clone before applying to production.

---

## 8. Cache Corruption (Report Data Stale)

**Symptoms:** Report endpoints return outdated data even after data changes.

**Remediation:**
```bash
# Invalidate all report cache for all tenants via API
curl -X POST https://<host>/api/v1/reports/cache/invalidate \
  -H "Authorization: Bearer <owner_token>"
```

If Django cache backend is Redis and Redis is unreachable, the cache silently degrades —
reports will run live queries at higher cost until Redis recovers.

---

## 9. Gunicorn / uWSGI Worker Restart

**To gracefully reload workers without dropping connections:**
```bash
# Gunicorn
kill -HUP $(cat /var/run/gunicorn.pid)
```

**To check worker count and status:**
```bash
ps aux | grep gunicorn
```

---

## 10. Full Service Restart Order

If a full restart is required:

1. Stop Celery workers (when wired): `systemctl stop ristofy-worker`
2. Stop the API: `systemctl stop ristofy-api`
3. Run pending migrations: `./venv/bin/python manage.py migrate`
4. Start the API: `systemctl start ristofy-api`
5. Start Celery workers: `systemctl start ristofy-worker`
6. Verify: `curl -sf https://<host>/api/v1/health/db`
