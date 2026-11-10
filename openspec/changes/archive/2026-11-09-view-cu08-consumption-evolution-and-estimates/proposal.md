# Proposal: CU08 consumption evolution and estimates

## Why

Account holders with CU05 meter readings need to see their own consumption evolve interval-by-interval and to obtain a deterministic, non-factured estimate for a chosen number of days. CU08 is the next planned use case after CU07; its eleven functional decisions (D01–D11) and the seven residual decisions (R01–R07) are now confirmed, so this change is ready for human approval before implementation.

## What Changes

- Add a read-only, owner-scoped CU08 query that computes, on the backend and with `Decimal`, the per-interval real consumption (kWh) and daily average (kWh/day) from the meter's CU05 readings, plus a deterministic estimate for a manually chosen 1–90 day horizon. No AI, no historical averages, no new persistence, no new dependencies.
- Use only CU05 readings (D08). Never mix CU06 bills or reuse CU07 comparison rules; CU07's read-only comparison domain is a separate capability and is not modified.
- Compute against real elapsed time between readings in UTC (D03, D05), display in `America/Argentina/Buenos_Aires`, and show decreasing-reading intervals as "not calculable" without blocking the rest of the history (D04). Accept zero-kWh intervals and zero estimates (D06).
- Apply the approved residual rules: CU05-based validity and UTC chronological ordering with current stored values (R01, R03), no estimate on a decreasing latest interval or with fewer than two readings (R02, R07), inclusive-overlap date filtering with visible endpoint dates (R05), and Decimal-precise presentation with sub-day and sub-cent guards (R04, R06).
- Present two distinct views — real consumption and daily average — with a clear visual separation between historical and estimated data (D07), a two-decimal display with an "orientativa, no facturada" warning (D09), and filtering by owned meter and date range with account isolation (D10).
- Evaluate Recharts for the charts (D11); if it conflicts with the current React 19 / TypeScript 7 / Vite 8 stack, propose alternatives and leave the chart library as a TBD for review.

## Capabilities

### New Capabilities

- `consumption-trends`: owner-scoped CU08 reading-derived evolution and deterministic estimation for a meter's CU05 reading history, including decreasing/zero interval handling, elapsed-time daily averages, the 1–90 day estimate, and the historical-versus-estimated presentation rules.

### Modified Capabilities

None. CU04 meter identity, CU05 reading storage/transport, CU06 bills and CU07 comparisons are reused read-only without changing their requirements.

## Impact

Affected code: a new backend domain/transport module (e.g. `app/consumption.py` + a read-only API router) and a new frontend feature under `frontend/src/features/`. No migrations, no new tables, no new persistence. Dependencies: Recharts is evaluated but not installed in this PROPOSE step; any chart-library decision is a review TBD (D11). Tests: backend deterministic-calculation and isolation tests, frontend presentation tests. No CU05/CU06/CU07 endpoint, schema or persistence change is proposed.

See [design](design.md) for confirmed decisions (D01–D11, R01–R07), inferences and the Recharts compatibility assessment.
