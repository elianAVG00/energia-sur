# CU09 interruption diary - stage 06 engineering record

Status: **VERIFIED AND ARCHIVED 2026-11-08; MAIN SPECS SYNCHRONIZED**.
Updated 2026-11-07. U07 accepts the recommended proposal/design and requests Apply;
U07-T explicitly approves the technical package in the [contract](../../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/contract.md).
Links: [proposal](../../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/proposal.md),
[design](../../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/design.md),
[tasks](../../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/tasks.md),
[domicile delta](../../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/specs/account-domiciles/spec.md),
[diary delta](../../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/specs/interruption-diary/spec.md).

## Apply checkpoint and actual implementation

### Closure decision and final verification - 2026-11-08

**Archive result:** synchronized `account-domiciles` and `interruption-diary` to
`openspec/specs/`, verified exact Purpose/requirement/scenario content, then moved
this change to [archive/2026-11-08-record-cu09-interruption-diary](../../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/).
The separately approved foundation was synchronized and archived too. No commit
or push was performed by this closure operation. Post-move strict OpenSpec
validation passed 6/6 current items and archived validation passed 2/2 changes;
307 relative documentation/spec targets resolved and both diff checks passed.

The user explicitly approved closure and synchronization/archive of this change
and the frontend foundation subject to final repository checks. No commit, push,
new change or data cleanup was authorized. Independent reviewer
`ses_e4a277d40ffeKFk0IOVunZlbV5` classified out-of-band pre-1970 rows as a low,
nonblocking robustness risk for this accepted API scope: such rows can make listing
return 500 or reports 422. The NUL-input 503 concern is a low, unverified hypothesis,
not a confirmed failure or a change to the 422 contract. Neither is claimed fixed;
retain both for future triage rather than silently changing requirements. The copied
registry-config concern was resolved by a secret-free primary inspection.

The full independent review covered every owner-bound operation; the U09 focused
recheck `ses_e48c2222cffebM8WOEV9Jfbiux` resolved M1. The primary verified current
code against the retained verification images byte-for-byte: backend 20 files
SHA256 `e785e8aa54f3dee5cf26ef446448dd05a54a57a682ce75734a2e527a0627c78b`;
frontend 41 files SHA256 `f30d340d479a1c46b0e5f419b16879a6c543ee2fe9e05fdf2c26e56addb01ce9`.
The retained logs confirm 66 backend tests, 50 frontend tests, one 7.7s real-browser
workflow and actual PDF inspection. U09 regressions cover absent/untrusted login
Origin and missing/invalid CSRF for every protected mutation. Strict OpenSpec4/4
and unstaged/staged `git diff --check` passed before synchronization. The current
checkout was clean at entry on `main`, HEAD `ce88194`, ahead of origin by two commits;
those human commits are preserved. Task 8.3 is reconciled based on the review,
clarification, regression evidence and explicit nonblocking classification above.

### Foundation adoption regression checkpoint

U10 authorized the separate shared-frontend implementation. CU09 now uses its
Tailwind/local shadcn shell, memory-only Zustand session/selection, RHF/Zod forms
and centralized cookie/CSRF-safe Axios adapter; backend behavior/contracts remain
unchanged. Actual final rerun PASS: 66 backend tests (14 PostgreSQL, zero skips,
10.397s), 50 frontend tests/types/build/lint, exactly one Chromium workflow7.7s,
actual PDF text/content and migration/restart persistence. New assertions cover
one unavailable chat mount/no chat requests and narrow viewport containment.
See [foundation evidence](establish-frontend-foundation.md) for commands, review,
corrections and limitations. Latest log `Temp/opencode/foundation-acceptance.log`;
retained DBs `cu09_app_6fde6167e31f` / `cu09_test_6fde6167e31f`, QA container
`energia-sur-cu09-qa-6fde6167e31f`. No repeat browser run, DB deletion or Archive.
Earlier registry-config review limitation is resolved: primary inspected the copied
config for credential-related entries and found none, logging no values. Out-of-band
stored-row/NUL low residuals remain explicit for final CU09 review, not silently waived.

