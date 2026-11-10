# CU02 fixtures provenance

- `enre_data_eds_scheduled.js` — byte-faithful copy of the live ENRE Edesur payload
  (`GET https://www.enre.gov.ar/paginacorte/js/data_EDS.js`) captured on
  2026-11-10 at 11:08 ART. It contains four `cortesProgramados` rows, all with
  `normalizacion: 'Sin datos'`, and an empty `cortesComunicados`. No personal data.
- `enre_data_eds_scheduled_dated.js` — excerpt of the archived ENRE Edesur payload
  from 2026-01-14 (Wayback Machine capture `20260114162420`) reproducing the single
  `cortesProgramados` row verbatim, whose `normalizacion` is the full date-time
  `2026-01-14 15:33`. Unrelated collections and totals were not observed in the
  excerpt and are omitted; the fixture is labelled as an excerpt, not a full payload.

`cortesComunicados` has never been observed populated (2019-2026), so no synthetic
populated fixture is committed. Parser tests that need a non-empty collection build
it inline and only assert that it is counted and never emitted.
