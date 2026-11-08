# Design

## Context

See `proposal.md` and both delta specs. The current `es_domiciles` has stable ID, account ID and 300-character display address; `es_interruptions` points to domicile ID. `GET/POST /domiciles` return only ID and display address, permit duplicates and do not require meters. The PDF uses the current address. `Workspace.tsx` owns the domicile list; the memory-only session store owns its selected ID. The shared HTTP interceptor currently appends diary-specific advice to every 409.

## Goals / Non-Goals

**Goals:** preserve old clients, rows, cuts and session isolation while adding CU04 with enforceable concurrent uniqueness and stale-write protection.

**Non-Goals:** change archived CU09 specifications or CU03 mount; implement CU05/CU06, attachments, geocoding, shared ownership, deletion, transfer or physical meter replacement; change dependencies.

## Decisions

### Approved boundaries and reviewable refinements

U11 and U12 approve CU04-scoped ownership, meter identity, validations, routes and conflict codes, additive migration, composite FK, optimistic locking and composition. This approval does not extend to other CUs. BUILD is conditional on successful REVIEW, independent review and documented gates.

### Data and concurrency

Add `es_domiciles.version` positive and non-null, with server default 1 so preexisting rows and old `POST /domiciles` remain valid. Add unique `(id, account_id)` for a composite reference. Create `es_meters` with `id` string(36) PK, `domicile_id`, `account_id`, `meter_number` string(120), nullable `alias` string(120), and positive `version` default 1. A composite FK `(domicile_id, account_id)` references the corresponding domicile pair. Use a unique DB index on account and normalized number; the redundant account ID is intentional so the DB enforces both association consistency and account-wide uniqueness under concurrent writes. A pre-insert check alone is insufficient.

Meter numbers contain only ASCII bytes 0x20–0x7e: reject all non-ASCII, NUL and controls before trimming; trim ASCII space (0x20) from both ends and require 1–120 characters. Preserve case, leading zeroes, punctuation and internal spaces for display. Compare using ASCII A–Z to a–z after trimming. PostgreSQL enforces a named unique expression index on `(account_id, translate(btrim(meter_number, ' '), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') COLLATE "C")`, with a check constraint that stored numbers are nonempty printable ASCII and already trimmed. Backend uses the same ASCII translation and trimming. This deterministic index is atomic under concurrent writes and does not rely on a prior query or Unicode locale.

Alias: optional JSON null or string, reject NUL and Unicode control characters (category Cc) before trimming; trim Unicode whitespace, convert blank to null and enforce at most 120 Unicode characters after trimming. Spanish accented text is allowed and alias never participates in uniqueness. Do not change the current domicile input contract.

Every domicile or meter PATCH MUST perform a PostgreSQL atomic `UPDATE` with expected version and owner in its predicate, set submitted values and `version = version + 1`, and return the updated row via `RETURNING`. For meters include both path domicile ID and account ownership through the composite association. This write occurs even for identical values; each successful request increments exactly once and returns that new version. Mapper `version_id_col` alone or a prior version read cannot satisfy this rule. A zero-row result is classified by a same-transaction owner-scoped existence query: owned resource means `409 VERSION_CONFLICT`, foreign/missing/mismatched means indistinguishable 404, with no foreign data exposed. No deletion or reassignment route exists; if any is introduced later, its locking/isolation must preserve this classification.

Execute each correction as one transaction; on duplicate constraint or other failure roll back all changes. Map only the named meter unique constraint to `DUPLICATE_METER`; other DB errors retain sanitized 503 behavior. Never retry writes automatically. Independent PostgreSQL connections and controlled interleavings MUST verify changed/no-op current and stale writes, two concurrent same-version PATCHes, changed-versus-old-value race, foreign/missing 404 and failure atomicity for both resource types.

### Proposed API

Paths below are backend paths; the frontend uses the existing `/api` proxy. All responses are JSON with no-store. Existing `GET /domiciles` and `POST /domiciles` and `{id, display_address}` response stay unchanged. Input objects reject unknown fields.

| Method/path | Input | Success |
| --- | --- | --- |
| `GET /domiciles/{d}/management` | none | 200 `{id, display_address, version}` |
| `PATCH /domiciles/{d}` | `{display_address, version}` | 200 management DTO |
| `GET /domiciles/{d}/meters` | none | 200 array of meter DTOs |
| `POST /domiciles/{d}/meters` | `{meter_number, alias?}` | 201 meter DTO |
| `GET /domiciles/{d}/meters/{m}` | none | 200 meter DTO |
| `PATCH /domiciles/{d}/meters/{m}` | `{meter_number, alias, version}` | 200 meter DTO |

Meter DTO: `{id, domicile_id, meter_number, alias, version}`. Version is a strict positive integer. Patch is a complete correction payload, with null to clear alias. Domicile `display_address` keeps the existing trimmed 1–300 validation. Session-invalid is 401; origin/CSRF failures 403; foreign, missing or mismatched resources 404; invalid input 422. CU04 409 JSON is `{ "detail": "<sanitized user message>", "code": "DUPLICATE_METER" | "VERSION_CONFLICT" }`; clients validate the code and never branch on message text. Stale domicile or meter edits use VERSION_CONFLICT, same-account meter duplicates use DUPLICATE_METER. Preserve existing CU09 `{detail: string}` errors and recovery. Check ownership first, preserve no-store and never reveal another account's state.

`meter_number` identifies a physical device, not a customer number. A customer number commonly has 7–10 digits and can appear alongside the meter number on a bill; those observations are examples, not validation rules. No `customer_number` field is added. Whether CU06 needs it remains a future CU06 decision and does not block CU04.

### Frontend composition

Add `frontend/src/features/domiciles/` with RHF/Zod forms and a typed adapter using shared Axios. Keep `Workspace.tsx` as the only owner of the domicile rows and Zustand's `selectedDomicileId` as the only shared selection; pass rows and update callbacks into the new feature. Replace a row after a validated correction without remounting the diary or losing its draft; use scopes, abort signals and generation/selection checks to reject stale responses. Reset only CU04 drafts when their account, domicile, meter or revision changes. Meter rows remain feature-local. Validate status, MIME, shape and response identity.

Remove or scope the transport's unconditional diary-specific 409 advice while retaining existing CU09 behavior through the diary UI. No second Axios client/store/router/cache and no CU03 mount changes. Duplicate-address warning uses an exact trimmed comparison against currently loaded own rows, excludes the row being edited, and does not block submission.

## Risks / Trade-offs

- Normalization and SQL collation can diverge → use explicit ASCII translation and C collation, test controls/non-ASCII, ASCII edge cases and concurrent database writes.
- Existing PDF output changes after address correction → inform the user and test that IDs, cuts and calculations stay unchanged; no historical address snapshot is promised.
- Version addition or composite FK could disrupt old rows/clients → use additive defaults and test existing data, original API payloads, restart and two accounts on real PostgreSQL.
- Different 409 causes can mislead users → differentiate them without weakening CU09 conflict recovery.
- Later readings/bills may require history rules not covered here → decide Q09/Q10/Q11/Q12 before those features; do not assume safe edits once linked records exist.

## Migration Plan

After successful review and satisfaction of the user's conditional Apply authorization, create a new Alembic revision based on `0001_cu09`; add domicile version and supporting uniqueness, then create meters and constraints. Do not modify the initial revision, recreate tables, delete rows, alter cut FKs or require existing domiciles to have meters. Test an upgrade from populated 0001 using synthetic records and retained data; do not perform destructive downgrade. Correct forward with another migration; any data deletion or destructive rollback requires separate explicit authorization and recovery planning.