### U09 - Approved clarification verified (current checkpoint)

The user explicitly approved Origin-only login and Origin plus session-bound CSRF
on authenticated unsafe operations. Updated `contract.md` detail wording/route
table, design and security delta scenarios. This aligns the approved policy with
the existing backend rather than changing endpoint behavior; it resolves M1 below.
The remaining older M1-blocker prose is historical to the preceding review.

Added real PostgreSQL/ASGI tests for absent/null/malformed/foreign login Origin,
no session issuance on rejection, trusted login without pre-auth CSRF, and missing,
wrong and non-ASCII CSRF on every authenticated write (logout, domicile creation,
cut creation/correction/closure). Each rejection checks unchanged records/versions,
domiciles and live session. No production backend or frontend code needed changing.
This is a bounded accepted-contract alignment/regression update in the existing
change, not a new feature or a silent security-policy decision.

| Check | Mandatory? | Actual result / evidence |
| --- | --- | --- |
| Locked backend verification build | Yes | PASS: `docker build --target verification -t energia-sur-backend-checks:cu09 backend`. |
| Backend tests and live acceptance | Yes | PASS: `pwsh -NoProfile -File scripts/Test-Cu09Acceptance.ps1`, exit 0; 66 backend tests, 14 real PostgreSQL/ASGI, zero skips, 9.720s. |
| Quick real-browser CU09/PDF | Yes | PASS: exactly one Chromium workflow, 4.9s; actual PDF downloads/text, two accounts/ownership/409, migration/restart identity/value checks. No additional browser run. |
| Backend lint | Yes | PASS: `docker run --rm energia-sur-backend-checks:cu09 ruff check --no-cache app tests migrations`. |
| Independent M1 recheck | Yes | PASS: separate read-only reviewer session `ses_e48c2222cffebM8WOEV9Jfbiux` confirms contract/table/spec/code alignment and all-route regression coverage, no focused findings. Runtime executed by primary only. |
| OpenSpec/documentary validation | Yes | PASS: strict noninteractive validation 4/4 active changes; `git diff --check` exit 0; 100 relevant relative Markdown targets resolve; STATE 40 lines. |
| Broader unrelated frontend/backend gates | No new runtime code | Earlier mypy/Oxlint/Node/TS/build/lock-drift results retained below; the update only adds backend regressions and documents existing behavior. |

Latest actual log: user-local `Temp/opencode/cu09-security-u09.log`; retained QA
container `energia-sur-cu09-qa-a0290c0f7601`; synthetic databases
`cu09_app_a0290c0f7601` / `cu09_test_a0290c0f7601`. Original DB container remains;
no data/volume deletion. Current app uses this synthetic acceptance database.

The earlier full independent audit remains recorded below; U09 focused recheck
resolves its Medium M1. Low out-of-band-row/NUL hypotheses and registry-config
review limitation remain explicit final review items. Task 8.3 stays open for their
disposition. User requests review before Archive/commit/push; none performed.
The separate frontend foundation is planning-only and must not inherit these
runtime passes as proof of its future CU09 adaptation.

### Post-restart review and latest verification

The user approved the changes, then requested the lost independent review be
rerun after restarting OpenCode. A fresh foreground read-only reviewer completed
in session `ses_e4a277d40ffeKFk0IOVunZlbV5`, including a follow-up audit of every
owner-bound operation (login/session/logout, domiciles, list/create/correct/close,
summary and PDF), ownership helpers, CSRF/Origin, errors, provisioning and migration.
No critical/high security or data-isolation defect was found. This is separate
source review, not independently executed tests.

**BLOCKED M1 (Medium):** contract detail-package wording requires a CSRF token
on every unsafe request including login, but its route table and implementation
require only an allowed Origin on login. Authenticated mutations use both checks.
No bypass was found, but the approved security contract is internally inconsistent.
Human decision is required: explicitly approve Origin-only login plus CSRF on
authenticated mutations, or approve/design pre-authentication CSRF tokens. Neither
the earlier general approval nor this source review silently changes that policy.
Task 8.3 and implementation closure remain open.

