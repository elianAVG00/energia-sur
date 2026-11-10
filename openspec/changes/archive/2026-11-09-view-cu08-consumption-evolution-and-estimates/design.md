# Design

## Context

CU08 builds read-only on the already-implemented CU05 reading history. Readings are stored as UTC second-resolution `recorded_at` plus a nonnegative-integer `value_kwh` (`Numeric`/`Decimal`), owner-scoped through the meter's domicile account (CU04/CU09). CU07 already established the read-only "domain module + transport router" pattern (`app/comparison.py` + `app/comparison_api.py`) with a `localcontext`-based `Decimal` arithmetic helper, a `BUENOS_AIRES` zone, and `Auth`-only read endpoints. The frontend has no charting library today: React 19.3.1, TypeScript 7.0.2, Vite 8.3.6, Tailwind 4, Zustand, RHF/Zod, Axios. See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**

- Backend-only deterministic calculation in `Decimal`; the UI only renders and rounds to two decimals.
- A read-only, authenticated, account-isolated query with no new persistence, migrations, tables or dependencies.
- Two views (real consumption kWh, daily average kWh/day) with a clear historical-versus-estimated distinction and the "orientativa, no facturada" warning.

**Non-Goals:**

- No AI, historical-average, tariff, monetary or billing forecast; no CU06/CU07 data reuse; no mutation of any reading/bill/comparison; no chart-library installation in this PROPOSE step; no physical meter replacement handling.

## Decisions

### D01/D02/D03/D06 — Deterministic estimation formula

Estimate = (interval consumption ÷ real elapsed days) × chosen days. Interval consumption is `end - start` in kWh; elapsed days is the real UTC delta in seconds ÷ 86400, so same-day readings yield fractional days. `days` is a validated integer 1..90. Zero consumption intervals and zero estimates are accepted. Rationale: confirmed rule; no inference of linear extrapolation beyond the chosen window, no historical aggregation. Precision: interval consumption is an exact integer difference emitted as a canonical decimal string; the daily average (`consumption ÷ elapsed_days`) and the estimate (`daily_average × days`) are `Decimal` operations computed under a per-call `localcontext()` with `prec = max(28, operand digit counts) + 10` and `MAX_EMAX`/`MIN_EMIN` (mirroring `comparison.compare_values`), carrying enough guard digits that the two-decimal rendering is stable. The divisor is guarded: a zero-duration interval is structurally impossible because CU05 enforces per-meter uniqueness on the exact instant (two distinct readings always differ in `recorded_at`), but the domain still rejects a non-positive divisor defensively.

### R01/R02/R03/R07 — Validity, chronology and the estimation base

The estimation base is exactly the last chronological interval: the two most recent readings of the meter ordered by `recorded_at` UTC. A reading is "valid" by the same rules CU05 already enforces on a confirmed stored reading (nonnegative integer, nonfuture, second-resolution UTC); no additional filter is introduced (R01). Ordering always uses current stored values and times, so edits are reflected (R03). If the last chronological interval is decreasing, no estimate is returned and the system does NOT fall back to older intervals (R02). With zero or one reading the UI shows an empty state and no estimate is offered (R07). Physical meter replacement is out of scope (R03).

### D04/D05 — Decreasing intervals and time handling

Intervals are computed in chronological `recorded_at` order (UTC), displayed in `America/Argentina/Buenos_Aires` (reusing `comparison.local_date`). A decreasing interval is emitted as `calculable=false` with no negative consumption; historical decreasing intervals remain visible as "not calculable", while a decreasing latest interval also suppresses the estimate (R02).

### R04/R06 + D07/D09 — Presentation precision and units

The API returns canonical decimal strings: interval consumption is exact, while the daily average and estimate are computed at the defined `Decimal` precision and rounded only at display. The UI renders to two decimals with half-up rounding (`ROUND_HALF_UP`) and appends the warning "orientativa, no facturada" to the estimate (D09). Units are kept explicit: interval and estimate values are kWh and daily-average values are kWh/day, never merged (D07). A positive value whose two-decimal rendering rounds to "0.00" is shown as "< 0.01" instead, so it is not confused with the real zeros D06 permits; a true zero renders "0.00" (R06). A sub-24-hour interval is still computed but flagged "poco representativo" (not representative) in the UI (R04).

