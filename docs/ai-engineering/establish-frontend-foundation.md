# Establish frontend foundation - implementation and verification evidence

Status: **IMPLEMENTED AND VERIFIED; READY FOR HUMAN REVIEW; UNARCHIVED** (2026-11-07).

## Apply checkpoint

After artifact presentation, the user explicitly requested "Aplicá
establish-frontend-foundation". The preceding canceled attempt made no edits.
Primary preserved the existing uncommitted CU09 tree on main (ahead 1); no reset,
commit/push/Archive/deployment/cleanup. Foundation task 1.1 records this handoff.

Actual split: frontend delegate owns local components/layout/forms/styles and schema
tests only; primary owns exact dependencies/configuration, memory-only Zustand,
Axios/typed CU09 adapter and transport tests, E2E, docs/tasks and verification.
No concurrent writers to shared files. Delegate has no shell/web permission; its
verification is primary-run, not delegated runtime evidence. A separate read-only
reviewer inspects stable session/transport files before final UI recheck.

Early actual PASS: proposed exact dependencies installed/locked with npm11.19.1
`--strict-peer-deps` and no force/legacy peers; optional peer metadata checked;
React/ReactDOM/TypeScript/Vite/Node/npm pins unchanged. Manual reviewed local
shadcn/ui source adaptation uses official new-york-v4 source and MIT license;
no CLI initializer or shadcn runtime dependency needed. Mounted locked dependencies
ran 42 Node tests and strict typecheck successfully before UI integration. This is
not the final rendered-browser acceptance. Primary security inspection found no
credential-related entries in frontend/.npmrc, without logging configuration values.

## Delivered behavior and source

- Tailwind 4.3.5/Vite plugin integrated without replacing the existing app/proxy.
  `components.json`, Vite/TS alias and Docker copies/allowlist agree.
- Local shadcn/ui-derived primitives and cn helper retain official source links,
  review date and the full MIT license in `frontend/src/components/ui/LICENSE`.
  Only needed source was adapted; no remote initializer or shadcn runtime package.
- `AppLayout` owns one unavailable `ChatMount`, outside auth/domicile keyed views.
  CU03 messaging/LangChain/streaming remain excluded, not simulated.
- Memory-only Zustand centralizes validated identity/CSRF and selected domicile.
  Generation checks prevent late responses from clearing a newer login or installing
  old data. Private rows/forms remain feature-local; no browser persistence/devtools.
- All login/domicile/cut/correction/closure/period forms use RHF/Zod, with associated
  accessible errors, pending states, typed null mapping and preserved keyed reset.
  Backend owns date/timezone/order/ownership/summary rules.
- One centralized Axios boundary keeps cookie auth, explicit current-token CSRF,
  token-free login/GET and no forged Origin. Destinations cannot escape same-origin
  `/api`; errors omit raw credential-bearing config; unsafe writes never auto-retry.
  Logout alone can use the pre-reset token while clearing local state immediately.
- Typed CU09 adapter retains DTO/resource-identity/status/MIME checks and PDF blobs;
  timeout/cancellation cover bounded JSON-blob error decoding. Existing native-fetch
  receiver-specific regression was replaced with shared-adapter validation when
  diary fetch was removed, not dropped to hide a failure. Health helper tests remain.
- [Reuse guide](../frontend-foundation.md) documents future CU adoption and limits.

## Final check matrix - repository root, primary runner

