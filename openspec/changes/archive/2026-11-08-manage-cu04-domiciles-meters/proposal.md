# Proposal

## Why

CU09 delivered only the account-owned domicile prerequisite, not CU04's management of personal meters and corrections. CU04 can build on those stable domicile identities while preserving existing interruption history and compatibility.

## What Changes

- Add owner-only meter registration, listing and correction, with stable identity, printable ASCII number, per-account duplicate protection and optional descriptive alias.
- Add owner-only correction of the existing display address, without changing its identity or requiring a meter; preserve existing domicile registration/listing and duplicate-address behavior.
- Preserve existing cuts and explain that future PDFs display the current address. Do not delete, transfer, merge or physically replace domiciles or meters.
- Propose additive persistence, optimistic concurrency, scoped security and a small composed frontend feature; no new dependencies or changes to CU03.
- Apply the user's approved CU04-scoped Q03/Q08/Q09 decisions only; do not resolve other use cases' ownership or file-lifecycle rules.

## Capabilities

### New Capabilities
- `account-meters`: owner-scoped meter management, identity, validation, duplicate prevention and safe correction.

### Modified Capabilities
- `account-domiciles`: owner correction, duplicate-address warning and continuity of existing domicile and CU09 behavior.

## Impact

Affected areas are `backend/app` models, schemas and APIs; an additive Alembic revision after `0001_cu09`; frontend `features/domiciles/` with minimal `Workspace.tsx` composition; and relevant tests. Existing domicile API responses remain compatible. Existing PostgreSQL, SQLAlchemy, FastAPI, React, RHF/Zod and Axios are reused; no dependencies are requested.

Sources: `docs/use-cases/cu04.md`, `shared-rules.md`, `decisions.md` (U11/U12), and current `account-domiciles`/`interruption-diary` specs. CU05/CU06, file retention, sharing, GeoRef, CU03 runtime and the archived CU09 change are out of scope. A meter number is not a customer number; no customer-number field is approved. The user approved the CU04 decisions and conditionally authorized Apply only after successful REVIEW, documentary gates and independent review with no blockers.
