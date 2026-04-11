# Frontend Sync and Offline Specification

Last updated: 2026-04-11

## 1. Purpose

Guarantee operational continuity during intermittent connectivity without silent data loss.

## 2. Local Persistence Objects

## 2.1 OutboxAction

Required fields:
- local_action_id (uuid)
- idempotency_key (string)
- endpoint (string)
- method (string)
- payload_json (json)
- created_at (timestamp)
- retry_count (int)
- status (PENDING, RETRYING, ACCEPTED, CONFLICT, FAILED)
- last_error (string)

## 2.2 SyncCursor

Fields:
- device_uuid
- branch_id
- last_cursor
- updated_at

## 2.3 ConflictRecord

Fields:
- idempotency_key
- entity_type
- entity_id
- server_detail
- device_payload
- created_at
- resolved (bool)

## 3. Device Lifecycle

1. First launch
- register device via /devices/register

2. Recurring heartbeat
- /devices/heartbeat every N seconds (recommend 30-60)

3. Session open
- pull initial deltas via /sync/pull

## 4. Push Workflow

1. Every mutating user action writes OutboxAction before API call.
2. Foreground call may execute immediately.
3. If call fails due to network/transient errors, leave in queue.
4. Background worker sends queued items to /sync/push.
5. Handle each result:
- ACCEPTED: mark done
- CONFLICT: write ConflictRecord and require manual resolution

## 5. Pull Workflow

1. On interval and after successful push, call /sync/pull with cursor.
2. Apply returned events deterministically by event id order.
3. Update cursor to next_cursor after durable local apply.
4. If has_more is true, continue paging.

## 6. Conflict Handling

1. Display conflict queue in dedicated panel.
2. Show:
- entity type/id
- conflict detail
- device payload summary
3. Resolution actions:
- keep server version (drop local)
- retry with amended payload and new idempotency key

## 7. Retry and Backoff

1. Retry classes
- class A: network timeout, connection error
- class B: 5xx
- class C: 429

2. Policy
- exponential backoff with jitter
- cap max attempts per action
- after max attempts: FAILED and surface in UI

## 8. Data Safety Rules

1. Never delete queue item before durable ACCEPTED response.
2. Never reuse idempotency_key for new semantic action.
3. Never auto-resolve CONFLICT items.
4. Always audit sync errors in local logs.

## 9. Operational Metrics

Track and expose:
- pending queue size
- conflict count
- failed count
- average push latency
- last successful pull timestamp

## 10. LLM Implementation Tasks

1. Build Outbox repository with transactional writes.
2. Build SyncEngine with push-first then pull strategy.
3. Build conflict UI panel and resolution actions.
4. Add unit tests for idempotency and retry branches.
