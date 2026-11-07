# Proposal

## Why

CU09 is the user's selected first stage 06 development: neighbors need a private
interruption diary and a PDF supporting a complaint. The stage 05 documentary
baseline is accepted and Q00 satisfied on user confirmation; the app currently
implements only technical health checks, not accounts, domiciles or diary behavior.

## What Changes

- Propose CU09 save/view/correct/close/export for only the account with the registered
  domicile, including correction of open and closed cuts under the same validation.
- Include only CU04's prerequisite: register, list and select an own-account domicile
  with stable identity/display address; no meter or full CU04 lifecycle is required.
- Use Buenos Aires minute-resolution cut times, reject future dates and require end
  after start. Keep ongoing cuts; summary generation never closes them implicitly.
- Summarize positive intersections with a queried period, union overlaps per domicile,
  cap ongoing ends at min(generation, period end), and display total hours/minutes.
- Export the approved PDF content in a start-descending table; absent end is “En curso”.
- Preserve all existing catalog scenario IDs; convert approved rules into draft
  implementation delta contracts without promoting them into current main specs.

Authority: [U05/U06 register](../../../docs/use-cases/decisions.md),
[CU09 fiche](../../../docs/use-cases/cu09.md), and [accepted workflow](../../../docs/openspec-workflow.md).
Auth/provisioning, persistence, minimal domicile input and PDF decisions in
[design](design.md) require explicit approval. This request authorizes proposal
artifacts only, not implementation, dependencies, Apply, Sync or Archive.

## Capabilities

### New Capabilities

- `account-domiciles`: bounded CU04 own-account domicile registration/list/selection
  prerequisite for CU09, not full address/meter management.
- `interruption-diary`: CU09 private record lifecycle, temporal validation, summaries
  and downloadable complaint-support PDF.

### Modified Capabilities

None. `openspec list --specs --json` reports zero main specifications.

## Impact

Future accepted implementation affects React UI, FastAPI transport/business logic,
PostgreSQL business schema/connection, dependency manifests/locks, tests and setup
documentation. No implementation or runtime change is made in this proposal.

Excluded: meters, readings/bills, complete CU04 editing/deletion, household sharing,
domicile reassignment, destructive migration, self-service account recovery, public
feeds, chatbot, hosting/deployment and actual complaint submission. Account provisioning
is a necessary design decision, not an already-approved signup feature. Existing
Docker lint/backend-type gates remain unresolved. Independent auth/data-isolation
review and real browser/backend/database/PDF acceptance are required before future closure.
