# isolate-cu05-reading-history-by-meter

Status: APPLY + VERIFY complete and accepted; SYNC + ARCHIVE completed 2026-11-13 after the base CU05 change was archived first. No commit or push.

## Goal and specification

Fix the CU05 defect where changing the selected meter in the CU04 management view left the previous meter's reading visible.

- Change: [proposal](../../openspec/changes/archive/2026-11-13-isolate-cu05-reading-history-by-meter/proposal.md) · [design](../../openspec/changes/archive/2026-11-13-isolate-cu05-reading-history-by-meter/design.md) · [tasks](../../openspec/changes/archive/2026-11-13-isolate-cu05-reading-history-by-meter/tasks.md) · [spec delta](../../openspec/changes/archive/2026-11-13-isolate-cu05-reading-history-by-meter/specs/meter-readings/spec.md)
- Base CU05 capability: [archived record-cu05-meter-readings](../../openspec/changes/archive/2026-11-13-record-cu05-meter-readings/proposal.md) and [canonical meter-readings spec](../../openspec/specs/meter-readings/spec.md).
- Prior evidence: [stabilize-cu05-cu06-backend-test-runtime](stabilize-cu05-cu06-backend-test-runtime.md).

## Approval and scope

The user authorized BUILD/APPLY for this change in the 2026-11-13 stabilization request and ordered a stop after APPLY + VERIFY, before SYNC, ARCHIVE, commit or push. Scope was limited to reading-history isolation; backend, PostgreSQL, models, API contracts, dependencies and the exact kWh representation were excluded. `.vscode/settings.json`, the archived runtime-stabilization change and the CU05 red-fraction documentation conflict were not modified.

On 2026-11-13 the user accepted the functional result, authorized SYNC/ARCHIVE and authorized deferring the seeded CU04/CU06/CU07/CU08 regression to the integral project stage. The deferral is not a PASS.

## Reproduction and correction cycle

**1. Failure reproduced (pre-fix).** `frontend/e2e/cu05-history.spec.ts:57` (test at `:24`) failed:

```
Locator:  getByText(/9007199254740993 kWh/)
Expected: 0
Received: 1
```

The mocked flow selected `m1` (one reading), then `m2` (empty list). `No hay lecturas registradas.` appeared, but the `m1` row stayed in the reading-history `<ul>`.

**2. Investigation.** DOM ancestry confirmed the stale `<span>` was inside the CU05 history list. Temporary instrumentation of `ReadingHistory` showed:

- After selecting `m2`, the remaining history list still carried `meter=m1` and one row while the `m2` instance mounted.
- React logged: `Encountered two children with the same key ... 1:d:m1` and later `1:d:m2`.

**3. Root cause.** `DomicileManagement.tsx` rendered `ReadingHistory`, `BillHistory` and `ConsumptionPanel` as siblings with the same key template `${generation}:${selected}:${readingMeter}`. Duplicate sibling keys make React reconciliation unsupported, and the surviving subtree is not defined; the old `m1` history subtree remained visible. `active()` was not the cause: it checks generation and selected domicile, neither of which changes on a meter switch, and the session store does not hold the reading-meter selection. Late responses were also not the reproduced cause; request scopes are per instance and invalidate on unmount.

**4. Correction.** Distinct key namespaces (`readings:`, `bills:`, `consumption:`) plus a single `selectedMeter` guard. `ReadingHistory` received a comment documenting that instance identity is guaranteed by the parent key. No state, API or numeric logic changed.

**5. Red → green proof.** Temporarily restoring only the duplicate keys made 5 isolation tests fail and the 4 pre-existing tests pass. Restoring the fix made the complete suite pass:

```
fixed:        9 passed
duplicate keys: 5 failed, 4 passed
```

## Tests and evidence

`frontend/e2e/cu05-history.spec.ts` (9/9 PASS unless noted):

1. Meter switch with different histories, empty target meter, photo and open edit reset, exact `9007199254740993` kWh.
2. Pending previous-meter refresh: cancelled request evidence, no stale row during the new meter's load.
3. Rapid switching with gated overlapping responses; exact value after switching back.
4. HTTP 503 for the new meter: error shown, previous row and edit action absent.
5. Bill (CU06), comparison (CU07) and consumption estimate (CU08) reset on meter switch.
6. A per-test guard fails on any React duplicate-sibling-key warning.

Static gates: typecheck PASS, 142/142 node tests PASS, Oxlint 0 warnings/errors, build PASS, `openspec validate --all --strict` 16/16 PASS.

Environment: Windows host, Docker Desktop; Playwright Chromium 1.65.0 from `energia-sur-frontend-checks:cu10`, Vite dev server in an isolated container on port 5273 with the working tree mounted. No shared database or volume was reset.

BLOCKED and DEFERRED: seeded CU04/CU06/CU07/CU08 real Chromium specs require external synthetic QA credentials and state (`QA_USERNAME_A`, `QA_PASSWORD`, `CU07_STATE`, `CU08_STATE`), unavailable in this session. The user authorized deferral to the integral regression stage on 2026-11-13. They were not executed and are not PASS; their mocked UI surface is covered by scenario 5 plus static review. Residual risk is tracked as **QA-INT-CU04-08** below and in `docs/STATE.md`.

