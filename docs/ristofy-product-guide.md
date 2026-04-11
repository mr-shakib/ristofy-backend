# Ristofy — Restaurant Operations Platform
### Complete Product Guide

---

## The Problem with Running a Restaurant

Running a restaurant means managing five things at once — a dining room full of guests, a kitchen under pressure, a cashier handling payments, a manager watching costs, and an owner who needs to know what happened today. Most teams cobble this together with whiteboards, shouted tickets, and spreadsheets. The result is lost orders, wrong bills, slow tables, and a manager who cannot answer the most basic question at close of day: *did we make money?*

Ristofy replaces that chaos with a single, connected platform that every role in the restaurant uses — from the moment a table is seated to the moment the till is closed.

---

## What Ristofy Does

Ristofy is a full-service restaurant management platform built for desktop (Windows and macOS). It connects every station in your restaurant — front of house, kitchen, cashier, and management — through one live system.

- Waiters manage tables and take orders on their screens.
- The kitchen sees tickets the moment an order is fired.
- The cashier handles the bill without ever asking the waiter what was ordered.
- The owner sees today's revenue, top dishes, and table utilisation without leaving the office.

Everything is connected. Everything is live. And if the internet goes down, Ristofy keeps working and syncs when it comes back.

---

## Who Uses Ristofy

Ristofy is built around five roles. Each person sees exactly what they need — nothing more, nothing less.

### Owner
Full visibility across the entire operation. Reviews daily reports, monitors revenue, manages users and permissions, oversees menu pricing, and approves fiscal actions. The owner dashboard surfaces what matters: revenue, seat turns, top-selling dishes, and any operational alerts.

### Manager
Runs the day-to-day. Opens and closes the restaurant, manages the floor plan, adjusts the menu, monitors kitchen throughput, and reviews bills before they go to fiscal. The manager can act on anything the owner can — and is the first point of escalation when something goes wrong on the floor.

### Waiter
Lives on the floor. Opens table sessions, takes orders from the menu, fires courses to the kitchen, requests bills, and seats guests from the waitlist or reservations. The waiter interface is fast and touch-friendly — designed to be used mid-service, not at a desk.

### Cashier
Owns the payment desk. Receives bills from the floor, applies discounts or split payments, finalises the bill, takes payment, and sends to the fiscal printer. Every action is logged and protected — the cashier cannot edit what the waiter ordered, only settle it.

### Kitchen
Sees only what matters: the ticket queue. Incoming orders appear immediately when fired by the waiter, grouped by course and priority. One tap marks a ticket as prepared and clears it from the board.

---

## Core Modules

### 1. Floor and Table Management

The floor screen shows every table in your restaurant with a live colour-coded status:

| Colour | Meaning |
|---|---|
| Green | Free — available to seat |
| Orange | Occupied — session open, order in progress |
| Blue | Reserved — guest expected |
| Grey | Out of service — temporarily unavailable |

Waiters open a table session with one tap. Closing a session automatically handles any outstanding billing checks. Tables can be **merged** (two parties combined onto one bill) or **split** (one party divided into separate bills) without manual recalculation.

The floor screen also shows the **waitlist** and **reservations panel** side by side, so the host always knows who is waiting, how long they have been waiting, and which tables are about to free up.

### 2. Reservations and Waitlist

Guests can be pre-booked with a reservation (date, time, party size, name, notes) or added to the live waitlist when they walk in without a booking.

- Call a waitlist guest when a table becomes available — one tap sends the notification.
- Mark a reservation as arrived, and the system locks the table for them.
- Cancel either without losing the record — the history is always retained.

No more sticky notes by the host stand.

### 3. Order Taking and the Order Composer

The order composer is where the waiter builds the order. It is designed for speed:

- **Category navigation** at the top — tap a category to see only those items.
- **Item tiles** show the name and price. One tap adds it to the order.
- **Quantity, variants, and add-ons** can be set per line.
- The live order panel on the right shows what has been added, what has been sent to the kitchen, and what is still pending.

Each order line carries a status — **Pending, Sent, Prepared** — so the waiter knows the state of every dish without going to the kitchen.

#### Order Actions

| Action | What It Does |
|---|---|
| **Hold** | Saves the order without sending to kitchen. Use when the table is still deciding. |
| **Fire** | Sends all pending items to the kitchen immediately. |
| **Course Fire** | Sends specific items by course — starter first, then mains when ready. |
| **Request Bill** | Signals to the cashier that this table is ready to pay. |

