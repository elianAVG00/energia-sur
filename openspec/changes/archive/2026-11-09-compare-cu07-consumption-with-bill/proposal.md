# Proposal: CU07 recorded consumption vs bill

## Why

Account holders need to compare the consumption derived from their own CU05 meter
readings with the kWh recorded in a CU06 bill for the same meter. The previously
approved exact-boundary rule is too rigid for real reading dates, so U14 replaces it
with a bounded +/-7-day window that requires explicit confirmation for approximate
periods.

## What Changes

- Add a read-only, on-demand comparison between one CU06 bill and CU05 readings of
  the same owned meter and account; persist nothing.
- Match each bill boundary against readings whose Buenos Aires local date is within
  +/-7 days inclusive. Exact boundary dates compare directly.
- When a selected boundary date differs from the billed boundary, require explicit
  confirmation; when multiple candidates exist, require manual selection of the start
  and end readings.
- Never interpolate, prorate or estimate. Show the real reading dates and a visible
  warning when they differ from the billed period.
- Do not calculate when a boundary has no compatible reading or when the end reading
  is lower than the start reading.
- Show recorded consumption, billed kWh and the exact difference in kWh with its
  direction; no percentage.
- Exclude OCR, PDF extraction, bill authenticity, tariff or fraud features, new
  tables/migrations and any mutation of CU05/CU06 data.

## Capabilities

### New Capabilities

- `bill-comparisons`: owner-scoped, read-only comparison of recorded meter
  consumption with a recorded bill.

### Modified Capabilities

None. CU05 and CU06 contracts are reused without changing their requirements.

## Impact

Future work affects the FastAPI read API and the React bill workspace. No database
schema, migration or private-file change is required. Reuses CU04 ownership, CU05
reading data, CU06 bill data and the existing opaque session.

Sources: `docs/use-cases/cu07.md`, decisions U14/Q13/Q14, shared SR02/SR04, and the
CU05/CU06 specifications. Q00 is satisfied by U06 user confirmation. Functional
rules are approved in conversation (U14); technical details are proposed for
explicit human Review. This proposal authorizes neither Apply nor code, migration,
deployment, Sync, Archive, commit or push.
