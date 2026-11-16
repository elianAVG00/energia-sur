# Proposal

## Why

CU01 and CU02 currently build their area selectors from separate ENRE snapshots plus a partial file-based coverage seed, so available options differ and disappear when a snapshot has no corresponding rows. A shared PostgreSQL catalog sourced from the approved Edesur concession list and GeoRef's official locality data will make the selectors stable while keeping reported outages and works exclusively snapshot-backed.

## What Changes

- Add a persistent, idempotently seeded territorial catalog for the twelve approved Buenos Aires partidos and GeoRef `/localidades` records associated with them; exclude CABA/CAPITAL entirely from both selectors.
- Preserve GeoRef identifiers and categories, deduplicate equal displayed names within a partido, retain same-name localities across different partidos, and review unusual records before deciding whether they are useful selector entries.
- Store verified ENRE-to-GeoRef name equivalences separately from canonical labels; retain original ENRE text for reported records and document observed names that cannot be resolved without inventing equivalences.
- Make CU01 and CU02 area endpoints read the same catalog, independently of their snapshots. Keep ENRE snapshots and existing query behavior for outages and scheduled works.
- Preserve address search, device geolocation, and party/locality filtering using canonical IDs and verified aliases. Clarify empty-result copy so it describes the latest available report and never guarantees uninterrupted supply.
- Add migration, idempotent seed, normalization/equivalence and endpoint/UI regression coverage, including empty snapshots and identical CU01/CU02 selector zones.

## Capabilities

### New Capabilities

- `territorial-catalog`: Shared official party/locality catalog and verified source-name equivalences used by public territorial selectors.

### Modified Capabilities

- `current-outages`: The CU01 area selector SHALL use the shared persistent territorial catalog, exclude CABA/CAPITAL, and remain available without outage rows; party/locality matching, geographic resolution and empty-result wording SHALL preserve uncertainty.
- `scheduled-works`: The CU02 area selector SHALL use the same persistent catalog as CU01, exclude CABA/CAPITAL, and remain available without scheduled-work rows; party/locality matching, geographic resolution and empty-result wording SHALL preserve uncertainty.

## Impact

- Backend persistence and API: `backend/migrations/versions/`, `backend/app/models.py`, `backend/app/coverage.py`, `backend/app/outages_api.py`, `backend/app/scheduled_api.py`, `backend/app/georef.py`, and potentially the ENRE normalizers/stores.
- Frontend API contracts and selector/result copy: `frontend/src/features/outages/` and `frontend/src/features/scheduled-works/`.
- Tests: `backend/tests/test_cu01_territory.py`, `backend/tests/test_cu02_scheduled_works.py`, relevant API tests, and corresponding frontend tests.
- No new dependencies or change to ENRE refresh/query behavior. The official GeoRef v2.1 endpoint and the ENRE 2023 Edesur audit are the territorial data sources; locality existence in GeoRef SHALL NOT imply Edesur service at that locality.