Every action is guarded by state. You cannot fire an order that has already been sent. You cannot request a bill that has not been fired. The system prevents the mistakes that happen when things move fast.

#### Order Event Timeline

Every order carries a live timeline — a log of every action from creation to close. When did it open? When was it fired? When did the kitchen confirm? When was the bill requested? The timeline is always visible in the order screen, so any staff member can answer a guest's question without guessing.

### 4. Kitchen Board

The kitchen screen is a two-column board:

- **Left column: Pending** — tickets waiting to be prepared, ordered by time received.
- **Right column: Prepared** — tickets the kitchen has completed, waiting to be served.

Each ticket shows the ticket number, order number, and course. The board auto-refreshes every 12 seconds. A manual refresh button is always available.

When the kitchen marks a ticket as prepared, it moves to the right column and the waiter is able to serve. No more paper tickets. No more shouting across the pass.

### 5. Takeaway Orders

Takeaway is a first-class workflow, not an afterthought.

- Look up a customer by phone number — their history and loyalty status appear immediately.
- Create a takeaway order from the same menu as dine-in.
- Fire to the kitchen in the same way — kitchen staff see no difference.
- Mark the order as ready when it is packed — the customer-facing status updates.
- Bill and payment work identically to dine-in.

### 6. Loyalty Programme

Every takeaway customer can be enrolled in the loyalty programme automatically.

- Visit history is recorded on every completed order.
- Loyalty eligibility is checked at billing time — does this customer qualify for a reward?
- Visit credits are issued on confirmed payment.

The system does not require a separate app or card — phone number is the identifier. Guests who have been coming for years are recognised the moment they call.

### 7. Buffet Mode

For restaurants that run buffet service — fixed-price, all-you-can-eat sittings — Ristofy has a dedicated buffet engine:

- Create a **buffet plan** with a cover price and round structure.
- Open a **buffet session** at the start of service.
- Record **rounds** as guests move through the buffet — quantity per guest, per sitting.
- Log **waste** at the end of service and attach it to the session for cost tracking.
- Compare performance across branches with the **buffet branch comparison report**.

### 8. Billing and Payments

The billing workspace is where money changes hands. It is clean, fast, and prevents errors.

**Creating a bill:**
The cashier creates a bill from the order with one action. Everything the waiter ordered is already on the bill — no re-entry, no discrepancies.

**Bill adjustments (before finalising):**

| Adjustment | Details |
|---|---|
| **Coperto** | Cover charge per head — applied to the bill automatically. |
| **Discount** | Fixed amount (€) or percentage (%). Applied to the grand total. |
| **Split bill** | Divide into two or more equal parts. Each part becomes its own bill. |

**Finalising and paying:**

Once the bill is finalised, no further changes can be made to the amount. Payment can be taken in:

- **Cash**
- **Card**
- **Other** (voucher, account, etc.)

Partial payments are supported — the system tracks how much has been paid and how much remains. A progress bar shows payment completion in real time. The cashier cannot accidentally take double payment.

**Bill status flow:**

```
DRAFT → FINALIZED → PAID
```

Each status is clearly displayed. Actions are only available at the correct status — there is no way to finalise a bill that has already been paid, or pay a bill that has not been finalised.

### 9. Fiscal Integration

For restaurants in Italy and compliant jurisdictions, Ristofy handles the full fiscal receipt lifecycle:

- **Send to fiscal** — transmit the finalised bill to the fiscal printer or bridge.
- **Receipt tracking** — every fiscal receipt is stored with its fiscal number, timestamp, and bill reference.
- **Reprint** — reprint a receipt at any time.
- **Refund** — issue a fiscal refund with a recorded reason and amount.
- **Z-report** — end-of-day fiscal closure with one action.

All fiscal actions are owner/manager level. The cashier executes; the system records. Nothing is lost.

### 10. Inventory Management

Ristofy tracks inventory at the ingredient level so you always know what you have and what you are running low on.

**What is tracked:**

- **Ingredients** — every item in your store, with unit, current stock, and low-stock threshold.
- **Recipes** — which ingredients are used in each menu item, and in what quantity.
- **Auto-deduction** — when an order is fired to the kitchen, the recipe ingredients are automatically deducted from stock. You always have a live stock count.
- **Stock movements** — every movement (receiving, waste, adjustment) is logged with a reason and timestamp.

