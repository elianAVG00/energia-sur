# Design

Status: **PROPOSED FOR HUMAN REVIEW - NOT APPROVED FOR APPLY**. D0-D5 below are
concrete recommendations and alternatives for acceptance/revision, not installed
dependencies or silent resolutions of project TBDs. See [proposal](proposal.md)
for motivation and the two [delta capabilities](specs/interruption-diary/spec.md).

## Context

The app has a storage-free FastAPI `/health` and React health UI only. Backend
dependencies are FastAPI/Uvicorn; frontend uses React/TypeScript/Vite/npm. PostgreSQL
18.6 in Compose is approved, but backend connection, driver, ORM, migrations, auth
and PDF dependencies do not exist in the manifests. Existing Docker lint/backend
type gates are still unresolved. Preserve the technical environment and its volume.

The user accepts stage 05 and confirms teacher approval of all ten Energía Sur CUs
(Q00, on user confirmation only; no teacher date/channel recorded). U06 selects
CU09 first and approves the diary's business policies. This does not accept this
design or authorize installation, schema changes or Apply.

## Goals / Non-Goals

**Goals:** bounded own-domicile prerequisite, server-enforced account isolation,
one backend temporal/report calculation for UI and PDF, persistent records, and
real browser/API/database/export acceptance with two synthetic accounts.

**Non-Goals:** full CU04, meters, GeoRef/address verification, self-service signup/
recovery, domicile deletion/reassignment, household sharing, reopening a closed
cut by deleting its end, complaint submission, deployment, chatbot or public feeds.
Exclusions do not erase those other catalog CUs or decide their remaining questions.

## Decisions

### Confirmed constraints, not open design choices

- Q17/Q18/Q19/Q20: Buenos Aires minute recording; no future cut dates; end after
  start; only domicile's account saves/views/corrects/closes/exports; corrections
  allowed for both states; retained overlaps unioned after period clipping; nonpositive
  intersections excluded; open effective end min(generation, period end); hours/minutes.
- Q23: required fields, descending-start table and exact missing-end “En curso”.
- Authoritative rules/calculations and authorization belong in backend; provider/
  database credentials never go to the frontend. Main specs are not updated here.

### D0 - Minimum CU04 slice and domicile input [APPROVAL REQUIRED]

**Recommend:** include register/list/select own domicile in this change, alongside
CU09, rather than blocking the first diary on complete CU04 or using hidden fixture-only
addresses. Proposed payload: a required human-readable `display_address`; server
assigns stable `id` and authenticated `account_id`. Choose concrete nonempty/length
validation during contract approval; no claim of verified legal occupancy or source lookup.

**Alternatives:** separate CU04 prerequisite change (cleaner sequencing, delays this
vertical slice); pre-provisioned domiciles (less UI, but does not exercise registration).
**Decision needed:** accept the bounded registration UI/API and exact address input
contract. Q08 identity/deduplication remains open outside this narrow stable-record model.
Two accounts' address text may coincide without granting access to each other's records;
do not use matching text as authorization. No meter or domicile editing/deletion is added.

### D1 - Authentication, provisioning and authorization [APPROVAL REQUIRED]

**Recommend:** same-origin opaque server sessions, backend login/logout and server-
resolved account; cookies HttpOnly, appropriate SameSite/Secure configuration per
environment, expiry/revocation and CSRF protection for mutations. Compare:

| Option | Benefit | Cost / decision |
| --- | --- | --- |
| Opaque server session | Browser credentials stay out of JS; immediate revocation | Session store/cookie/CSRF/provisioning design required |
| Bearer JWT | Useful for non-browser consumers | Revocation, refresh and client storage increase scope |
| External OIDC | Delegated identity management | External provider/configuration and service dependency approval |

Propose controlled local development account provisioning and real credentialed
login for two synthetic accounts, not public signup/recovery or an account-switch
bypass. Password hashing library/settings, cookie/CSRF rules, session expiry,
provisioning process and dependency versions all need explicit review before code.

Apply account ownership checks to every direct record/domicile lookup, list, summary,
mutation and PDF, deriving identity from the session, never body `account_id`.
Proposed error contract: unauthenticated 401; inaccessible/missing resource uniform
404; invalid input 422. This error mapping is proposed, not a user-approved business
policy. Mandatory independent security/data-isolation review remains a future gate.

