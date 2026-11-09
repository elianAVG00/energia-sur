# Proposal

## Why

CU06 needs a private, durable record of billed consumption and the supporting bill, linked to an owned CU04 meter. Exact boundary dates also preserve compatibility with the approved CU07 matching rule without implementing comparison.

## What Changes

- Propose owner-only creation, listing, viewing, correction and file retrieval for bills. Preserve bill and meter identity; do not offer deletion or reassignment.
- Record required start and end dates, nonnegative billed kWh with up to three decimal places, a PDF/JPG/PNG file, and optional ARS amount. Reject identical periods for a meter and allow explicitly confirmed overlaps.
- Propose a private persistent attachment lifecycle, bounded validation, optimistic concurrency and race-safe duplicate/overlap handling.
- Exclude OCR, extraction, authenticity verification, tariff calculations, consumption comparison and physical meter replacement. No existing CU04/CU05 contract changes are intended.

## Capabilities

### New Capabilities

- `electricity-bills`: account-owned bill records and private supporting files for CU06.

### Modified Capabilities

None.

## Impact

Future work affects FastAPI, PostgreSQL/Alembic, private volume operations and the React workspace. Reuse CU04 ownership and CU05 patterns without treating CU05's open OCR closure as a CU06 prerequisite. Dependencies and PDF validation require review; no new package is approved here. Sources: `docs/use-cases/cu06.md`, shared SR02/SR04, Q12/Q13 and the user's CU06 PLAN and PROPOSE instructions; the original PDF is unavailable in this checkout and its `docs/stage-05-context.md` synthesis is the source consulted. Q00 is satisfied by U06 user confirmation. Functional rules are approved in conversation; technical refinements are proposed for explicit human Review. This proposal authorizes neither Apply nor migration, deployment, Sync or Archive.