Reviewer documentary findings were corrected in README, Q20/Q23, catalog counts,
proposal/design wording, and the operational/task snapshots. Additional tests now
cover aware-offset exact-floor acceptance, exact-floor correction/PDF, near-floor
closure and non-echoed validation detail. Latest full script execution PASS, exit 0:
64 backend tests including 12 real PostgreSQL/ASGI tests, zero skips, **9.403s**;
real Chromium workflow **6.8s**; downloaded PDF inspection, migration rerun with
data, restart field/identity persistence, and original db container preservation.
Ruff and Oxlint were rerun and PASS (Oxlint zero warnings/errors, 14 files/96 rules).
Latest log: user-local `Temp/opencode/cu09-acceptance-review.log`; retained synthetic
databases `cu09_app_7242b1a690fc` / `cu09_test_7242b1a690fc`, QA container
`energia-sur-cu09-qa-7242b1a690fc`. Earlier timings below identify preceding runs.

One cached backend image export failed because Docker lacked a parent snapshot.
A `--no-cache` rebuild succeeded without deleting images, data, or volumes.

Low residuals recorded, not silently waived: pre-1970 rows inserted outside the
accepted API can cause list 500/report 422; NUL text could yield 503 (review
hypothesis, not runtime-confirmed); the reviewer could not inspect registry
configuration for credentials. No legacy production data, new DB constraint,
data cleanup, migration change, or permission expansion is claimed. These need
explicit disposition before closure. Prior user approval is recorded, but no
Sync/Archive/commit/push/deployment is authorized or performed.

Apply entry: clean `main`, ahead 1, HEAD `f76bc0f06b24666ff7852010142baf218dc8eed4`
(`docs: close stage 05`). All implementation changes remain uncommitted. No reset,
commit, push, Sync, Archive, deployment or data/volume deletion was performed.
Q00 remains satisfied solely by the user's teacher-approval confirmation; no teacher
date/channel is recorded. Stage 05 remains documentarily closed, not reopened here.

Implemented: owned domicile registration/list/selection without meters; controlled
local account provisioning and credentialed login/logout; scrypt, opaque eight-hour
sessions, HttpOnly/SameSite cookies, CSRF/Origin boundary; owned cut creation/list,
atomic correction/closure with optimistic 409; shared backend period clipping,
ongoing caps and overlap union; Unicode on-demand authenticated PDFs; React UI,
typed DTO validation/cancellation and error/conflict recovery. `/health` is unchanged
storage-free liveness. Full CU04, chatbot, hosting and other CUs remain excluded.

Actual tools/agents: primary OpenCode reads/searches/patches/PowerShell/Docker/OpenSpec;
Apply, FastAPI endpoint and quality-gate procedures; Context7 public library docs
(including React form reset and Playwright role/label selection on resumption).
Backend domain delegate delivered calculations/tests. Backend/frontend integration
delegates encountered `subscription_sharing_usage_limit_exceeded`; primary continued,
not counted as successful QA/review. Later separate read-only QA and reviewer agents
did inspect source. Their permissions prohibit runtime execution and secret/external
file access; primary executed all runtime checks. No permission changes were made.

### Verification evidence - Apply, primary runner, repository root

All commands below actually ran on 2026-11-07. Successful commands exited 0.
Host-local logs/artifacts are intentionally outside shared files and contain only
synthetic acceptance data; never print QA container environments or credential inputs.

