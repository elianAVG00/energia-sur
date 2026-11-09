# Design: CU07 recorded consumption vs bill

## Context

- CU05 `es_meter_readings`: `recorded_at` is a UTC timestamp with seconds, `value_kwh`
  is a nonnegative integer decimal string, and each reading is unique per meter and
  instant. Ownership is derived from the meter's account.
- CU06 `es_electricity_bills`: `period_start`/`period_end` are inclusive calendar
  dates without timezone, and `value_kwh` has at most three decimal places.
- Both records already exist; no new table is needed. U14 replaces the earlier
  exact-boundary rule (Q13) with a bounded +/-7-day window.

## Goals / Non-Goals

**Goals:** a simple read-only comparison, deterministic matching, explicit
confirmation for approximate periods, exact decimal arithmetic and no storage.

**Non-Goals:** no OCR, PDF extraction, bill authenticity, tariff, fraud or percentage;
no interpolation, proration or estimation; no new tables, migrations or file changes;
no automatic association beyond `meter_id` and account ownership.

## Decisions

### Matching window (U14)

A reading's comparison date is its **Buenos Aires local calendar date**:
`recorded_at.astimezone(America/Argentina/Buenos_Aires).date()`.

For the start boundary, candidates satisfy
`period_start - 7 days <= local_date <= period_start + 7 days` inclusive. The end
boundary uses `period_end` identically. A pair is **exact** iff
`start.local_date == period_start` and `end.local_date == period_end`; any other
in-window pair is **approximate**.

The tolerance only widens which readings may be selected. It never scales values:
recorded consumption is always `end.value_kwh - start.value_kwh`, with no
interpolation, proration or estimation. An 8-day difference is outside the window.

### Candidate and comparison contract

Both routes are read-only, authenticated and `Cache-Control: no-store`. Ownership is
validated through the meter's account; foreign, missing or mismatched resources
return the same 404.

1. `GET /meters/{meter_id}/bills/{bill_id}/comparison-candidates`
   - 200 `{bill_id, meter_id, period_start, period_end, billed_kwh,
     start_candidates: [...], end_candidates: [...]}`.
   - Each candidate is `{reading_id, recorded_at, local_date, value_kwh, version}`,
     ordered by `local_date`, then `recorded_at`.
   - `start_candidates` and `end_candidates` come from their own +/-7-day windows and
     may overlap for short periods; the same reading cannot be selected for both, so a
     same-day bill needs two distinct readings and a single reading yields no
     comparison.
   - Empty arrays are a normal 200 and mean no compatible reading for that boundary.

2. `GET /meters/{meter_id}/bills/{bill_id}/comparison`
   - Query: required `start_reading_id`, `end_reading_id`; optional
     `confirm_approximate` (boolean, default false).
   - The backend re-reads both readings and validates: ownership of the bill's meter
     and account, distinct reading IDs, and each `local_date` inside its boundary
     window. It also rejects a selection whose start local date is after the end local
     date. Invalid selection returns 422; foreign or missing resources return 404.
     No result is produced for an invalid request.
   - If the pair is not exact and `confirm_approximate` is not true, return 409
     `{detail, code: "CONFIRMATION_REQUIRED", period_start, period_end,
     start_local_date, end_local_date, start_candidates, end_candidates}` with no
     result. The confirmation is a validated backend input, not a modal-only guard.
   - If `end.value_kwh < start.value_kwh`, return 200
     `{status: "no_comparison", reason: "decreasing_reading", ...}` with no
     consumption or difference.
   - Otherwise return 200:
     `{bill_id, meter_id, period_start, period_end, billed_kwh,
     status: "comparable", exact, start_reading: {...}, end_reading: {...},
     recorded_kwh, difference_kwh, outcome}` where
     `outcome` is `recorded_higher`, `billed_higher` or `equal`.
   - `difference_kwh = |recorded_kwh - billed_kwh|` exact. There is no percentage
     field and no mutation.

### Arithmetic and formatting (U14, Q14)

Compute with `Decimal` or arbitrary-precision integers; never float. Reading values
are nonnegative integers; billed kWh may have up to three decimals. `recorded_kwh`,
`billed_kwh` and `difference_kwh` are canonical decimal strings with trailing
fractional zeros trimmed. Recorded consumption 0 (two distinct readings with equal
value) is valid. No percentage and no warning threshold are produced.

### No-comparison outcomes

The comparison result reports `status: "no_comparison"` with
`reason: "decreasing_reading"` when the selected end value is lower than the start
value. The absence of candidates is reported by the candidates route (empty array);
the interface then shows a neutral no-comparison message and does not request a
comparison. Messages never assert that the bill is wrong.

### Frontend

Add a "Comparar" action per bill in `BillHistory`. Fetch candidates first:

- exactly one candidate in each window and it lies on the boundary date -> direct
  comparison, no modal;
- a single non-exact candidate per window -> modal with the real dates, a visible
  warning and an explicit confirmation checkbox;
- more than one candidate in either window -> modal requiring manual selection of the
  start and end reading, plus confirmation when the selection is non-exact;
- empty window -> neutral "no comparison" message.

The result shows both real local dates, recorded consumption, billed kWh, the exact
difference and the direction, and warns when `exact` is false. Reuse existing
`Card`/`Alert`/`Button` components and the existing request-scope pattern.

### Security

The existing opaque session and owner-only checks apply. Both comparison routes are
reads (`Auth`) with `Cache-Control: no-store`; authenticated writes are not involved.
Foreign or missing meter, bill or reading IDs return indistinguishable 404 responses.
No provider keys, storage paths or private files are exposed.

## Risks / Trade-offs

- [Timezone edge] Local-date derivation depends on the Buenos Aires zone; always
  convert the stored UTC instant consistently.
- [Ambiguous candidates] Manual selection avoids guessing; the backend re-validates
  every submitted ID and window.
- [Approximate misuse] A visible warning plus a backend-validated confirmation flag
  prevents a silent approximate comparison.
- [No percentage] Explicitly excluded by Q14; adding it later would need new approval.

## Migration Plan

None: no schema or data changes. Deploy code only after separate Apply authorization.

## Open Questions

The exact Spanish wording of warnings and no-comparison messages, and cosmetic
presentation, remain Q14 presentation details. They do not change matching or
arithmetic and do not block structural validation.
