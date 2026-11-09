# Tasks

## 1. Review and contract gates

- [x] 1.1 Obtain explicit human Review of the proposal, delta and design, including the +/-7-day inclusive window, exact-versus-approximate behavior, candidate/confirmation contract, no-percentage and read-only scope. Record approval and resolve blockers. (The user approved the three refinements and authorized BUILD on 2026-11-09.)
- [x] 1.2 Obtain a separate explicit Apply request before functional implementation. (Same 2026-11-09 instruction authorized BUILD.)

## 2. Backend comparison

- [x] 2.1 Implement a pure domain module: Buenos Aires local-date derivation, per-boundary +/-7-day filtering, exactness detection, exact decimal consumption/difference, outcome and no-comparison reasons, including the decreasing-reading guard.
- [x] 2.2 Implement `GET /meters/{meter_id}/bills/{bill_id}/comparison-candidates` with owner-only access and a bounded window scan; return ordered candidates and empty arrays without error.
- [x] 2.3 Implement `GET /meters/{meter_id}/bills/{bill_id}/comparison` validating ownership, distinct reading IDs, window membership, date order and backend confirmation; return `CONFIRMATION_REQUIRED`, `no_comparison` or the exact result per the design.
- [x] 2.4 Add tests for exact match, 7-day acceptance, 8-day rejection, multiple candidates, missing and confirmed confirmation, zero consumption, decreasing readings and cross-account isolation. (`tests/test_comparison.py`, `tests/test_comparison_api.py` and `tests/test_comparison_postgres.py`; the full suite passed.)

## 3. Frontend

- [x] 3.1 Add a comparison client and runtime-validated types using the existing HTTP helper, including the structured `CONFIRMATION_REQUIRED` warning.
- [x] 3.2 Add the "Comparar" action, candidate modal/selection, real-date warning and explicit confirmation, plus comparable and no-comparison rendering in the bill workspace.
- [x] 3.3 Add tests for direct exact comparison, approximate confirmation, manual multi-candidate selection, zero consumption, decreasing readings and no candidates. (`tests/comparison-api.test.ts`; 80 frontend tests passed.)

## 4. Verification and evidence

- [x] 4.1 Run OpenSpec strict validation, backend tests/Ruff/mypy and frontend tests/lint/build; record PASS/FAIL/BLOCKED/NOT APPLICABLE with evidence. (PASS: 275 backend tests with 2 opt-in skips, Ruff and mypy (30 modules), 80 frontend tests, Oxlint, TypeScript, build and OpenSpec strict 10/10.)
- [x] 4.2 Run a synthetic end-to-end browser flow with two accounts exercising exact, approximate-confirmed and no-comparison outcomes. (PASS: 4/4 Chromium scenarios covering exact, multiple candidates, approximate confirmation, zero, decreasing and cross-account isolation.)
- [x] 4.3 Obtain an independent review of ownership, validation and regressions; resolve concrete findings before closure. (Focused `reviewer` session `ses_e3d6e939dffe7rvvDOAVkDrrgK`; the MAJOR Decimal-precision defect and the confirmed MINOR edges were corrected and re-verified. The inline confirmation panel is recorded as Q14 presentation latitude.)
- [x] 4.4 Update `docs/STATE.md`, README and the CU07 engineering record with actual commands and outcomes; verify links and no sensitive data. (STATE updated; engineering record added.)

## Workflow follow-up

Sync and archive only after all required gates pass and a separate explicit authorization.
