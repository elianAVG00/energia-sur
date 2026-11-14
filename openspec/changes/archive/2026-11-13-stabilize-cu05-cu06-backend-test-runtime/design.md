# Design: Stabilize CU05/CU06 backend test runtime

## Context

See [proposal](proposal.md) for motivation. The six historical backend failures are:

1. `backend/tests/test_bill_postgres.py::BillPostgresTests.test_concurrent_idempotent_replay_and_duplicate`
2. `backend/tests/test_bill_postgres.py::BillPostgresTests.test_concurrent_edits_advance_version_once`
3. `backend/tests/test_bill_postgres.py::BillPostgresTests.test_bill_isolation_duplicate_overlap_edit_and_file`
4. `backend/tests/test_photo_postgres.py::PhotoPostgresTests.test_ocr_real_engine_suggestion_does_not_save`
5. `backend/tests/test_photo_postgres.py::PhotoPostgresTests.test_ocr_abstains_if_runtime_privacy_is_unverifiable`
6. `backend/tests/test_photo_postgres.py::PhotoPostgresTests.test_startup_logs_reconciliation_failure_without_leaking_paths`

The first three fail when `CU06_BILL_DIR` is unset or relative and `CU06_CONFIRMATION_SECRET` is shorter than 32 bytes, because `bill_api._configuration()` returns HTTP 503 before any business logic runs. The fourth needs a writable CU05 photo directory, Tesseract and verifiable OCR privacy preconditions. The fifth is mocked and verifies fail-closed abstention. The sixth currently asserts exactly one warning record, but `app.main.lifespan()` logs a warning for both photo reconciliation failure and bill reconciliation failure, so the count is environment-dependent.

## Goals / Non-Goals

**Goals**
- Provide a single-command, reproducible QA runner for the six tests.
- Use only isolated synthetic databases and temporary storage.
- Capture per-test evidence (logs, status, traceback) without exposing secrets.
- Clearly classify each result as PASS, FAIL or BLOCKED.
- Record the origin of the reconciliation-log warning count discrepancy.

**Non-Goals**
- Fixing the separate CU05 history E2E bug.
- Modifying product behavior, contracts or security restrictions to make tests pass.
- Running the full acceptance suite or recreating shared services.
- Cleaning up external QA artifacts from prior runs.

## Decisions

### Reuse the existing verification image

The project already builds `energia-sur-backend-checks:cu10` with Python, Tesseract, OpenCV and the current backend dependencies. Reusing it avoids new images and dependency changes. The runner passes the required environment variables to each container.

### Isolated but additive database provisioning

The runner creates a unique nonprivileged role and one isolated test database on the running `energia-sur-db-1` container, setting both `DATABASE_URL` and `TEST_DATABASE_URL` to it. It never drops the existing `energia_sur` database, `pgdata` volume or shared db container. This preserves existing development state while guaranteeing a clean schema.

### Private temporary storage with tmpfs

CU05 photos and CU06 bills use separate container tmpfs mounts (`/photo-tests` and `/bill-tests`) with `nosuid`, `nodev`, restricted size and ownership by the runtime UID (`10001`). This keeps synthetic bytes out of persistent volumes and avoids cross-test leakage.

### Synthetic CU06 confirmation secret

The runner generates a 32-byte cryptographically random hex string and passes it as `CU06_CONFIRMATION_SECRET` only through the container environment. It is never written to tracked files, logs or chat.

### Fail-closed OCR privacy verification

The real OCR engine test requires `private_ocr_runtime()` to return `True`. Inside the verification container this depends on `RLIMIT_CORE == 0` and cgroup v2 `memory.swap.max == 0`. The runner checks these preconditions explicitly. If they cannot be verified, the real-engine test is marked BLOCKED rather than weakening the check. The abstention test uses mocks and can run regardless.

### Targeted test execution

Instead of `unittest discover`, the runner invokes each of the six tests individually with `python -m unittest ... -v`. This produces per-test output and avoids unrelated test interactions.

### Reconciliation warning count

`test_startup_logs_reconciliation_failure_without_leaking_paths` patches only `app.main.reconcile_photos`, but `lifespan()` also calls `reconcile_bills()`. When `CU06_BILL_DIR`/`CU06_CONFIRMATION_SECRET` are misconfigured, bill reconciliation logs a second warning. With correct CU06 configuration bill reconciliation succeeds silently, leaving exactly the single patched photo-reconciliation warning the test expects. Therefore the runner supplies correct CU06 configuration and the test should pass; if it still sees two warnings, the second source will be identified before any assertion is changed.

## Risks / Trade-offs

- [Host does not expose cgroup v2 swap controls] → Real OCR test is BLOCKED; the abstention test still runs and the product fail-closed behavior is preserved.
- [Docker Desktop on Windows reports cgroup v1 or hybrid paths] → Same as above; no weakening of OCR admission.
- [tmpfs size too small for concurrent bill/photo tests] → Sizes are generous (32 MiB each) because synthetic fixtures are small; if a future test needs more, the runner parameters can be adjusted.
- [Synthetic databases accumulate across repeated runs] → Databases are uniquely named per run and never deleted automatically; the runner prints their names for manual cleanup.
- [Runner misconfiguration could touch shared services] → The script inspects the existing db container by name and creates only new role/databases; it does not run `docker compose up` or restart `db`.

## Migration Plan

No migration. The runner is a new script and documentation; it does not change deployed code or data.

## Open Questions

None that affect this change. The question of whether `test_startup_logs_reconciliation_failure_without_leaking_paths` should tolerate two warnings when CU06 is misconfigured is deferred to a separate product change if evidence shows it is needed; this runner resolves the environmental cause instead.
