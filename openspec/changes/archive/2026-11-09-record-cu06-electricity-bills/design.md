# Design: CU06 electricity bills

## Context

CU04 meters have stable IDs, a domicile and account ownership; CU09 provides sessions and Origin/CSRF. CU05's implemented file store and frontend provide useful patterns, but CU05's OCR contract is still open. `photo_store.py` and recovery scan only `cu05-` objects and CU05 references; do not blindly reuse those names or delete rules. See proposal and delta for scope.

## Goals / Non-Goals

**Goals:** preserve private attachments and exact calendar/value semantics under concurrent writes and failures, without changing existing CU04/CU05 contracts.

**Non-Goals:** OCR, parsing invoice fields, bill authenticity, calculations, deletion, reassignment, a new storage provider, or a CU07 comparison implementation.

## Decisions

### Status and data

Confirmed by the user's PLAN instruction: dates required and start ≤ end; kWh ≥ 0 and up to three decimals; required PDF/JPG/PNG ≤ 5 MB; optional ARS with at most two decimals; identical meter/period duplicates blocked; overlaps warned and confirmable; edit fields/file with stable ID, no deletion/reassignment, owner-only access. The user subsequently approved Review and authorized Apply of this design.

Propose an additive `bills` table: opaque ID, meter FK, two PostgreSQL `DATE`s, exact numeric billed kWh and optional ARS, non-null opaque file key and validated MIME type, positive version. The domicile is derived through the stable owned meter, avoiding redundant inconsistent associations. PostgreSQL enforces date order, finite nonnegative kWh, maximum scales without silent rounding, positive version and unique `(meter_id, start_date, end_date)`; proposed nonnegative ARS has equivalent constraints. No automatic future-date cutoff. Calendar dates stay dates in API/UI/DB, with no timezone conversion; future CU07 resolves its own reading-local-date selection under Q10/Q13. Use decimal strings, not binary floats, with up to 18 integer digits for either value and 3/2 fractional digits respectively; reject extra digits, signs, exponents and rounding. This bounded precision is a technical proposal for Review, not a prior functional restriction.

### Overlap and concurrency

Propose inclusive periods: overlap iff new start ≤ existing end and new end ≥ existing start. An exact duplicate takes precedence. Serialize every bill create and edit for a meter using a database row lock on that owned meter, and perform version/duplicate/overlap checks and write in the same transaction; the DB unique constraint remains the final concurrent duplicate defense. All code paths obey the same lock order. Edits exclude their own row. A 409 `OVERLAP_CONFIRMATION_REQUIRED` returns the owned overlapping bills' IDs, dates and versions and a server-issued integrity-protected token tied to account, meter, operation, bill ID/target version, proposed dates and a canonical snapshot of overlap IDs/versions/dates. The token also binds a length-delimited fingerprint of validated canonical kWh, nullable canonical ARS, file action and SHA-256 digest of decoded replacement/create bytes (or an explicit keep marker). No base64 spelling, token or idempotency key enters this fingerprint. Reacquire the lock and recompute on confirmation: only the unchanged complete snapshot and matching payload authorize the write; stale, changed or missing confirmation returns a fresh warning with no mutation. Test changes to each bound field, including file bytes. The client displays the actual intervals and preserves draft data. Same-day boundary contact warns, unlike half-open intervals. Avoid relying on a UI-only preflight which races with concurrent requests.

The user approved a random secret of at least 32 bytes supplied through a backend-only environment variable, automatically generated for local Docker and never stored in Git. Local restart may invalidate outstanding confirmations, requiring a fresh warning. No key-rotation infrastructure is in scope; concurrent instances serving one workflow need the same effective key.

Each PATCH requires current version and advances it even if unchanged; stale versions return 409 `VERSION_CONFLICT`. Duplicate returns 409 `DUPLICATE_BILL`; 409 codes are structured, not message-matched. Propose a CU05-style stable create idempotency key and transactional account/meter/payload fingerprint, including decoded file digest and confirmation state; a retry of a committed identical request returns its original response, a different payload with the same key returns `IDEMPOTENCY_KEY_REUSED`. A warning is not a committed creation: the confirmed attempt uses a new key, retained across uncertain retries. Client reconciles uncertain PATCH by GET/version before retry. No automatic overwrite.

### Proposed API and UI