| Check / criterion | Mandatory? | Command or method | Actual result / limitation |
| --- | --- | --- | --- |
| Exact dependencies and compatible peers | Yes | Public npm metadata/optional peers, npm11.19.1 `install --package-lock-only --strict-peer-deps --ignore-scripts`, then strict `npm ci` in approved temporary workspace | PASS, no force/legacy peer bypass; original React/DOM/TS/Vite/Node/npm pins preserved. |
| Locked verification build | Yes | `docker build --target verification -t energia-sur-frontend-checks:cu09 frontend` | PASS, exit 0; npm ci, strict type/build, tests and lint executed in image. Final local log `Temp/opencode/foundation-frontend-build-final.log`. |
| Frontend tests | Yes | Image build RUN `npm test`, also prior mounted runs | PASS: 50 Node tests, zero skips/failures, including schema bounds/nulls, stale generations/401, all write CSRF, destination rejection, safe status errors, PDF MIME/error/cancel and deterministic deadline regressions. Mocks are not browser acceptance. |
| Frontend lint | Yes | `docker run --rm energia-sur-frontend-checks:cu09 npm run lint` | PASS: Oxlint1.92.0, 33 files/96 rules, zero warnings/errors. No suppressed diagnostics. |
| Strict TypeScript and production build | Yes | Verification image RUN `npm run build` | PASS: source, Node tests, E2E/config included; TS7.0.2 and Vite8.3.6 retained. |
| Backend lint/types | Yes (inherited regression) | `docker run --rm energia-sur-backend-checks:cu09 ruff check --no-cache app tests migrations`; `mypy --cache-dir /tmp/mypy-cache app` | PASS: Ruff; mypy 10 app modules. No backend implementation changed in this foundation. |
| Backend and actual PostgreSQL security/domain acceptance | Yes | `pwsh -NoProfile -File scripts/Test-Cu09Acceptance.ps1` | PASS, exit0: 66 backend tests including all14 PostgreSQL/ASGI tests, zero skips, 10.397s. U09 Origin/CSRF regressions retained. |
| One quick real Chromium CU09 adoption | Yes | Same script, Playwright1.65.0/Chromium, exactly one workflow (retries0) | PASS: 7.7s, actual login/cookies, registration/selection/create/correct/close, 409 and same-version reset, two accounts/foreign IDs, empty/excluded periods and logout. No second browser run. |
| Shell/chat/narrow layout | Yes | Assertions added to that same workflow | PASS: one disabled chat mount across login/auth/domicile/logout, no chat requests, viewport390x844 document without horizontal overflow, reachable PDF control/focus and restored desktop viewport. Not a universal accessibility or multi-browser audit. |
| Downloaded PDFs | Yes | Browser saves real closed/ongoing PDFs; script extracts actual downloads with pypdf | PASS: Unicode/address/text/complaint, periods, both retained descending rows, closed/ongoing statuses and exact3h/13h totals. No PDF renderer change. |
| Migration/restart/health regression | Yes | Same acceptance script reruns head with data and restarts backend, then compares fields/IDs | PASS: original DB container unchanged; two domiciles/three cuts survive exactly. Cluster contains additive synthetic DBs, not an unchanged-volume claim. |
| Lock drift rejection | Yes | `pwsh -NoProfile -File scripts/Test-Lockfiles.ps1` with nonsecret Compose interpolation placeholder | PASS: uv/npm reject deliberately changed disposable manifests without changing locks; no repository manifests altered by test. |
| Independent security/integration review | Yes | Separate read-only reviewer `ses_e48b00a1dffevhekFKL5Dug2tR` (partial audit then integrated recheck) | PASS source review: no remaining confirmed defects; low timeout finding corrected/rechecked. Reviewer did not execute tests or inspect secret files. Primary executed runtime gates. |
| Credentials in copied registry config | Yes | Primary redacted inspection of frontend/.npmrc for credential-related keys | PASS: none present, values not logged. Resolves earlier CU09 reviewer limitation. |
| OpenSpec, docs and preservation | Yes | `openspec validate --all --strict --no-interactive`, Markdown target/heading check, `git diff --check` and staged check | PASS: 4/4 active changes; 68 relevant local targets/5 anchors resolve; STATE41 lines; whitespace/staged checks exit0. HEAD unchanged at f76bc0f; no unrelated reset, AGENTS edit or archive. Foundation18/18 tasks verified, ready for human review. |
| Chat runtime/other CUs/backend migration/deployment | No | Accepted scope | NOT APPLICABLE: unavailable mount only, no provider/chat dependencies, no business/backend schema change or deployment. |

Latest acceptance log: user-local `Temp/opencode/foundation-acceptance.log`.
Retained synthetic DBs `cu09_app_6fde6167e31f` / `cu09_test_6fde6167e31f`, QA
container `energia-sur-cu09-qa-6fde6167e31f`; PDFs/state under the documented
`Temp/opencode/cu09-acceptance/`. No credentials printed, original DB container/data
preserved; current app uses this synthetic acceptance database. No cleanup authorized.

## Review findings and actual correction cycles

1. First integrated lint run: FAIL, two no-control-regex warnings in URL validation.
   Replaced control-character regex with explicit character-code checks, preserving
   rejection behavior; rerun lint/build PASS. No rule suppression or gate waiver.
2. Separate reviewer found a Low error-path bug: deadline expiry during asynchronous
   PDF JSON-blob decoding could look like cancellation and decoding could wait for
   body completion. Context now tracks caller/deadline/combined signals and the read
   races abort; deterministic manual-deadline and late-generation tests added.
   Separate integrated recheck found no remaining confirmed defects; final50 tests,
   types/lint/build and one real browser run pass. No browser correction/rerun occurred.

