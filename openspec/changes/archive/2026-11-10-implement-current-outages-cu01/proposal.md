# Proposal: CU01 current outage queries

## Why

CU01 lets a visitor or account holder query *currently reported* electricity outages in a zone, using the public ENRE Edesur feed as the primary source. The feed is now verified live end-to-end (HTTP 200, `var data = {...}` UTF-8 JavaScript literal, `Last-Modified` refreshing ~every five minutes), and decisions D1–D11 plus T1–T3 are approved and recorded in `docs/use-cases/decisions.md`, so this change captures the first external public-source integration for Energía Sur. No query of our frontend may depend on ENRE at request time: outages must be served from a cached snapshot that preserves provenance and uncertainty.

## What Changes

- Add a **public, read-only CU01 query API** (`GET /api/outages/...`) that reads a PostgreSQL snapshot of the ENRE feed — never ENRE directly — and returns reported outages, provenance, freshness and a normative result state for a partido with an optional localidad.
- Add a **server-to-server background acquisition** (initial cadence 5 minutes, D6) that fetches the ENRE feed with an isolated legacy-TLS context (D1) via `httpx`, parses the JavaScript data literal with JSON5 (D7), and normalizes/validates before persisting. Never execute remote code; if the JSON5 proof fails, stop and request approval instead of substituting a parser.
- Persist (D5) the **last valid snapshot**, its normalized rows and a **fetch-run history** with a bounded retention policy, via an additive Alembic migration; preserve the last valid snapshot across failures and `N/A` degradation (D8).
- Add a frontend feature (`frontend/src/features/outages/`) with partido + optional localidad selection, address assistance via a backend GeoRef adapter (D2/T1), optional consented browser geolocation with reverse geocoding (D9/T1), a versioned coverage catalog (D4/T2) and the differentiated states of D11. The existing shell has no router, so the change adds a minimal public view switch in the shared shell without introducing a router dependency.
- Show medium-tension, low-tension and preventive categories only; reserve programmed cuts for CU02 (D3). Show distributor-wide official totals and per-record figures, labelled as such, without summing localities or unverified dedup (D10).
- Apply freshness thresholds `fresh ≤ 15 min`, `stale ≤ 60 min`, `unavailable > 60 min` or no valid snapshot (D8); return `no_reports` only for a covered area with a fresh valid snapshot lacking records.

## Capabilities

### New Capabilities

- `current-outages`: public CU01 acquisition, caching and querying of ENRE-reported current Edesur outages by partido (with optional localidad) and GeoRef-assisted address/location resolution, including provenance, freshness, the normative state machine, three-valued coverage and the geographic limits of the source.

### Modified Capabilities

None. CU09 `interruption-diary`, CU04/CU05/CU06/CU07 capabilities and the `frontend-shell` requirements are reused; the shell files are extended additively for a public view without changing an existing requirement. CU02 (programmed works) and CU10 (source administration) are explicitly not implemented.

## Impact

- **Backend:** new modules (`app/enre_client.py`, `app/enre_parser.py`, `app/georef.py`, `app/outage_store.py`, `app/outages_api.py`) and a versioned coverage data file, a scheduler in the FastAPI lifespan with a dedicated-connection advisory lock, and an additive migration (e.g. `0005_cu01`) for `es_outage_snapshots`, `es_outage_reports`, `es_outage_fetch_runs`. New runtime dependencies `httpx` and `json5` (pinned; D7), gated on the JSON5 fixture proof.
- **Frontend:** new `features/outages/` folder, an additive public view switch in `App.tsx`/`AppLayout.tsx` (no router) and a narrow public-POST allowlist in `lib/http.ts` for the body-carrying resolve endpoints, reusing Zustand and shadcn/Tailwind primitives. No new frontend dependency.
- **External:** ENRE feed (read-only, primary source), GeoRef `apis.datos.gob.ar/georef` (backend-only forward/reverse lookup) and the coverage catalog. GeoRef scoping and the ENRE↔GeoRef name correspondence are verified before the address/location modes ship.
- **No change** to CU02/CU09/CU10, authentication, existing schemas or deployment topology; public endpoints are added without weakening any authenticated route.

## Blockers (required before BUILD)

1. **Coverage catalog contents (D4/T2):** the mechanism is approved (versioned file with provenance and verification date), but the initial verified Edesur coverage contents and their authoritative source must be supplied; until then the API returns `coverage_unverified` and `out_of_coverage` is not shippable.
2. **GeoRef↔ENRE name mapping (D2/T1):** the backend adapter and province scoping are approved, but the exact rule mapping GeoRef `departamento`/`localidad_censal` (and CABA) to ENRE `partido`/`localidad` must be verified against real responses before the address/location modes ship.
3. **JSON5 compatibility (D7):** the captured payload is a data-only JS literal and is expected to parse with JSON5, but the parse must be proven against a redacted real fixture; on failure, stop and request approval.
4. **Unobserved ENRE categories:** `cortesPreventivos` and `cortesServicioMedia` were empty in the capture, so their populated row shape is not observed; only a populated capture can freeze the media/preventivo schema.

See [design](design.md) for the verified vs proposed contract distinction, T1–T3 coverage, the acquisition flow, the API contract and the retention/state decisions.
