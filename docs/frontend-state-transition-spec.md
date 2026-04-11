# Frontend State Transition Specification

Last updated: 2026-04-11

This document defines UI state machines required for predictable behavior in a production desktop app.

## 1. Order State Machine

## 1.1 Primary states
- OPEN
- HELD
- SENT_TO_KITCHEN
- COMPLETED
- CANCELED

## 1.2 Allowed transitions
1. OPEN -> HELD via POST /orders/{id}/hold
2. OPEN -> SENT_TO_KITCHEN via /orders/{id}/fire or /send-to-kitchen
3. HELD -> SENT_TO_KITCHEN via /orders/{id}/fire or /send-to-kitchen
4. OPEN -> CANCELED via /orders/{id}/cancel (owner/manager)
5. HELD -> CANCELED via /orders/{id}/cancel (owner/manager)
6. SENT_TO_KITCHEN -> COMPLETED via /orders/{id}/complete (owner/manager)

## 1.3 UI rules
1. Disable edit-item actions once order is terminal.
2. Disable hold action unless state is OPEN.
3. Disable complete/cancel for waiter/cashier.
4. Show event timeline from /orders/{id}/events after each transition.

## 2. Kitchen Ticket State Machine

## 2.1 Primary states
- QUEUED
- PREPARED

## 2.2 Allowed transition
1. QUEUED -> PREPARED via POST /kitchen/tickets/{id}/prepared

## 2.3 UI rules
1. Prepared action must be idempotent in UI to avoid double-submit.
2. Ticket board should refresh after successful prepared action.

## 3. Table State and Session Machine

## 3.1 Core states (business view)
- FREE
- OCCUPIED
- RESERVED
- OUT_OF_SERVICE

## 3.2 Session transitions
1. No active session -> Active session via POST /tables/{id}/open-session
2. Active session -> Closed session via POST /tables/{id}/close-session
3. Multiple active tables -> merged session via POST /tables/merge
4. Merged session -> split result via POST /tables/split/{id}

## 3.3 UI rules
1. Prevent opening second session on same table if one is active.
2. Prevent close-session if open billing/order invariants fail (show API detail).
3. Merge UI must enforce same branch table selection.

## 4. Reservation and Waitlist State Machine

## 4.1 Reservation transitions
1. Pending/confirmed -> arrived via POST /reservations/{id}/arrived
2. Any non-terminal -> canceled via POST /reservations/{id}/cancel

## 4.2 Waitlist transitions
1. Waiting -> called via POST /waitlist/{id}/call
2. Called/waiting -> seated via POST /waitlist/{id}/seat
3. Waiting/called -> canceled via POST /waitlist/{id}/cancel

## 5. Bill State Machine

## 5.1 Primary states
- DRAFT
- FINALIZED
- PAID

## 5.2 Allowed transitions
1. create-from-order creates DRAFT bill
2. DRAFT -> DRAFT after apply-coperto/apply-discount/split/pay(partial)
3. DRAFT -> FINALIZED via POST /bills/{id}/finalize
4. DRAFT or FINALIZED -> PAID when cumulative payments cover grand_total

## 5.3 UI rules
1. Lock line edits after FINALIZED.
2. Keep pay action available until PAID.
3. Disable fiscal send until bill reaches required backend-ready state.

## 6. Receipt/Fiscal State Notes

1. Bill to fiscal send triggers receipt lifecycle.
2. Reprint and refund are receipt-driven actions.
3. Z-report status and sync are manager controls.

## 7. Sync Push Result State Machine

## 7.1 Push item states
- ACCEPTED
- CONFLICT

## 7.2 Transition rules
1. New outbox item -> ACCEPTED when server entity timestamp allows apply.
2. New outbox item -> CONFLICT when server timestamp is newer.
3. Re-submitted idempotency_key returns same stored result.

## 7.3 UI rules
1. Accepted items leave queue and mark done.
2. Conflict items move to conflict panel with side-by-side details.
3. Do not auto-retry conflict items without user decision.
