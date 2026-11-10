# Proposal

**Definitive scope (U22):** *CU02 — Consultar trabajos de mantenimiento eléctrico
informados por ENRE.*

## Why

CU02 is delivered with the definitive scope approved by the user in U22: public,
read-only consultation of the maintenance works that ENRE reports for Edesur. The
2026-11-10 investigation verified that ENRE `data_EDS.js` publishes
`cortesProgramados` with partido, localidad, alimentador, affected users and an
estimated restoration text, and does not publish start/end dates, a reason or
coordinates. `cortesComunicados` has never been observed populated, and the Edesur
`outage-report` agenda is unavailable and out of scope.

The original academic proposal (upcoming works filtered by dates, with planned
start/end, reason and proximity) is preserved in the CU02 fiche and in U22 as
historical context. It is not the delivered scope, and no date, reason or distance is
invented.

## What Changes

- Add a **public, read-only scheduled-works API** (`GET /scheduled-works...`) served
  from a PostgreSQL snapshot, never from ENRE at request time.
- Add an **independent server-to-server acquisition** for the same ENRE feed, reusing
  the existing TLS/`httpx` transport unchanged, with its own JSON5 parser, advisory
  lock, snapshot tables and fetch-run history. CU01 is not modified.
- Parse only `cortesProgramados` into normalized rows; count `cortesComunicados` and
  record whether it is present, but do not emit its rows because no populated shape
  has been observed.
- Return provenance, publication freshness, three-valued coverage and a normative
  state; keep the last valid snapshot across failures and never invent a negative.
- Expose `planned_start_at`, `planned_end_at` and `reason_text` as **null** with an
  explicit `limitations` list, and surface `normalizacion` as an estimated restoration
  text, never as a planned end.
- Add an independent public **"Trabajos"** view with partido/localidad selection,
  address/GPS assistance through the existing resolve endpoints, and no date inputs.
- Record the definitive scope and preserve the original proposal in U22; no dated
  behavior is promised by this change.

## Capabilities

### New Capabilities

- `scheduled-works`: public acquisition, caching and querying of ENRE-reported
  maintenance works by partido with an optional localidad, including provenance,
  publication freshness, three-valued coverage and the exact fields the source
  publishes.

### Modified Capabilities

None. No existing spec-level requirement changes. `current-outages`,
`interruption-diary`, `frontend-shell` and the account capabilities keep their
requirements unchanged; the new public "Trabajos" view is owned by the new
`scheduled-works` capability. `App.tsx` gains an additive third view in the same way
CU01 added "Cortes", and CU01's GeoRef/coverage code is reused read-only.

## Impact

- **Backend:** new `app/scheduled_parser.py`, `app/scheduled_store.py`,
  `app/scheduled_api.py`; additive migration `0006_cu02` with
  `es_scheduled_snapshots`, `es_scheduled_works`, `es_scheduled_fetch_runs`; a second
  lifespan task with its own advisory-lock key.
- **Frontend:** new `frontend/src/features/scheduled-works/` and a "Trabajos" entry in
  the existing shell; no router and no new frontend dependency.
- **Reuse, unchanged:** `app/enre_client.py` (transport), `app/georef.py` (resolve
  endpoints), `app/coverage.py` (read-only catalog), the shared Axios client and UI
  primitives.
- **Out of scope by design:** the Edesur `outage-report` agenda, future agenda, date
  filtering, temporal classification, planned start/end, unpublished reasons,
  distance/coordinates, coverage-catalog expansion, CU01 changes and CU10 UI.

## Operational notes (not pending work)

1. **Populated `cortesComunicados` shape unobserved.** It stays counted and not
   displayed. A future change would need a real populated capture; this is an
   operational limit of the source, not an unfinished CU02 requirement.
2. **Partial coverage catalog (inherited from CU01 U20).** Unverified zones stay
   `coverage_unverified` and no negative result is invented.
3. **Edesur agenda unavailable.** It is out of scope; a future change would require a
   new proposal and a verified payload.

See [design](design.md) for the acquisition flow, contracts, states and limits.