### D2 - PostgreSQL integration and migrations [APPROVAL REQUIRED]

| Option | Benefit | Cost |
| --- | --- | --- |
| SQLAlchemy + psycopg + Alembic (recommended) | Reusable relationships and repeatable additive migrations | Three unapproved components and version choices |
| psycopg + explicit SQL/versioned scripts | Smaller runtime dependency set | Manual mapping, migration sequencing and ownership-query discipline |
| Async driver/ORM stack | Potential concurrency benefits | More lifecycle complexity; no demonstrated need yet |

Recommend the first option, subject to exact versions/Windows-container compatibility
review; do not install it or modify `pyproject.toml`/`uv.lock` during proposal work.
Use backend-only environment-backed connection configuration, internal `db:5432`,
explicit transactions, bounded pool/lifecycle and controlled error translation.
Keep `/health` storage-free liveness; do not silently change its existing contract.

Proposed additive data model: account identity/credential material and sessions per
D1; domicile `(id, account_id, display_address)`; interruption `(id, domicile_id,
start_at, nullable end_at, observations, complaint_number)` with stable references.
Account checks traverse the domicile relation. No client-controlled owner, bill,
meter, photo, auto-feed, sharing or deletion table is needed for this slice.
Store timezone-aware instants and convert/display using the Buenos Aires named zone;
minute payload/storage constraints and atomic updates depend on D4 approval.
Approve database credentials provisioning deliberately: the persisted technical test
volume does not rotate its initialization password when `.env` changes.

### D3 - PDF technology and delivery [APPROVAL REQUIRED]

**Recommend:** backend ReportLab generation as an authenticated on-demand download,
not persistent report files. Its bounded table suits the requested report without
an HTML/native-renderer dependency. **Alternatives:** WeasyPrint for richer HTML/CSS
with additional runtime dependencies; browser printing with weaker reproducibility
and authorization control. Exact library/version/license, Unicode font packaging,
pagination and response/error behavior need approval before dependency or image edits.

Render server-selected authorized records, preserving observations/complaint text,
including multi-page tables and the exact “En curso” string. Escape/encode user
text safely; no external URLs/assets or provider data are fetched to build a PDF.
Use the same backend report result for rows/total; do not sum overlapping row
durations. Proposed on-demand delivery avoids unapproved storage/retention policies.

### D4 - Temporal/payload and correction-edge contract [APPROVAL REQUIRED]

Recommend the following review bundle; these mechanics are not additional approved
catalog requirements until accepted:

- Named zone `America/Argentina/Buenos_Aires`; minute-level ISO input, reject seconds/
  fractions instead of silently rounding user records. Alternative: normalize them
  with disclosed rules. Never infer a fixed offset for all historical/future dates.
- Capture trusted backend `now` once per request and floor its reporting value to
  a minute; inject it in tests. Never let callers supply an authoritative clock.
- Query endpoints use minute boundaries with start strictly before end; allow a
  future **query** end, since only future **cut** dates are prohibited. Reject
  reversed/empty periods. No arbitrary reporting-period limit is approved here.
- Compute each segment from max(cut start, period start) to min(cut end or captured
  generation, period end); exclude end <= start; union sorted segments per domicile;
  accumulate integer minutes and render quotient/remainder hours/minutes.
- Correction updates fields atomically; an invalid request leaves the record intact.
  Recommend preserving state when correcting closed cuts, so clearing an existing
  end/reassigning domicile is unsupported unless separately approved. This does
  not restrict the approved corrections to dates/text within the existing lifecycle.
- Choose optimistic-conflict detection versus last-writer-wins before mutation
  contract approval. A PDF/report uses one consistent read and one generation instant;
  separate requests may legitimately differ for ongoing cuts.

These choices resolve API/time/lifecycle edge ambiguities for human review now,
not in a deferred “Open Questions” list after implementation has started.

### D5 - Transport/UI/testing contracts [APPROVAL REQUIRED]