| Check / criterion | Mandatory? | Command or method | Result / evidence / limitation |
| --- | --- | --- | --- |
| Locked verification images | Yes | `docker build --target verification -t energia-sur-backend-checks:cu09 backend`; corresponding frontend build | PASS: uv locked install and npm ci; runtime pins preserved. Latest frontend build log: user-local `Temp/opencode/cu09-frontend-oxlint-build.log`. |
| Domain/API/security/PDF/health tests | Yes | `pwsh -NoProfile -File scripts/Test-Cu09Acceptance.ps1` invokes actual migrated PostgreSQL/ASGI tests | PASS: 64 tests, including all 12 PostgreSQL tests; zero skips, 9.403s on the post-review rerun with expanded floor/offset/correction/PDF assertions. Synthetic nonprivileged role and distinct app/test databases. |
| Real rendered UI/API/database acceptance | Yes | Same script; real Chromium via Playwright 1.65.0, one comprehensive workflow | PASS: 1 test, 6.8s on the latest rerun. Register/select, create overlapping/open cuts, summary, correction/closure, actual second writer/409/discard/retry, same-version editor reset, future rejection, two populated accounts and reciprocal domicile lists, foreign-ID denials/unchanged owner records, empty/excluded summaries, domicile draft reset, logout. No response mocks. |
| Actual downloaded PDF | Yes | Same script extracts browser-downloaded `closed.pdf`/`ongoing.pdf` with pypdf | PASS: Unicode, optional text/complaint, complete period, both retained rows in descending order, closed statuses, two ongoing end/status cells, exact 3h/13h totals. |
| Migration/persistence | Yes | Same script reruns Alembic head with existing synthetic diary, restarts backend, authenticates and rereads | PASS: two domiciles and three cuts retain IDs, every date/text/status/version field; existing original db container ID unchanged. Cluster volume receives additive synthetic databases, not a claim of byte-for-byte unchanged volume. |
| Backend lint | Yes | `docker run --rm energia-sur-backend-checks:cu09 ruff check --no-cache app tests migrations` | PASS, Ruff 0.17.4. |
| Backend strict types | Yes | `docker run --rm energia-sur-backend-checks:cu09 mypy --cache-dir /tmp/mypy-cache app` | PASS, mypy 2.4.1, 10 app modules. |
| Frontend helper tests | Yes | `docker run --rm energia-sur-frontend-checks:cu09 npm test` | PASS: 32 tests, zero skips. Injected-fetch tests are not browser acceptance. |
| Frontend strict types/build | Yes | `docker run --rm energia-sur-frontend-checks:cu09 npm run build`; also verification image RUN | PASS: tsc includes source, tests, E2E and configs; Vite production build. |
| Lock drift rejection | Yes | `pwsh -NoProfile -File scripts/Test-Lockfiles.ps1` with nonsecret placeholder POSTGRES_PASSWORD only for Compose interpolation | PASS: uv/npm reject manifest drift without changing locks. First attempt BLOCKED by missing Compose variable; no db started/recreated by this check. |
| PDF visual inspection | Yes | Primary opened synthetic `closed.pdf` and generated three-page `long.pdf` with read/PDF renderer | PASS: readable Spanish accents, wrapped long address/text, preserved columns/rows and repeated headers, no observed overlap/clipping. Row continuation can repeat a header within a page; cosmetic only. No universal glyph-coverage claim. |
| Independent auth/isolation review | Yes | Separate read-only reviewer inspected every owner-bound route, sessions/CSRF/errors, frontend, migrations and direct dependencies | Review completed in `ses_e4a277d40ffeKFk0IOVunZlbV5`: no critical/high isolation defect, but M1 security-contract inconsistency BLOCKS closure; see post-restart checkpoint above. Not reviewer-executed runtime tests. |
| Frontend lint | Yes | `docker run --rm energia-sur-frontend-checks:cu09 npm run lint` (Oxlint 1.92.0, also in verification-image build) | PASS: 0 warnings and 0 errors on 14 files with 96 rules; TypeScript 7.0.2 preserved. Stable typescript-eslint 8.72.1 still excludes TS 7, so U08 approved this pinned alternative. |
| Historical date floor | Yes | Domain/API regressions plus Python offset probe in the backend image | PASS: 1970-01-01 00:00 Buenos Aires is inclusive and round-trips exactly; 1969-12-31 23:59 and equivalent instants return sanitized 422 on save/correct/close/summary/PDF; hourly probe 1970-2026 found zero fractional offsets. |
| Full CU04/chatbot/deployment | No | Scope comparison with accepted proposal | NOT APPLICABLE to this bounded change; no claim of implementing the other CUs. |

