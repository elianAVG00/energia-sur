# Proposal: isolate CU05 reading history by selected meter

## Why

CU05 was implemented but blocked from full closure by the red-fraction contract conflict. During stabilization, the mocked Chromium regression `frontend/e2e/cu05-history.spec.ts` reproduced a functional defect: after the owner selects a second meter, the reading history still shows a reading that belongs to the previously selected meter. The previous change `stabilize-cu05-cu06-backend-test-runtime` confirmed the behavior but deliberately did not diagnose its internal cause.

The defect is a frontend presentation-state bug. It does not involve backend logic, PostgreSQL, API contracts or the approved exact decimal-string kWh representation.

## What Changes

- Correct the CU04 management view so that the three meter-scoped panels (CU05 readings, CU06 bills, CU07/CU08 consumption) receive distinct React keys instead of the same sibling key.
- Guarantee that a meter selection change removes the previous meter's visible state, so no previous reading, photo, editable value, bill draft, comparison, estimate or error remains visible, and an empty history shows its empty state.
- Add focused Chromium regressions for: different histories, empty target meter, photo and open-edit reset, pending-request cancellation, deterministic out-of-order responses, rapid switching, HTTP errors, bill/comparison/estimate reset and exact preservation of `9007199254740993` kWh. The suite also fails if React reports duplicate sibling keys.
- Preserve CU04–CU08 behavior and the existing API/backend contracts. No backend, database, migration, model or dependency change.

## Capabilities

### New Capabilities

- `meter-readings`: follow-up ADDED requirements that the visible reading history is isolated to the selected meter across selection changes, pending/late responses, errors and rapid switching. The capability base is the canonical `openspec/specs/meter-readings/spec.md`, created when `record-cu05-meter-readings` was synced and archived on 2026-11-13. This change does not alter any existing CU05 requirement.

### Modified Capabilities

None.

## Impact

- Affected code: `frontend/src/features/domiciles/DomicileManagement.tsx` (unique sibling keys and a shared selected-meter guard), `frontend/src/features/readings/ReadingHistory.tsx` (identity clarification comment only), `frontend/e2e/cu05-history.spec.ts` (focused regressions and duplicate-key guard).
- No API, backend, database, storage or dependency impact.
- Approval: the user explicitly authorized BUILD/APPLY for this change in the current request and ordered a stop after APPLY + VERIFY, before SYNC, ARCHIVE, commit or push.
- Archive ordering: on 2026-11-13 the base CU05 change was synced and archived first, then this change appended its 3 requirements to the existing canonical spec. Verified: `meter-readings` now has 21 requirements / 44 scenarios, and both changes are archived.
- Untouched: `.vscode/settings.json`, the archived `stabilize-cu05-cu06-backend-test-runtime` change and its evidence, and the separate pending CU05 red-fraction documentation conflict.