Proposed route family (not existing endpoints): `GET/POST /domiciles`,
`GET/POST /domiciles/{id}/interruptions`, `PATCH /interruptions/{id}`,
`POST /interruptions/{id}/close`, `GET /domiciles/{id}/summary` and
`GET /domiciles/{id}/report.pdf`; D1 supplies login/logout/session endpoints.
Approve typed payloads, text limits, period fields, errors and auth integration
before endpoint implementation. No contract field name is silently fixed by this draft.

React handles login, domicile registration/selection, diary form/list/corrections/
closure, period summary and download; no authoritative owner/date/union logic in UI.
Keep route handlers focused on transport and reuse a small backend business module
for validation and reporting, with database and PDF I/O separate; no generic new
dependency-injection framework or architecture rewrite is proposed.

Use existing standard-library/Node tests where appropriate; obtain approval for
any integration/browser/lint/type framework or added test dependency. Browser checks
must render real UI against FastAPI/PostgreSQL and download/open the actual PDF;
mock-only or health-only evidence is insufficient. See [tasks](tasks.md).

## Traceability

Authority: [U05/U06 register](../../../docs/use-cases/decisions.md) and
[CU09 fiche](../../../docs/use-cases/cu09.md); all original CU09 scenario IDs are
preserved across the deltas, not counted twice as independently working tests.

| Proposed capability / requirement | Scenario IDs | Catalog rules / decision source |
| --- | --- | --- |
| account-domiciles: registration/list/selection | AD-S01/AD-S02 | CU04 prerequisite, proposal scope and D0; detailed contract pending review |
| account-domiciles: mandatory own domicile | CU09-S03 | CU09-R3 / Q18, U05 + U06 |
| interruption-diary: five owner-only operations | CU09-S09 | CU09-R3/R8 / Q18, U06 |
| interruption-diary: stored closed/ongoing records | CU09-S01/S02 | CU09-R1/R3 / P, U05 + U06 |
| interruption-diary: minute/date validation | CU09-S10 | CU09-R7 / Q17, U06 |
| interruption-diary: correction/closure | CU09-S11/S12 | CU09-R7/R8 / Q17/Q18, U06 |
| interruption-diary: positive period intersection | CU09-S05/S13 | CU09-R5 / Q20, U05 + U06 |
| interruption-diary: ongoing effective end | CU09-S07/S08 | CU09-R5 / Q20, U05 + U06 |
| interruption-diary: retained overlap union/units | CU09-S04/S14 | CU09-R4/R5/R7 / Q17/Q19/Q20, U05 + U06 |
| interruption-diary: PDF fields/order/ongoing text | CU09-S06/S15 | CU09-R2/R6 / Q23, U05 + U06 |

Authentication/error contracts, exact domicile payload, temporal normalization,
persistence and PDF technology remain D0-D5 approval items, not silently accepted
library or schema choices in the deltas. No full CU04, sharing, deletion or reopening.

## Risks / Trade-offs

- [Cross-account direct-ID/PDF leak] -> server-side checks on every path, two-account
  negative acceptance and mandatory independent review before implementation closure.
- [Scope growth into all CU04/auth account management] -> D0/D1 bounded contracts and exclusions.
- [Clock drift/union inconsistency] -> trusted captured clock, minute arithmetic,
  reusable report result, regression fixtures CU09-S04/S05/S07/S08/S13/S14/S15.
- [New dependencies or native rendering fail in Windows/Docker] -> approve versions,
  test locked builds and font packaging before accepting the implementation.
- [Lost optional text/multipage PDF rows] -> long-text/multipage synthetic fixtures
  and real downloaded PDF inspection, not filename/MIME assertions alone.
- [Existing lint/backend-type gaps] -> explicit tooling decision and real checks;
  no weakening tests or closing inherited gates by assumption.

## Migration Plan

After design acceptance and separate Apply authorization: create reviewed additive
business migrations, test on an approved disposable/synthetic database, then run
against intended local development configuration with retained data. Never delete
`pgdata`, overwrite credentials or reuse technical fixtures as real user data.
Prefer forward correction; rollback procedure must be reviewed for data preservation.
Destructive down migrations/data deletion require separate explicit permission.
No migration, account provisioning, service change, installation or deployment runs now.

## Open Questions

Only deferrable cosmetic choices: table styling and tie ordering for identical start
times, within the approved descending-start rule. Material decisions are D0-D5 and
must be accepted/revised before Apply, not silently postponed until coding.