Latest successful pipeline evidence: user-local `Temp/opencode/cu09-acceptance-review.log`;
the preceding run is `Temp/opencode/cu09-acceptance-floor.log`, plus the earlier
`cu09-acceptance-run.log` and `cu09-acceptance-final.log`; latest retained QA
container `energia-sur-cu09-qa-7a8d1ccebe8f`; synthetic databases
`cu09_app_7a8d1ccebe8f` / `cu09_test_7a8d1ccebe8f`; PDF/state artifacts under
`Temp/opencode/cu09-acceptance/`. Previous synthetic resources are retained too.
The running app uses that synthetic acceptance database, not real user data.

### Observed problems and correction evidence

- Frontend lock generation initially hit bind-mount EACCES; generated the lock in
  container temporary storage from the reviewed manifest, then copied it back.
  Backend Docker allowlist initially omitted new modules/migrations; corrected it.
- Ruff cache lacked nonroot write permission; used `--no-cache`, then corrected
  actual import-order findings. Ruff and strict mypy pass; gates were not suppressed.
- Native browser fetch was called with the client as receiver. Wrapped the default
  fetch adapter and added a regression; Vite initially served cached old code on
  the Windows mount. Restarting frontend confirmed the wrapper and original browser
  flow passed in 4.3s. This is resolved, not a current connectivity blocker.
- Reviewer found extreme-date overflow, lax numeric date coercion, stale 409 editor
  snapshots and cross-domicile drafts. Guarded timezone conversions, raw ISO
  validators, explicit discard/reload and domicile-scoped form identity address them;
  API invalid-mutation snapshots and rendered two-writer regressions were added.
- Reviewer then found same-version discard retaining local state. Form keys now
  always include reset revision, and opening another editor clears obsolete conflict
  state. Rendered reopening checks the persisted text replaces the draft.
- Expanded browser conflict check failed before and after that key correction.
  Artifact showed the reloaded form actually contained the expected text. Minimal
  Chromium reproducer proved wrapped-label getByLabel exact count 0 versus accessible
  textbox role count 1 when textarea initial content is present. Replaced only that
  selector, retaining the exact value assertion; full workflow now passes.
- First pipeline reaching restart failed its domicile count because PowerShell
  wrapped Invoke-RestMethod's JSON array as a nested one-item array. Assign first,
  normalize at count use; rerun passed full identity/value comparisons. A further
  expanded empty/excluded-summary and populated-account browser run also passed.
- QA initially identified missing persisted invalid/foreign mutation snapshots,
  report nonclosure, fixed-clock PDFs, both populated accounts, download row/status
  assertions, migration-with-data and post-restart values. Added and ran those
  checks. QA then asked for explicit persisted-field assertions after successful
  open/closed corrections; those assertions were added and the full pipeline reran
  green (64 tests, 9.068s; browser 4.9s) after the date-floor boundary test joined
  the same suite. Final QA/reviewer reconciliation confirmed the tested 2026
  scenarios/AD paths and the corrected findings, with no remaining critical/high
  isolation defect. That reconciliation remains source review, not independently
  executed runtime evidence.

### Resolved historical-date defect (U08 floor)

The earlier probes showed that Buenos Aires 1890 serialized with a truncated
`-03:53` offset and a 1920 interval crossing a historical offset change produced
fractional elapsed minutes and 422. U08 resolved the policy explicitly: supplied cut
and report-period times before **1970-01-01 00:00 Buenos Aires** now return a
sanitized 422, while that exact boundary is accepted. From 1970 onward offsets are
whole minutes, verified hourly through 2026, so no approximate transport, silent
narrowing of modern dates, or invented rounding is used. The fractional-minute guard
remains as defense in depth.

### Resolved frontend lint gate (U08 Oxlint)

U08 approved pinned Oxlint 1.92.0 after confirming the latest stable typescript-eslint
8.72.1 still caps TypeScript at `<6.1.0`. The verification image now runs `npm run
lint`; the gate reports zero warnings/errors and the approved TypeScript 7.0.2 is
unchanged.
The former date/lint blockers are resolved. No completion/Archive until M1 and the
recorded residual dispositions are resolved and independently rechecked.

