# CU07 comparison engineering record

## Goal and authority

Implement a read-only comparison between a CU06 bill and CU05 readings of the same
owned meter, using the U14 +/-7-day Buenos Aires window, exact-versus-approximate
behavior, manual candidate selection and backend-validated confirmation. See
[U14](../use-cases/decisions.md#u14---cu07-revised-matching-and-comparison-authorization),
[archived proposal](../../openspec/changes/archive/2026-11-09-compare-cu07-consumption-with-bill/proposal.md),
[design](../../openspec/changes/archive/2026-11-09-compare-cu07-consumption-with-bill/design.md),
[main spec](../../openspec/specs/bill-comparisons/spec.md)
and [tasks](../../openspec/changes/archive/2026-11-09-compare-cu07-consumption-with-bill/tasks.md).

The user approved the three refinements (422 for invalid date order, two distinct
readings for one-day periods, clear Spanish messages without calculation-changing
rounding) and authorized BUILD directly. No new tables, migrations or dependencies
were introduced; CU07 reads existing CU05/CU06 data.

## Work

- Backend `app/comparison.py`: Buenos Aires local-date derivation, inclusive
  +/-7-day window, exact decimal canonicalization, recorded/difference/outcome and
  the decreasing-reading guard.
- Backend `app/comparison_api.py`: owner-scoped candidate and comparison routes.
  The comparison route revalidates ownership, distinct IDs, window membership, date
  order and the confirmation flag; non-exact pairs without confirmation return
  `409 CONFIRMATION_REQUIRED` with the real dates and candidates. No percentage,
  interpolation, proration or mutation.
- Frontend `features/bills/comparison.ts` and `BillComparison.tsx`: runtime-validated
  client, direct exact comparison, manual candidate selects, visible real-date
  warning and explicit confirmation, and comparable/no-comparison rendering in the
  existing bill workspace.
- Added `tests/test_comparison.py`, `tests/test_comparison_api.py`,
  `tests/test_comparison_postgres.py`, `tests/seed_cu07_e2e.py`,
  `frontend/tests/comparison-api.test.ts` and `frontend/e2e/cu07.spec.ts`.

## Checks and results

- **PASS:** `openspec validate --all --strict` (OpenSpec 1.16.1): 10/10 items before
  archive, and `openspec validate --specs --strict`: 7/7 after sync.
- **PASS:** full backend suite on the isolated CU06 QA PostgreSQL with
  `TEST_DATABASE_URL`, `CU05_PHOTO_DIR=/photo-tests`, a synthetic
  `CU06_CONFIRMATION_SECRET` and the CU06 bill directory: 278 tests, 2 opt-in
  skips, OK. The first run without the bill/photo environment returned expected
  503/photo-directory errors; the configured rerun passed.
- **PASS:** Ruff 0.17.4 on `app` and `tests`; mypy 2.4.1 strict on 30 modules.
- **PASS:** frontend `node --test` 80 tests (5 new comparison tests), Oxlint zero
  warnings/errors, `tsc --noEmit`, and `vite build`.
- **PASS:** 4/4 Chromium scenarios against the development frontend/backend with
  synthetic accounts: exact direct comparison, multiple candidates via manual
  selection, approximate comparison with confirmation, zero consumption, decreasing
  reading and cross-account 404 isolation.
- The browser flow required restarting the development frontend so Vite served the
  current mounted source; the earlier cached module lacked `BillHistory`.
- The development PostgreSQL was upgraded from `0003_cu05` to the already-approved
  `0004_cu06` revision so the seeded bill table existed. This is not a CU07
  migration and was applied only to the synthetic development database.

## Independent review and corrections

A focused independent `reviewer` session (`ses_e3d6e939dffe7rvvDOAVkDrrgK`) audited
ownership, windows, confirmation, arithmetic, frontend state and regressions. It found
one MAJOR and several MINOR issues; all confirmed findings were corrected:

- **MAJOR:** `Decimal` arithmetic used the process-wide 28-digit context, silently
  rounding readings that CU05 accepts beyond that precision. `compare_values` now runs
  in a `localcontext` sized from the operands and clamps `Emax`/`Emin`; a 30-digit
  regression test asserts exact recorded and difference values.
- **MINOR:** bills near `date.min`/`date.max` could raise `OverflowError`; `window()`
  now clamps and candidate construction/`local_date` conversion return a controlled
  empty/422 instead of 500. Added a window-clamp test.
- **MINOR:** the UI could show stale bill metadata; it now uses the server candidate
  period/billed values for display and exactness.
- **MINOR:** a single shared reading for both windows now yields the neutral
  no-comparison state instead of a dead-end form.
- **MINOR:** multiple candidates are no longer preselected; a window must have exactly
  one candidate to preselect.
- Added a foreign/missing reading-ID 404 test.
- The confirmation remains an inline panel rather than a modal; the backend-validated
  confirmation contract is unchanged. This presentation choice is recorded as Q14
  latitude, not a functional relaxation.

Re-verification after the corrections: 278 backend tests (2 skipped), Ruff/mypy,
frontend typecheck/Oxlint, and 4/4 Chromium scenarios passed.

## Limitations and closure

- The CU07 comparison itself adds no schema, migration, file store or dependency.
- Independent/human review of ownership, validation and regressions remains the open
  closure gate (task 4.3); it was not performed in this BUILD because the user asked
  to avoid repetitive reviews.
- No Sync, Archive, commit, push or deployment was performed. Synthetic accounts,
  seeded comparison scenarios and the development database remain retained.