**Receiving stock:**
When a delivery arrives, the manager records a receiving entry against a purchase order. Stock is updated immediately. The receiving history is permanent — useful for audits and supplier disputes.

**Low-stock alerts:**
The manager dashboard shows a low-stock panel. Any ingredient below its threshold appears here, with current stock and the threshold it crossed. Nothing runs out as a surprise.

**Purchase orders:**
Create purchase orders for suppliers, track their status, and receive against them directly.

### 11. Reporting and Analytics

Ristofy gives owners and managers the numbers they need to run a profitable restaurant — without exporting to spreadsheets.

**Daily snapshots:**
A consolidated summary of each day's performance — covers, revenue, average spend, and VAT — captured automatically at close of business.

**Sales reports:**

| Report | What it shows |
|---|---|
| **By category** | Which parts of the menu are driving revenue |
| **By table** | Which tables turn fastest and spend most |
| **By waiter** | Individual performance — covers served, revenue generated |
| **By VAT rate** | Revenue split by VAT bracket, ready for accounting |

**Buffet branch comparison:**
For multi-branch operators, compare buffet revenue, waste, and round averages across locations side by side.

**Cache controls:**
Reports use a smart cache to keep the dashboard fast under load. Managers can force a refresh when they need real-time accuracy — for example, at end of shift before the manager signs off.

### 12. Multi-Branch Support

Ristofy is a **multi-tenant, multi-branch platform**. A restaurant group can have one account with multiple locations, each fully isolated from the others.

- Each branch has its own tables, menu, staff, and reports.
- Staff are assigned to a branch — a waiter at Branch A cannot see Branch B's orders.
- Owners can view all branches. Managers see only their assigned branch.
- Branch comparison reports let the owner see all locations side by side.

There is no technical limit on the number of branches.

---

## The Complete Shift: Open to Close

Here is a full restaurant shift in Ristofy, step by step.

### Opening
1. Manager or waiter logs in with username and password (or fast PIN).
2. The app registers the device automatically — no configuration needed.
3. The floor screen loads showing today's table states and any reservations.
4. The menu is ready. The kitchen board is empty. The shift begins.

### During Service
**A reservation arrives:**
- The host marks the reservation as arrived.
- The table opens automatically.
- The waiter navigates to the table and opens the order composer.

**The order is taken:**
- Waiter selects items from the categorised menu.
- Starters are added. The waiter holds until the table has decided on mains.
- Starters are fired to the kitchen as a first course.
- The kitchen sees the ticket appear on the board instantly.
- Kitchen marks starters prepared. The waiter serves them.
- Mains are fired. Kitchen prepares and marks prepared.

**Bill time:**
- Waiter taps Request Bill.
- Cashier sees the table flagged in the billing queue.
- Cashier opens the bill — everything is already on it.
- Coperto is applied (2 guests × €2.50 = €5.00 added automatically).
- No discount tonight. Bill is finalised.
- Guest pays by card. Cashier records the payment.
- Bill moves to PAID.
- Fiscal receipt is sent. The guest receives their receipt.
- Waiter closes the table session. The table turns green on the floor screen.

**A walk-in joins the waitlist:**
- Host adds the guest to the waitlist — name and party size.
- When a table frees up, host calls the guest (one tap).
- Guest is seated and a new session opens.

### Closing
1. Manager reviews the sales report — revenue, covers, average spend.
2. Checks the low-stock panel — anything to order for tomorrow?
3. Runs the daily snapshot if not already auto-captured.
4. Sends the fiscal Z-report to close the day's fiscal session.
5. Logs out. The system records the sign-out in the activity log.

---

## What Happens When the Internet Goes Down

Ristofy is designed for the reality of restaurant Wi-Fi: it is not always reliable.

When connectivity is lost:
- The app continues to work. Orders can be taken, fired, and managed.
- Every action that cannot be sent immediately is queued locally in the outbox.
- The outbox icon appears in the interface so staff know sync is pending.

When connectivity is restored:
- Queued actions are sent to the server automatically, in order, with idempotency keys — so nothing is sent twice.
- The app pulls any changes made on other devices during the outage.
- Conflicts (cases where two devices changed the same record while offline) are flagged for manual review — the system never silently overwrites your data.

The result: a table full of guests never knows the Wi-Fi dropped.

---

## Security and Access Control

