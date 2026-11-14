# Tasks: isolate CU05 reading history by selected meter

APPLY + VERIFY are complete and user-approved. SYNC/ARCHIVE were authorized on 2026-11-13 and completed on 2026-11-13, after the base CU05 change `record-cu05-meter-readings` was synced and archived first (see section 6). No commit or push was performed. The archived `stabilize-cu05-cu06-backend-test-runtime` change and `.vscode/settings.json` remain untouched.

## 1. Reproduction and diagnosis

- [x] 1.1 Reproduce the existing `frontend/e2e/cu05-history.spec.ts` failure before changing code; record the failing assertion and the stale element.
- [x] 1.2 Identify which DOM element and state keep the previous reading visible; verify the component lifecycle and request-scope behavior.
- [x] 1.3 Confirm the root cause with reproducible evidence and document rejected hypotheses (`active()`, late responses, row clearing) in `design.md`.

## 2. Implementation

- [x] 2.1 Assign distinct React keys to the CU05, CU06 and CU07/CU08 meter-scoped sibling panels and share one selected-meter guard, so a meter change removes the previous instance.
- [x] 2.2 Verify the same reproduction scenario passes after the minimal fix, without backend, API, model, dependency or numeric-contract changes.

## 3. Focused tests

- [x] 3.1 Cover switching between meters with different histories, including the exact kWh value and absence of the previous meter's data.
- [x] 3.2 Cover switching to a meter with no readings and its empty state.
- [x] 3.3 Cover a pending previous-meter request: cancellation evidence, no stale rows while the new history loads, and a deterministic out-of-order release.
- [x] 3.4 Cover rapid changes between meters with gated, overlapping responses.
- [x] 3.5 Cover an HTTP error for the newly selected meter without resurrection of previous data.
- [x] 3.6 Cover photo, open edit form, bill draft, comparison and estimate reset on meter change; fail on any React duplicate-key warning.

## 4. Verification gates

- [x] 4.1 Focused CU05 Chromium tests PASS: `e2e/cu05-history.spec.ts` 9/9 after the fix; the five isolation scenarios fail with the key fix temporarily reverted.
- [x] 4.2 Mocked cross-CU regression PASS: bill draft (CU06), comparison (CU07) and consumption estimate (CU08) are isolated by the same test suite; no stale CU05 data remains.
- [x] 4.2b CU04/CU06/CU07/CU08 seeded real Chromium specs DEFERRED by explicit user authorization (2026-11-13) to the integral regression stage. Not executed and NOT PASS. BLOCKED reason: external synthetic QA credentials and seeded state unavailable. Residual risk tracked as **QA-INT-CU04-08** in `docs/STATE.md` and the engineering record.
- [x] 4.3 Frontend typecheck, 142 node tests, lint and build PASS.
- [x] 4.4 `openspec validate --all --strict` PASS (16/16).
- [x] 4.5 Independent `reviewer` audit completed (no blockers). Documentation overclaims, regression matrix, race-test determinism and panel-flow coverage were corrected; affected checks re-ran PASS.

## 5. Documentation and closure recommendation

- [x] 5.1 Update `docs/STATE.md`, the engineering record and the README evidence index with the correction cycle and redacted evidence.
- [x] 5.2 Reconcile task status and recommend closure. APPLY + VERIFY are accepted; SYNC/ARCHIVE were authorized but not executed at this checkpoint because of the integrity blocker in 6.2 (completed later on 2026-11-13 under 6.3). No commit or push.

## 6. Sync and archive

- [x] 6.1 Audit CU05 capability integrity: the only existing CU05 delta was the then-active `record-cu05-meter-readings` change with 18 requirements and 37 scenarios at audit time (38 after the red-fraction resolution); this change adds 3 requirements and 6 scenarios, with no MODIFIED/REMOVED/RENAMED operations.
- [x] 6.2 Probe OpenSpec archive behavior in an isolated copy: archiving this change as a new capability creates `openspec/specs/meter-readings/spec.md` with only the 3 new requirements (`added: 3, modified: 0, removed: 0`). The 18 base requirements remain intact in the blocked CU05 change but would be absent from the main spec.
- [x] 6.3 RESOLVED 2026-11-13: the base CU05 change resolved its red-fraction conflict by explicit human decision, was validated and archived first, creating the canonical `openspec/specs/meter-readings/spec.md` with 18 requirements / 38 scenarios. This change then appended its 3 ADDED requirements and 6 scenarios to that existing spec (21 requirements / 44 scenarios) and was archived. `openspec validate --all --strict` PASS.