## Proposal-phase history (before U07; not current authorization)

The sections below preserve actual proposal-stage evidence and failures. Their
pending-approval/zero-code statements describe that earlier phase only; the Apply
checkpoint and accepted contract above supersede them for current work.

## Goal, authority and existing state

The current user accepts stage 05's documentary baseline, selects CU09 first for
stage 06, approves its remaining stated business policies and requests OpenSpec
proposal/design review before any Apply. [U06 evidence](../use-cases/decisions.md#u06---baseline-acceptance-and-cu09-proposal-authorization)
records the message and Q00 approval on the user's teacher-approval confirmation.
Teacher date/channel are not recorded. No external teacher evidence is fabricated.

Entry checkout: `main` tracking `origin/main`, HEAD
`96192587c03bd0897637ba238a0285b5f1588581`; two unstaged tracked edits and 17 untracked
files from earlier documentary work. They were retained, never reset/staged.
AGENTS and the supplied stage context plus both old change trees are protected by
an eleven-file aggregate SHA256 baseline:
`460F6796861AF633A1F8C1C0C16621D4A8444AA2872AB9FBA5AAD852981DBD0C`.

Actual app/manifests inspected: React health UI and FastAPI storage-free `/health`;
FastAPI/Uvicorn only backend dependencies, no auth/database/PDF integration. Existing
frontend type/build/Node-test and backend standard-library test setup were inspected;
lockfile headers/configs and empty CI directory checked. No runtime check rerun here.

## Actual workflow, agents and tools

- Primary OpenCode used read/glob/grep, patch, permitted git/PowerShell and installed
  OpenSpec 1.16.1. Loaded `openspec-propose` and `quality-gate` skills. No generated
  skill/agent/MCP permissions edited and no tooling installed.
- Verified initialized nearest local root with `openspec list --json` and
  `openspec context --json`; verified schema `spec-driven` and supported CLI help.
  Updated stale project context to Q00 approved and CU09 selected from U06.
- Ran `openspec new change record-cu09-interruption-diary`, then followed `status`
  dependency ordering and `instructions` for proposal, specs, design and tasks.
  Verified resolved paths remain in the new non-symlink change tree. Read each
  dependency before drafting its dependent artifact. No main spec was changed.
- `spec-analyst` was verified/called in read-only mode for bounded CU04/auth/data/PDF
  scope analysis and a follow-up review of the artifacts. It produced recommendations,
  not edits, teacher evidence, CLI results or independent implementation security approval.
- Context7 returned public OpenSpec workflow/schema documentation through the
  existing external development server in OpenCode; only library questions were
  transferred, no project records/secrets. Installed CLI output governed local paths.

## Decisions, risks and review gates

- U06 closes stage 05 and resolves Q00/Q17/Q18/Q20 within scope; Q19 retained.
  Q23 approved content/order/ongoing text, but generation technology remains pending.
- Chosen implementation target CU09 needs bounded CU04 domicile registration/list/
  selection, not meters, GeoRef, full CU04 editing/deletion or a completed second CU.
- D0-D5 explicitly propose alternatives/recommendations for domicile contract,
  auth/provisioning, PostgreSQL driver/ORM/migrations/connection, PDF library/delivery,
  temporal payload/clock/concurrency edges and API/test contracts. User review is
  required; no recommendation is recorded as an approved stack dependency.
- All implementation tasks remain unchecked, with design acceptance and a separate
  Apply request first. Auth/isolation requires independent review before future
  closure, plus real browser/API/PostgreSQL/PDF evidence. Historical Docker lint/
  backend-type blockers remain unresolved; no waived or invented functional PASS.
- Read-only analyst review found one concrete oracle gap: CU09-S08 did not state
  the report period start. Corrected both fiche and delta to 2026-11-01 00:00 through
  2026-11-02 00:00, fixed generation 2026-11-02 03:00 and expected 2 h 0 min.
  This is one documentary correction, not a failed runtime test or business-rule change.
- First post-draft strict structural check: **FAIL**, exit 1, 2/3 changes passed;
  CU09's two delta files had unsupported top-level `## Traceability` sections,
  warned as not carried into main specs by Archive. Moved trace mapping and design
  caveats to design.md, retaining requirements/scenario IDs and strict validation.
  One structural correction-and-rerun cycle; no Archive or weakened gate.

## Verification evidence

Root commands/methods below are run by the primary. PASS means observed preparation
checks, not implementation acceptance. Successful CLI/assertion commands exit 0.

| Check | Mandatory? | Command/method | Result / limitation |
| --- | --- | --- | --- |
| Initial checkout/root/context | Yes | Git status/HEAD, OpenSpec list/context, local instruction reads | PASS: initialized local root, baseline above; unrelated local work preserved. |
| Structural baseline | Yes | `openspec validate --all --strict` before creating CU09 change | PASS: 2/2 old changes, zero main specs, no prior failure; MCP skip_specs INFO. |
| New planning artifact discovery | Yes | `openspec status --change record-cu09-interruption-diary --json` and four artifact `instructions` calls | PASS: all 4 artifact types done, 2 spec files; current context/Q00/selection and 2 rules injected per artifact (8 rules). Tasks 0/24. Done means existence, not accepted design or implemented tasks. |
| Final structural validation | Yes | `openspec validate --all --strict` | PASS, exit 0 after one correction: MCP, Docker and CU09 changes, 3/3, zero main specs. CU09 contains 2 delta specs/10 requirements/18 scenarios including the supplementary pre-1970 floor case. MCP skip_specs INFO unchanged; no existing change failed. Not catalog prose or working-CU validation. |
| Documentary IDs/traces/states | Yes | PowerShell index/fiche/scenario/register/trace checks plus content review | PASS, exit 0: 10 IDs/fiches, 44 globally unique traced Given/When/Then catalog scenarios; all 15 CU09 IDs mapped once in deltas, plus AD-S01/AD-S02; 24 questions (6 approved/6 partial/12 open). Q00 approved/stage 05 closed/CU09 selected, unrelated TBDs retained. |
| Links/anchors | Yes | Resolve relative Markdown targets and heading anchors in current stage docs/new artifacts/root index | PASS, exit 0: 260 destinations/160 anchors across 25 Markdown files; no recursive audit of unrelated historical targets. |
| Whitespace/scope/preservation | Yes | `git diff --check`, `git diff --cached --check`, full new-file scan, allowed paths and eleven-file hash comparison | PASS, exit 0: 27 checkout paths (3 tracked, zero staged, 24 untracked); STATE 36 lines/5 actions. Eleven preserved hashes match, main/HEAD unchanged. No source/manifests/old-change/main-spec/AGENTS edits. Informational LF-to-CRLF warnings only. |
| Runtime/tests/build/security acceptance | No for proposal | NOT APPLICABLE: no implementation or dependency/runtime changes | Future checks remain mandatory tasks, not passes from structural validation. |
| CU09 design acceptance / Apply request | Yes before implementation | Explicit subsequent user acceptance/authorization | BLOCKED pending review, intentionally not required to close accepted stage 05. |

## Current checkpoint

Final measured counts are above. Analyst approval/scope contrast passed except the
stated S08 period-start oracle gap; primary corrected/rechecked it. Targeted analyst
recheck **PASS**: both period boundaries and 2 h 0 min outcome are correct, mapping
is preserved in design and unsupported trace sections removed from deltas. This
does not independently validate CLI/mechanical counts or approve design/Apply.
Strict structural FAIL from two unsupported trace sections was corrected once and
rerun PASS, retaining all requirements/scenarios and moving mapping into design.
Stage 05 is accepted and closed; CU09's proposal/design is ready for human review,
not accepted for implementation. No Apply, implementation, migration, provisioning, installation,
Sync, Archive, commit or push is performed. Stage 05 documentary closure is not
closure of this new functional change.
