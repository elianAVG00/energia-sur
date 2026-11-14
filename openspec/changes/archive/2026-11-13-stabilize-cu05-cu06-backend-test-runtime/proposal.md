# Proposal: Stabilize CU05/CU06 backend test runtime

## Why

CU05 meter readings and CU06 electricity bills are implemented and mostly verified, but six historical backend tests fail reproducibly when executed outside their expected isolated Docker QA environment. The failures are caused by missing private storage directories, a missing CU06 confirmation secret and unverifiable OCR privacy preconditions, making it impossible to distinguish environmental gaps from real product defects before fixing the separate CU05 history E2E bug. This change delivers a focused, non-destructive runner that reproduces those six tests with correct preconditions and records PASS/FAIL/BLOCKED evidence.

## What Changes

- Add `scripts/Test-Cu05Cu06BackendRuntime.ps1`, a focused PowerShell runner that:
  - Provisions an isolated PostgreSQL role and database on the existing local `energia-sur-db-1` cluster without deleting or recreating shared services.
  - Creates per-run private temporary directories for CU05 photos and CU06 bills using container tmpfs mounts.
  - Generates a synthetic 32-byte CU06 confirmation secret passed only through the container environment.
  - Runs exactly the six historical failing tests, capturing per-test logs and an aggregate result report.
  - Cleans up only the resources it created (role, databases, temporary dirs), leaving the shared db container and persistent volumes untouched.
- Verify OCR privacy preconditions (`RLIMIT_CORE == 0` and cgroup v2 `memory.swap.max == 0`) inside the verification container before attempting real OCR; fail closed and mark the test BLOCKED if the host runtime cannot satisfy them.
- Document the real cause of the `test_startup_logs_reconciliation_failure_without_leaking_paths` assertion mismatch (both photo and bill reconciliation log warnings during lifespan) without weakening the test or hiding product behavior.
- Update `docs/STATE.md` and the testing section of `README.md` with commands, required variables, preconditions and actual results.
- **No product code changes** and **no weakening** of OCR, storage or security restrictions.

## Capabilities

No spec-level behavior changes. This change is pure test infrastructure and documentation, so the change opts out of spec deltas with `skip_specs: true`.

## Impact

Affects only test scripts, runner documentation and operational state. No API contracts, UI components, database schemas, dependency versions or production configuration are modified.