Actual agents: primary OpenCode orchestrator/implementer/test runner; frontend
delegate `ses_e48b70f7dffe12gQuTKg0EwHkq` (UI/forms only; no shell); separate reviewer
session above (read-only, no shell). No QA/Codex runtime execution is invented.
Actual tools: read/glob/grep/patch/PowerShell/Docker/OpenSpec, Context7 public docs,
official shadcn source/license fetch. No permissions edited or denials bypassed.

Residual limits: browser scope is one Chromium workflow, not a full visual/a11y audit.
CU03 runtime and unrelated catalog TBDs remain deferred. Earlier CU09 low risks for
out-of-band invalid stored rows and NUL text are not introduced or resolved here;
its final review task stays explicit. No Archive, commit, push, deployment or cleanup.

## Proposal-phase history (not current implementation status)

The sections below preserve proposal-stage context and gates; no-implementation
statements describe that earlier checkpoint only.

## Goal and authority

The user explicitly approved the shared frontend direction and requested this
separate change after aligning CU09 security. U09 is recorded in the
[decision register](../use-cases/decisions.md#u09---login-boundary-clarification-and-frontend-foundation-direction).
The installed proposal workflow and `openspec/config.yaml` require planning to
end at review, followed by a subsequent Apply request. Direction approval is not
misreported as execution of new artifacts. No foundation source, manifest, lock,
chat runtime or backend change was made.

Artifacts: [proposal](../../openspec/changes/establish-frontend-foundation/proposal.md),
[design](../../openspec/changes/establish-frontend-foundation/design.md),
[shell spec](../../openspec/changes/establish-frontend-foundation/specs/frontend-shell/spec.md),
[transport spec](../../openspec/changes/establish-frontend-foundation/specs/frontend-session-transport/spec.md),
[tasks](../../openspec/changes/establish-frontend-foundation/tasks.md).

## Actual investigation and tools

- Primary inspected existing App/forms, transport guards, request scopes, entry
  point, styles, Vite/TypeScript/Playwright/Docker files, manifests and tests.
  `openspec list --specs --json` confirmed zero main specs; CU09 is an active change.
- Used installed proposal instructions/status and dependency order. All four
  artifact types are present; task boxes remain unchecked. Capability specs describe
  observable shell/session/transport behavior, not library-specific implementation.
- Context7 public docs: shadcn/ui Vite/local components and RHF/Zod integration,
  Axios interceptors/cancellation/PDF/security boundary, Zustand memory reset and
  typed store patterns. Only public technical queries were transferred.
- Public npm registry metadata checked via the existing frontend verification image;
  proposed exact pins/compatibility caveats are in design F7. No install or lock
  regeneration was performed for this change; registry metadata is not install proof.
- No design/code subagent implemented this change. A separate read-only reviewer
  rechecked CU09's approved U09 security clarification only; its report is not
  foundation review or acceptance.

## Decisions and limits

Reuse Vite/React/TS and preserve pins. Split shared primitives/layout, memory-only
session/selection, typed transport and feature-local forms. Preserve CU09 reset,
ownership, date/PDF/status/cancellation contracts; no backend calculation in Zod.
Axios must attach only current session CSRF on authenticated writes, reject unsafe
destinations and never log raw credential-bearing config or retry writes. Chat is
one unavailable integration mount, not an implemented CU03. No new router/cache,
database/auth migration, hosting or persistent memory decision is introduced.

## Verification matrix

| Check | Mandatory now? | Result and evidence |
| --- | --- | --- |
| Project/root/schema discovery and artifact instructions | Yes | PASS: initialized nearest root, spec-driven, proposal/specs/design/tasks created in CLI dependency order. |
| Strict OpenSpec validation | Yes | PASS: `openspec validate --all --strict --no-interactive`, 4/4 active changes, zero failures. |
| Artifact completeness | Yes | PASS: `openspec status --change establish-frontend-foundation`, 4/4 artifact types complete; not implementation acceptance. |
| Documentation and whitespace | Yes | PASS: `git diff --check` exit 0; 100 relative Markdown targets across relevant docs/new artifacts resolve; STATE is 40 lines. Link target existence is not a complete anchor audit. |
| Foundation install/lint/types/unit/build/browser/security review | No at planning stage | NOT APPLICABLE now; mandatory future tasks, not claimed passes. All implementation task boxes remain unchecked. |
| Existing CU09 security baseline | Separate change | PASS primary-run: 66 backend tests/14 PostgreSQL, zero skips; one quick real-browser run/PDF 4.9s. See the CU09 record. This is not foundation adoption verification. |

No speculative correction attempts or failed installs are invented. No Archive,
commit, push, deployment or cleanup authorized/performed. Next action: review the
artifacts, then request Apply to implement the approved frontend direction.
