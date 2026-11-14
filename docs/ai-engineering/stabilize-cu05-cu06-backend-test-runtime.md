# stabilize-cu05-cu06-backend-test-runtime

## Goal

Provide a reproducible, isolated runner for the six historical CU05/CU06 backend test
failures so they can be classified as environmental or product defects without modifying
product code or fixing the separate CU05 history E2E bug.

## Spec / design links

- [Change proposal](../openspec/changes/stabilize-cu05-cu06-backend-test-runtime/proposal.md)
- [Change design](../openspec/changes/stabilize-cu05-cu06-backend-test-runtime/design.md)
- [Change tasks](../openspec/changes/stabilize-cu05-cu06-backend-test-runtime/tasks.md)
- [CU05 change](../openspec/changes/archive/2026-11-13-record-cu05-meter-readings/proposal.md)
- [CU06 archived change](../openspec/changes/archive/2026-11-09-record-cu06-electricity-bills/proposal.md)

## What was built

- `scripts/Test-Cu05Cu06BackendRuntime.ps1` — focused PowerShell runner.
- Updates to `docs/STATE.md` and `README.md` with commands and results.
- OpenSpec change artifacts under `openspec/changes/stabilize-cu05-cu06-backend-test-runtime/`.

No backend, frontend, API, contract or schema code was changed.

## Key decisions and approvals

- Reuse the existing `energia-sur-backend-checks:cu10` verification image.
- Create one isolated PostgreSQL role/database per run (not two); set both
  `DATABASE_URL` and `TEST_DATABASE_URL` to it.
- Use per-run tmpfs mounts for CU05 photos (`/photo-tests`) and CU06 bills
  (`/bill-tests`) with `nosuid`, `nodev`, `mode=700` and runtime UID `10001`.
- Generate a 32-byte synthetic `CU06_CONFIRMATION_SECRET` per run and pass it only
  through the container environment.
- Verify OCR privacy preconditions (`RLIMIT_CORE == 0` and cgroup v2
  `memory.swap.max == 0`) before the real OCR test; fail closed if they cannot be
  satisfied.
- Use a 2 GiB container memory limit with swap disabled so the cgroup swap limit is
  `0`; this satisfies the OCR privacy check while leaving enough headroom for the
  bounded OCR/photo workers.

## Problems and corrections

1. **Import path / multiprocessing spawn.** Running the tests through a single-file
   runner script caused `ModuleNotFoundError` and later a multiprocessing bootstrap
   `RuntimeError` because `__main__` was re-executed in spawned workers. Fixed by
   wrapping the test-discovery code inside `if __name__ == '__main__':` in the
   generated per-test runner script.
2. **Missing `test_bill_postgres.py` in older image.** The default `:cu09` verification
   image did not contain the CU06 bill tests. Fixed by switching the default to the
   current `:cu10` verification image.
3. **`pgvector` extension privilege.** The isolated role could not create the `vector`
   extension required by migration `0007_cu03`. Fixed by pre-creating the extension as
   the cluster superuser before running Alembic.
4. **Reconciliation warning count.** `test_startup_logs_reconciliation_failure_without_leaking_paths`
   expected exactly one warning, but a missing CU06 configuration caused `reconcile_bills()`
   in `app.main.lifespan()` to log a second warning. With `CU06_BILL_DIR` and
   `CU06_CONFIRMATION_SECRET` correctly set, only the patched photo-reconciliation
   warning is emitted and the test passes.

## Verification results

| Check | Result | Evidence |
| --- | --- | --- |
| Six historical targeted tests | 6/6 PASS | `results.csv` in artifact directory |
| CU06 regression (`test_bill_*.py`) | 32/32 OK (1 skipped) | `unittest discover -p 'test_bill_*.py'` |
| CU05 regression (`test_photo_*.py`) | 45/45 OK | `unittest discover -p 'test_photo_*.py'` |
| Ruff | PASS | `docker run --rm energia-sur-backend-checks:cu10 ruff check --no-cache app tests migrations` |
| mypy | PASS | `docker run --rm energia-sur-backend-checks:cu10 mypy --cache-dir /tmp/mypy-cache app` |
| OpenSpec validation | 16/16 PASS | `openspec validate --all --strict` |
| Independent reviewer | PASS with minor findings | Reviewer `ses_e289a490bffe4NXKGUlQRJKlMG`; design.md/README.md/script comments corrected |

## Commands

```powershell
pwsh -NoProfile -File scripts/Test-Cu05Cu06BackendRuntime.ps1
pwsh -NoProfile -File scripts/Test-Cu05Cu06BackendRuntime.ps1 -Cleanup
```

## Closure

- Archived as `2026-11-13-stabilize-cu05-cu06-backend-test-runtime` on 2026-11-13 with
  10/10 tasks complete; no spec deltas to sync.
- User authorized APPLY + VERIFY and archive on 2026-11-13.
- This change does **not** fix the separate CU05 history E2E bug; that will be handled
  by the next change `isolate-cu05-reading-history-by-meter`.
