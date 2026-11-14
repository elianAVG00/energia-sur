# Design: isolate CU05 reading history by selected meter

## Context

`DomicileManagement.tsx` renders three meter-scoped sibling panels for the selected meter: `ReadingHistory` (CU05), `BillHistory` (CU06) and `ConsumptionPanel` (CU07/CU08). Each was rendered with the same React `key` template `${generation}:${selected}:${readingMeter}`. `ReadingHistory` keeps `rows`, `loading`, `historyReady`, `error`, `photoUrl`, `editing` and retry attempts in local state and loads readings through `useRequestScope`.

Reproduction (mocked Chromium, `frontend/e2e/cu05-history.spec.ts`):

- Select meter `m1`: `GET /api/meters/m1/readings` returns one row `9007199254740993`.
- Select meter `m2`: `GET /api/meters/m2/readings` returns `[]`; `No hay lecturas registradas.` becomes visible.
- The row from `m1` remains visible in the reading-history list.

## Root cause

**Confirmed:** the three panels shared identical React sibling keys. React logged:

```
Encountered two children with the same key, `1:d:m1` ... Non-unique keys may cause children to be duplicated and/or omitted
```

Instrumentation observed that after selecting `m2`, the remaining reading-history list in the DOM belonged to the old instance (`meter=m1`, `rows=1`) while the `m2` instance had also mounted. React's surviving set is not contractually defined under duplicate keys, so the durable conclusion is the warning plus the unsupported reconciliation class, not a specific single subtree state. With distinct keys, React logged the `m1` unmount before the `m2` mount and the same test passed.

React's documented behavior for duplicate sibling keys is unsupported reconciliation ("duplicated and/or omitted"), which explains how the stale subtree survived. No stale response was involved in the reproduced case: the stale row was a reconciliation artifact observable before any late response handler could run.

## Rejected hypotheses

- **`active()` is the cause.** Rejected. `active()` compares session generation and selected domicile, both unchanged by a meter switch, and never claimed to compare meter IDs. Changing `active()` would not repair the duplicated-key reconciliation and would be misleading.
- **A late `m1` response overwrites `m2` state.** Rejected as the reproduced cause. `useRequestScope` is per component instance, is invalidated on unmount, and each lane accepts only its latest request. Instrumentation showed the stale list before any response could have been applied to the `m2` instance. Late responses are still covered by regression tests.
- **Clearing `rows` at the start of `refresh()`.** Rejected as the primary fix: it would mask the symptom in some orderings while React continues to reconcile unsupported duplicate keys; the stale subtree can reappear without any state change.
- **Wrapping the panels in one keyed container.** Larger refactor than required; it changes layout ownership and is unnecessary to restore correct sibling identity.

## Decision

Give each meter-scoped panel a distinct key namespace:

- `readings:${generation}:${selected}:${readingMeter}`
- `bills:${generation}:${selected}:${readingMeter}`
- `consumption:${generation}:${selected}:${readingMeter}`

Uniqueness restores identity per component type while preserving the intended remount on session, domicile or meter change. Because `ReadingHistory` remounts, its local rows, empty state, photo URL, editing state, retry attempts and error are reset; the old instance's request scope is invalidated, so late or out-of-order responses from the previous meter are discarded by both the unmounted instance and the abort/lane guards.

No change is made to `useRequestScope`, `active()`, the reading API client, the backend or the exact kWh representation.

## Numeric contract

`value_kwh` remains an exact decimal string end to end. The switch fix does not parse, coerce, clamp or normalize values, so `9007199254740993` stays exact. No `Number` conversion, `BigInt` or new functional limit is introduced. The existing client guard already rejects readings whose `meter_id` differs from the requested meter.

## Verification evidence

- **Pre-fix red:** original `cu05-history.spec.ts:57` (test at `:24`) failed at the `9007199254740993 kWh` count (`received: 1`). After the tests were strengthened, temporarily restoring the duplicate keys made all five isolation scenarios fail (5 failed / 4 pre-existing passed); the restored fix made 9/9 pass.
- **Post-fix green:** 9/9 mocked Chromium scenarios, including photo/edit reset, pending-request cancellation, deterministic out-of-order release, HTTP error and bill/comparison/estimate reset.
- **Guard:** every mocked scenario fails if React emits the duplicate-sibling-key warning.
- **Static gates:** typecheck, 142 node tests, Oxlint and build PASS; `openspec validate --all --strict` 16/16 PASS.
- **Independent review:** no blockers. Its documentation overclaim, regression-matrix wording, non-deterministic race tests and missing panel-flow coverage were corrected and re-verified.

## Risks / trade-offs

- **Key change affects CU06/CU07/08 panels too.** Required, because the collision involved all three siblings. Their base flows are otherwise unchanged. Mocked checks now cover bill/consumption remount plus bill-draft, comparison and estimate reset; the seeded CU04/CU06/CU07/CU08 Chromium specs remain BLOCKED because the external synthetic QA state and credentials are unavailable.
- **Remount discards in-progress local form state on meter switch.** Intended by the requirement: no editable data from the previous meter may remain visible. The meter selector is the sole control that changes this scope.
- **No new automated unit harness for React components exists.** Focused Chromium tests are the established evidence path for these user-visible flows; pure helper tests cannot express DOM reconciliation.
- **CU05 was unarchived with its red-fraction conflict.** This change does not touch that conflict. The conflict was resolved by explicit human decision and the base change was archived first, so the canonical `meter-readings` spec already existed when this delta was synced.
- **Archive ordering.** `openspec/specs/meter-readings/spec.md` is created by the base CU05 sync (18 requirements / 38 scenarios); this change then appends its 3 ADDED requirements and 6 scenarios to that existing spec, yielding 21 requirements / 44 scenarios. Syncing this change alone would have produced a 3-requirement partial spec, which is why the base change was archived first.

## Migration plan

None. No data, schema, API or deployment change. Rollback is reverting the key names in `DomicileManagement.tsx`.
