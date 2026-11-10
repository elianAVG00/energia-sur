# Tasks

## 1. Backend domain calculation

- [x] 1.1 Add `app/consumption.py` with `Decimal` interval/estimate primitives (real-UTC elapsed days, per-call `localcontext` precision, canonical exact formatting, decreasing/zero handling) and verify it imports and its pure helpers pass the new unit tests in 4.1
- [x] 1.2 Implement the estimation base as the last chronological interval only (two most recent readings by `recorded_at` UTC, current values) with no fallback to older intervals, and verify a unit test covers a decreasing latest interval returning no estimate
- [x] 1.3 Guard the elapsed-days divisor and verify a unit test documents that two distinct readings always have distinct `recorded_at` (no division by zero)

## 2. Backend read-only transport

- [x] 2.1 Add a read-only `app/consumption_api.py` router with `GET /meters/{meter_id}/consumption-evolution` and `GET /meters/{meter_id}/consumption-estimate`, `Auth`-only and ownership-checked, and register it in the app; verify endpoints return 404 for a foreign/missing meter
- [x] 2.2 Validate the `days` 1..90 selector and optional inclusive `from`/`to` filters (whole-interval overlap, no clipping) in the endpoint and verify out-of-range `days` returns 422 without an estimate

## 3. Frontend feature

- [x] 3.1 Add a `consumption` feature folder with the two-view presentation (real consumption kWh and daily average kWh/day) and a visible historical-versus-estimated distinction; verify the rendered views match the spec scenarios in 4.3
- [x] 3.2 Add the owned-meter selector, the 1..90 day estimate selector, the two-decimal display with the "orientativa, no facturada" warning, and the "< 0.01" and sub-24-hour "poco representativo" indicators; verify each renders
- [x] 3.3 Evaluate Recharts against React 19 / TypeScript 7 / Vite 8 (install --save-exact dry-run + typecheck); record the outcome and, on conflict, implement the documented fallback visualization without a new dependency — Recharts 2.x caps peer React at 18 and TS 7 / d3 types are unverified, so the dependency-free SVG/CSS fallback was used; no new dependency was added.

## 4. Tests

- [x] 4.1 Add backend unit tests for interval evolution, elapsed-time daily averages (irregular and same-day), deterministic estimate, decreasing/zero handling, the decreasing-latest no-estimate rule and insufficient-base outcome; verify `uv run pytest` passes
- [x] 4.2 Add backend API tests for ownership isolation (foreign/missing 404), `days` validation, inclusive date-range filtering and CU05-only sourcing; verify they pass with the rest of the suite
- [x] 4.3 Add frontend tests for the two views, estimate warning, "< 0.01" and "poco representativo" indicators, filter behavior and decreasing/empty states; verify `npm test` passes

## 5. Verification gates

- [x] 5.1 Run backend Ruff and mypy over the new modules and verify zero new warnings/errors
- [x] 5.2 Run the backend test suite on an isolated PostgreSQL and verify PASS, then run frontend `npm run lint`, `npm run typecheck` and `npm run build` and verify PASS — CU08 domain/adapter/PostgreSQL tests (12 + 6 + 19) all PASS; the full 316-test suite additionally surfaces 8 pre-existing CU05/CU06 environmental failures (missing `CU06_BILL_DIR` bills volume and cgroup-v2 OCR runtime safeguards in the ad-hoc checks-image run), unrelated to CU08. Frontend 93 tests, Oxlint, TypeScript and production build PASS.
- [x] 5.3 Run `openspec validate --strict` for this change and verify PASS with no delta/spec warnings

## 6. Review and acceptance

- [x] 6.1 Confirm the R01–R07 rules are recorded in `docs/use-cases/decisions.md` and traced in the specs/design, and that no residual functional TBD remains except the chart library (D11)
- [x] 6.2 Record a focused independent review of the calculation correctness, ownership isolation, date-filter and chart-library choice, and verify any findings are corrected; record PASS/FAIL/BLOCKED with evidence — independent reviewer returned READY (no CRITICAL/MAJOR); five MINOR findings (estimate-panel `< 0.01` gap, timestamp-parse asymmetry, bar-width overflow, local-time display nuance, flag serialization coverage) were corrected or recorded.

## Workflow follow-up

- Apply is authorized by a subsequent explicit user request; PROPOSE ends at human approval.
- Sync and Archive are performed only after the required verification gates pass and are authorized; update the engineering record under `docs/ai-engineering/` at that point.