Ristofy is built so that people can only do what their job requires.

- **Waiters** cannot access billing or change the menu.
- **Cashiers** cannot edit orders after they are sent to the kitchen.
- **Kitchen staff** see only the ticket board — nothing else.
- **Every action is logged** — who did what, on which record, at what time.
- **Tokens expire** — sessions time out automatically. Leaving a terminal unattended does not leave the system open.
- **PIN login** — fast login for staff who work a single station (kitchen, cashier). PIN accounts lock after repeated failed attempts to prevent guessing.
- **Passwords are never stored plain.** Tokens are stored in the device's secure credential vault.

---

## Why Ristofy Is Different

### Built around real workflows, not generic POS logic
Most POS systems were built to sell retail and adapted for restaurants. Ristofy was designed from day one around how a restaurant actually works: courses, kitchen tickets, table sessions, fiscal compliance, waitlists, loyalty.

### Every role has a purpose-built interface
The waiter's screen looks nothing like the cashier's screen. The kitchen board is a full-screen ticket display, not a form. Each role has exactly the controls they need, and nothing that would confuse or slow them down.

### Multi-branch from the start
Many platforms offer multi-branch as an expensive add-on. In Ristofy, every account is multi-tenant by design. Adding a second location means creating a branch — not buying another product.

### Offline-first reliability
Ristofy does not crash when the router restarts. It queues, syncs, and recovers. This is not optional — it is the baseline.

### Full fiscal compliance built in
Italian fiscal law requires a specific receipt lifecycle: numbered receipts, z-reports, refund tracing, and bridge acknowledgement. This is not a plugin. It is core to the billing module.

### One platform, all the data
Reports, inventory, orders, billing, and fiscal are all in the same system. There is no export-to-Excel, no manual reconciliation between the POS and the accounts spreadsheet. The data is already in one place.

---

## Technical Specifications

| Attribute | Detail |
|---|---|
| **Platform** | Windows 10+ and macOS 12+ desktop application |
| **Connectivity** | Online with offline fallback (queue-and-sync) |
| **Data sync** | Delta-based cursor sync with conflict resolution |
| **Security** | JWT authentication, secure token vault, role-based guards |
| **Fiscal** | Italian fiscal printer integration via fiscal bridge |
| **API** | RESTful JSON API with OpenAPI documentation |
| **Database** | PostgreSQL (server-side), SQLite (local device cache) |
| **Deployment** | Cloud-hosted, managed by Ristofy — no on-premise server needed |
| **Health monitoring** | Live uptime and database health endpoints |

---

## Implementation and Onboarding

Getting started with Ristofy takes less than a day.

**Step 1 — Account setup (30 minutes)**
Your account, branch, and menu are configured. Existing menus can be imported via the API or entered through the management interface.

**Step 2 — Staff setup (30 minutes)**
Create accounts for each staff member and assign their role. They receive their login credentials and can log in immediately.

**Step 3 — Floor plan (30 minutes)**
Enter your tables — number, code, and seat count. Assign them to your floor plan. The live floor screen is ready.

**Step 4 — Device registration (automatic)**
Each device registers itself on first login. No manual IT configuration is required.

**Step 5 — Training (half a day)**
The waiter interface is designed to be learned in under an hour. The cashier and kitchen interfaces are even simpler. A manager walkthrough covers reports, inventory, and end-of-day procedures.

**Step 6 — Go live**
Run a soft opening with Ristofy alongside your existing system if preferred. Most teams switch fully after the first service.

---

## Support and Continuity

- **Runbook included** — documented procedures for every on-call scenario: elevated errors, slow response, fiscal failures, stock anomalies, device issues.
- **Health probes** — the system monitors itself and can alert on any degradation before it affects service.
- **API documentation** — the full API is documented in Swagger/OpenAPI format for any integration needs.
- **Zero-downtime deployments** — updates are deployed with rolling strategy. No maintenance windows during service hours.

---

## Summary

Ristofy is the operating system for your restaurant. It connects every role, every station, and every workflow from the moment a guest arrives to the moment the fiscal day closes. It runs offline. It handles fiscal compliance. It tells you at the end of every day exactly what happened.

Restaurants that use Ristofy spend less time managing the system and more time running the restaurant.

---

*For licensing, onboarding, or technical integration enquiries, contact the Ristofy team.*

*Version: Phase 1 — MVP Operations | Last updated: 2026-04-11*