Backend paths, using the existing `/api` browser proxy: `GET/POST /meters/{meter_id}/bills`, `GET/PATCH /meters/{meter_id}/bills/{bill_id}`, `GET /meters/{meter_id}/bills/{bill_id}/file`. Create accepts ISO date strings, decimal strings, nullable amount, standard base64 file and optional overlap token; PATCH adds version and `file_action` keep/replace, requiring bytes only for replace. Strict validation rejects extra fields. Return ID, meter ID, dates, values, version and file metadata, never filesystem paths. GET file returns a private attachment with validated MIME, safe fixed filename, `Content-Disposition: attachment`, `nosniff`, and `Cache-Control: no-store`; private JSON is also no-store. Existing session and owner meter checks precede input processing; absent/foreign/mismatched resources return the same 404, invalid Origin/CSRF 403, invalid data 422, oversize 413, wrong transport 415, unavailable storage 503, without sensitive diagnostics.

Wire names: bill response `{id, meter_id, period_start, period_end, value_kwh, amount_ars, file_type, version}`; list is an array of these objects. Create JSON `{period_start, period_end, value_kwh, amount_ars, file_base64, overlap_token}` with an `Idempotency-Key` header; nullable amount/token must be explicitly present. PATCH JSON uses the same data plus `version` and `file_action`, with `file_base64` null for `keep` and non-null for `replace`. Success statuses are 200 for list/detail/edit/file and 201 for create. Conflicts are JSON `{detail, code}`; overlap conflict additionally returns `{overlaps: [{id, period_start, period_end, version}], overlap_token}`. A warning does not commit; confirmation resubmits the same values and bytes with the returned token and a new create idempotency key. All these details refine the approved behavior, not the business scope.

Reuse the selected domicile/meter workspace, session-scoped request cancellation and form components. List and detail, create/edit fields, select/replace/download, warn and confirm overlaps; never expose delete or meter/domicile controls on an existing bill. Clear account-scoped state and object URLs on context changes. UI validation supplements, never replaces, server rules.

### File safety and lifecycle

Use 5,000,000 decoded bytes, a streamed request cap of 7,000,000 bytes before JSON buffering and strict base64 decoding. Validate real signatures and structure, not extension/client MIME; restrict JPG/PNG to bounded isolated image validation similar to CU05, disallow WebP, and limit decoded pixels/time/memory. The user approved `pypdf` as a production dependency for structural, page, encryption and detectable-active-content checks in an isolated time- and memory-bounded process, with documented limitations. Reject encrypted, malformed and detected active content, never render, execute, extract bill data or follow external references. The user explicitly accepts the limitations of this approach; do not claim complete malware detection. Attachment delivery reduces active-content risk but does not make downloaded PDFs harmless.

Propose a private dedicated CU06 namespace and directory/volume, opaque immutable keys, no client filenames or public mount. Reuse CU05's *pattern*, not its hard-coded names, locks or reference scanner. All instances and maintenance use a consistent shared PostgreSQL advisory lock then CU06 filesystem lock then meter row/transaction locks; reads retain protection until bytes are safely materialized or streaming ends. Durable no-replace publication and directory fsync precede DB commit. Preserve old file until commit; on definite failure clean only after a reference check. On unknown commit preserve both; invalidate connection, release filesystem lock, and reconcile only after original transaction/session resolution under locks, checking all CU06 committed references. Unknown topology or unavailable DB means no deletion. Missing referenced object fails closed and requires restoration; no silent repair. Cleanup is CU06-only and never operates on CU05 keys. Coordinated backup/restore must quiesce writers and pair the database with both relevant private volumes. No actual cleanup or backup is authorized now.

## Risks / Trade-offs

- [Concurrent changes invalidate a prior warning] → token binds the complete current overlap snapshot and is revalidated under the meter lock.
- [PDF parser exploit, active content or resource exhaustion] → bounded local structural validation, attachment-only delivery and explicit approval/verification; no claim of malware-free documents.
- [DB/filesystem partial failure] → immutable objects, lock ordering, commit-aware recovery and synthetic crash tests; no claim of atomic filesystem/database transaction.
- [CU05 hard-coded cleanup] → isolate CU06 namespace, reference scan, locks and regression tests; no change to existing CU05 references.
- [Value bounds not previously approved] → 18 integer digits and sign policy are proposed, subject to Review; do not claim prior approval.

## Migration Plan

After separate Apply authorization, add a non-destructive Alembic revision and provision the private volume with deployment permissions; verify upgrades with existing CU04/CU05 data. For rollback stop the new application and retain table and volume for recovery; no destructive downgrade or deletion without explicit authorization. Verify matched backups and restart behavior with synthetic data.

## Open Questions

CU07 selection among multiple same-date readings and display rounding remain CU07/Q10/Q14 decisions and do not block CU06. Hosting and retention policy outside replacement recovery remain future decisions; no deletion is authorized by this proposal.
