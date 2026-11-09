# Tasks

## 1. Review and contract gates

- [x] 1.1 Obtain explicit human Review of proposal, delta and technical design, including inclusive periods, limits, ARS sign, overlap protocol and storage; record approval and resolve blockers before Apply.
- [x] 1.2 Specify and obtain approval for bounded PDF validation, resource limits and any production dependency; demonstrate with synthetic hostile/malformed PDF tests, or mark PDF implementation BLOCKED. (Approved `pypdf` runtime dependency; encrypted, active, malformed, empty and oversized synthetic PDFs rejected. The wall-clock timeout path is configured but not directly exercised.)
- [x] 1.3 Obtain a separate explicit Apply request; record authorization before functional implementation.

## 2. Persistence and validation

- [x] 2.1 Add the additive bill migration and constraints; verify upgrades with retained CU04/CU05 fixtures, finite decimals, exact precision, date order and concurrent duplicate cases on PostgreSQL.
- [x] 2.2 Implement strict date, decimal and file input validation; test boundaries, maximum digits, invalid/forged formats, 5,000,000/5,000,001 bytes and resource limits.
- [x] 2.3 Implement owner-scoped reads, versioned correction and creation idempotency; verify two-account isolation, concurrent writes, duplicate and unknown-outcome retry tests. (Concurrent same-key replay, distinct-key duplicate and competing edits verified; unknown outcome is handled by exact-payload replay and version reconciliation.)
- [x] 2.4 Implement inclusive overlap detection and confirmation bound to the fresh snapshot and complete payload under meter locking; test create/edit, endpoint contact, stale tokens, changed file/value, simultaneous overlaps and duplicate precedence. (Includes empty-current-snapshot warning and UI confirmation.)

## 3. Private attachment lifecycle

- [x] 3.1 Implement isolated private storage, protected delivery and per-account ownership checks; test no-store, attachment/nosniff, invalid Origin/CSRF and indistinguishable foreign/missing resources.
- [x] 3.2 Implement publication, replacement and safe recovery with consistent locks and no CU05 cleanup impact; test failures before/after commit, unknown commit, process death, missing objects and concurrent reads. (Startup reconciliation removes only unreferenced `cu06-` objects and crashed temporaries under the writer advisory/filesystem locks; live files, CU05 objects and concurrent reads are preserved; a missing reference blocks all deletion.)
- [x] 3.3 Document configuration and matched database/volume backup and restore; verify synthetic restart and a quiesced backup/restore drill without using real bills. (Isolated synthetic drill backed up and restored PostgreSQL plus the `cu06_bills` volume as a matched pair while the backend was stopped; bill fields and the private file SHA-256 matched after restore, and startup reconciliation retained live files.)

## 4. Frontend

- [x] 4.1 Add the meter-scoped bill list, form and private file download using existing components; test valid/invalid values, required files, replacement and no reassignment/deletion.
- [x] 4.2 Implement duplicate/version/overlap warnings and explicit confirmation with draft retention, safe retries and context reset; test stale overlap and account/meter switching.

## 5. Integration and evidence

- [x] 5.1 Run OpenSpec strict validation, backend tests/Ruff/mypy and frontend tests/lint/build; record PASS/FAIL/BLOCKED/NOT APPLICABLE and evidence.
- [x] 5.2 Run a synthetic end-to-end browser flow through real backend and private file storage with two accounts, correction and restart; record observed results and limitations.
- [x] 5.3 Obtain independent implementation review of ownership, file lifecycle, concurrency and regressions; resolve concrete findings and record evidence before closure. (Findings on connection reuse, empty overlap snapshot, aggregate validation admission and stale list responses were corrected; residual recovery gaps are tracked in 3.2/3.3.)
- [x] 5.4 Update `docs/STATE.md`, README and the CU06 engineering record with actual commands, evidence and outcomes; verify links and no sensitive data.

## Workflow follow-up

- Sync and archive only after all required gates pass and a separate explicit authorization.