## Independent review

Reviewer session `ses_e28717683ffe4JVgTm9XghhIrg`: no blockers; root cause and fix accepted. Findings corrected:

- Documentation overclaimed CU04–CU08 mocked regressions; corrected to the real matrix with seeded specs BLOCKED.
- Race tests were non-deterministic; replaced with gated overlapping responses and abort evidence.
- Photo/edit reset and bill/comparison/estimate flows were untested; added.
- Duplicate-key warning had no guard; added to every test.
- Spec wording described an implementation detail; rewritten as observable behavior.
- Archive ordering noted: `meter-readings` is not yet in main specs; verify the generated spec before SYNC/ARCHIVE.

## Deferred QA regression (QA-INT-CU04-08)

- **Scope:** seeded real Chromium specs for CU04 (domicile/meter selection), CU06 (bill history and files), CU07 (registered-vs-billed comparison) and CU08 (evolution and estimate).
- **State:** NOT EXECUTED / BLOCKED. Required synthetic QA accounts and state files were unavailable.
- **Authorization:** the user explicitly deferred these checks to the project's integral regression stage on 2026-11-13. The mocked cross-CU checks in `cu05-history.spec.ts` are not a substitute.
- **Residual risk:** the unique-key change also remounts `BillHistory` and `ConsumptionPanel`; their mocked reset paths pass, but their full authenticated flows have not been re-exercised in a browser against a seeded backend.
- **Acceptance for closure of this pending:** run the seeded CU04/CU06/CU07/CU08 Chromium suites with provisioned synthetic QA credentials/state, record PASS/FAIL per suite, and investigate any regression against the meter-scoped remount behavior.
- **Tracking:** this section and the `QA-INT-CU04-08` entry in `docs/STATE.md`.

## CU05 specification integrity audit (2026-11-13, pre-resolution snapshot)

- **No archived CU05 capability spec or delta existed at audit time.** Git history showed the CU05 implementation/delta introduced in `ca30794`; there was no `openspec/changes/archive/*cu05*` entry and no `openspec/specs/meter-readings/`.
- **Why `meter-readings` was absent from main specs:** the base change `record-cu05-meter-readings` was still active (14/15 tasks). Its task 4.1 (red-fraction contract conflict) was open, and its design stated: "Do not sync or archive until the user resolves that contract conflict."
- **Existing requirements:** the base CU05 delta had **18 requirements and 37 scenarios**. This change's delta has **3 requirements and 6 scenarios**, all under `## ADDED Requirements`; it has no MODIFIED, REMOVED or RENAMED operations.
- **Expected merge:** 18 + 3 = **21 requirements** and 43 scenarios, if the base requirements were carried into the main spec. The final count is 44 because the red-fraction resolution added one scenario ("Indistinguishable fractional digit") to the base capability.
- **Archive probe (isolated copy, no repository change):** `openspec archive` on this change alone created `openspec/specs/meter-readings/spec.md` with only the 3 new requirements (`added: 3, modified: 0, removed: 0`). The 18 base requirements remained intact in the active CU05 change but were absent from the main spec.
- **Second probe:** seeding the main spec with the 18 base requirements and then archiving produced 21 requirements and passed `openspec validate --all --strict`; however, this promoted the CU05 delta before its red-fraction conflict was resolved, which the CU05 design and task 4.1 explicitly forbade at that time.
- **Decision at audit time:** SYNC/ARCHIVE were not executed. The change remained active because no available path both (a) preserved all base requirements in the resulting main spec and (b) respected the CU05 no-sync gate. No CU05 requirement, scenario or rule was modified.
- **Resolution (later on 2026-11-13):** the user approved the red-fraction contract resolution; the base change was synced and archived first, and this change then synced and archived normally. See "SYNC / ARCHIVE status" below.

## SYNC / ARCHIVE status

**COMPLETED 2026-11-13.** Sequence: the base CU05 change resolved its red-fraction conflict by explicit human decision and was synced, creating `openspec/specs/meter-readings/spec.md` with 18 requirements / 38 scenarios; it was then archived. This change appended its 3 ADDED requirements and 6 scenarios to that existing capability spec and was archived as `2026-11-13-isolate-cu05-reading-history-by-meter`. Final capability: 21 requirements / 44 scenarios, no MODIFIED/REMOVED/RENAMED operation, no duplicated or contradictory requirement.

Verification: the base delta requirements are present byte-for-byte in the main spec (line comparison after the title/requirements-header transformation), the 3 new requirements follow them, no delta operation headers remain, the existing Purpose and title were preserved, and `openspec validate --all --strict` PASS. The authorized deferral **QA-INT-CU04-08** was preserved and is still not PASS. No commit or push was performed.

Independent reviews (2026-11-13): `spec-analyst` and `reviewer` both audited the archived result. Neither raised a BLOCKER or MAJOR finding against this change; the reviewer confirmed the 3 requirements / 6 appended scenarios, the absence of duplicated or contradictory requirements, and that QA-INT-CU04-08 remains NOT PASS. Documentation corrections from the reviews touched only the base CU05 contract wording, `docs/STATE.md` length and stale task notes; this change's delta was not modified. See the [base engineering record](record-cu05-meter-readings.md#independent-reviews-and-corrections-2026-11-13).