### D08 — Source isolation

A new module `app/consumption.py` reads only `MeterReading` rows for the selected meter. It imports nothing from the bill or comparison domains. No bill data is joined.

### D10 + R05 — Ownership and filtering

Read endpoints use `Auth` (session) and resolve ownership through the meter's account, returning the standard 404 for missing/foreign meters (`own_meter`). The evolution endpoint accepts optional inclusive `from`/`to` date filters interpreted in Buenos Aires; the estimate endpoint accepts `days`. Date filtering uses inclusive overlap (R05): an interval that crosses or touches the selected range is included whole, with its real endpoint dates visible, never clipped, interpolated or prorated.

### D11 — Charting: Recharts evaluation (TBD for review)

Recharts is the candidate library. Assessment against the installed pins:

- React 19: Recharts 3.x targets React 19; older 2.x peer ranges cap at React 18, which would conflict with React 19.3.1.
- TypeScript 7.0.2 is very new; Recharts and its transitive types (d3-* and `victory-vendor` types) have not been validated against TS 7, so a peer/type conflict is plausible.
- The project deliberately pins exact versions and rejects drift (uv.lock / package-lock.json); adding Recharts is a new dependency that would need the same lock and lint gates.

**Decision:** do not install Recharts now. At Apply time, evaluate Recharts 3.x against React 19 / TS 7 / Vite 8 with `npm install --save-exact` dry-run and typecheck; if it conflicts, fall back to (a) a dependency-free SVG/CSS bar+line chart using existing shadcn/radix primitives, or (b) `@nivo/line` + `@nivo/bar` if its React 19/TS 7 peer ranges resolve. This remains a review TBD (D11).

### API contract (sketch)

- `GET /meters/{meter_id}/consumption-evolution?from=<local date>&to=<local date>` → `{ meter_id, intervals: [{ start_reading, end_reading, consumption_kwh, daily_average_kwh_day, calculable, elapsed_hours, below_minimum }] }`, ordered chronologically. `elapsed_hours < 24` drives the "poco representativo" flag; `below_minimum` marks a positive value whose two-decimal rendering is "0.00". `from`/`to` are inclusive Buenos Aires calendar dates; `from > to` returns 422.
- `GET /meters/{meter_id}/consumption-estimate?days=<1..90>` → either `{ meter_id, days, daily_average_kwh_day, estimate_kwh, orientative: true, below_minimum, base_start_reading, base_end_reading }` or `{ meter_id, status: "base_unavailable", reason: "insufficient_readings" | "decreasing_latest" }` when there are fewer than two readings or the last interval is decreasing.

Interval inclusion is inclusive-overlap (R05): an interval is included whole when its start local date ≤ `to` and its end local date ≥ `from`, with both real endpoint dates returned; no clipping, interpolation or proration. Both endpoints are `Auth`-only GETs (no CSRF/Origin, no mutation), consistent with CU07's read-only comparison endpoints.

## Risks / Trade-offs

- [Recharts peer/type conflict with React 19 / TS 7 / Vite 8] → do not install in PROPOSE; resolve at Apply via dry-run + typecheck, with documented fallbacks (D11).
- [Sub-24-hour interval daily averages inflate the estimate] → keep the formula deterministic and flag the interval "poco representativo" (R04).
- [Date-corrected readings change intervals already seen] → CU08 reads current stored values in `recorded_at` order; no snapshotting (R03).
- [Rounding a tiny nonzero value to "0.00" misleads users] → "< 0.01" indicator at the display boundary (R06).
- [Decreasing latest interval] → no estimate and no fallback to older intervals (R02).
- [Division by zero] → structurally prevented by CU05's per-meter exact-instant uniqueness (two distinct readings differ in `recorded_at`); the domain still guards a non-positive divisor defensively.

## Migration Plan

None. CU08 adds a read-only endpoint and UI only; no schema, migration, data mutation, or dependency change is proposed. Rollback is removing the router registration and feature mount.

## Open Questions

Only the chart library remains unresolved (D11); it is deliberately deferred to Apply and does not change the specs, the approach, or the task breakdown. R01–R07 are approved and incorporated above.
