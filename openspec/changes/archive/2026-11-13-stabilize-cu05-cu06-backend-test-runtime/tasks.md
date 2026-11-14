# Tasks: Stabilize CU05/CU06 backend test runtime

## 1. Review and OpenSpec gates

- [x] 1.1 Read the six affected tests, `app/main.py`, `app/ocr_worker.py` and `app/bill_api.py`; confirm the environmental causes of each historical failure.
- [x] 1.2 Create OpenSpec change artifacts (`proposal.md`, `design.md`, `tasks.md`, `.openspec.yaml` with `skip_specs: true`) and run `openspec validate --strict` for the change.

## 2. Focused QA runner

- [x] 2.1 Implement `scripts/Test-Cu05Cu06BackendRuntime.ps1` that provisions an isolated role/database on `energia-sur-db-1`, migrates it, sets `DATABASE_URL`/`TEST_DATABASE_URL`, mounts private tmpfs dirs for CU05/CU06 and generates a synthetic `CU06_CONFIRMATION_SECRET`.
- [x] 2.2 Add explicit OCR privacy precondition checks inside the container (`RLIMIT_CORE == 0` and `/sys/fs/cgroup/memory.swap.max == 0`) and skip/mark BLOCKED the real-engine OCR test when they are not satisfied.
- [x] 2.3 Run each of the six historical tests individually, capture per-test output, and write an aggregate report to a user-local artifact directory.

## 3. Analysis and verification

- [x] 3.1 For `test_startup_logs_reconciliation_failure_without_leaking_paths`, identify whether the second warning originates from `reconcile_bills()` and confirm the runner's correct CU06 configuration eliminates it.
- [x] 3.2 Run Ruff and mypy on any new/modified backend files and run a focused CU05/CU06 regression subset to detect runner-introduced regressions.
- [x] 3.3 Request an independent `reviewer` audit of the runner, isolation, security and absence of product changes; address only runner-related findings.

## 4. Documentation

- [x] 4.1 Update `docs/STATE.md` with the active change link, the six test results, OCR precondition status and the next action (CU05 history E2E bug fix awaits separate authorization).
- [x] 4.2 Update `README.md` testing section with the runner command, required variables and example output.

## Workflow follow-up

- Archive this change only after the user authorizes the resulting artifact and the CU05 history E2E bug is handled in a separate change.
