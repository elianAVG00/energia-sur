# Stage 05 - SDD context and proposed use-case catalog

Recorded: 2026-11-07 (PowerShell local time; verification began around 05:15 -03:00).
Current status: **stage 05 CLOSED - accepted documentary baseline under U06**.
This is a stage record, not a newly opened OpenSpec change.
The original sections below retain the initial checkpoint's evidence. Their
all-TBD descriptions and 33-scenario/191-link counts are historical, superseded
first by the [U05 closure checkpoint](#closure-checkpoint---u05-decisions), then by
the [U06 accepted checkpoint](#accepted-baseline-checkpoint---u06). Historical
missing-Q00/global-review/candidate-only statements are not current blockers.

## Goal, sources and authorization

User requested reading AGENTS and the [stage context](../stage-05-context.md),
completing stage 05, checking the checkout and using read-only `spec-analyst`.
The user limited edits to `openspec/config.yaml` and documentation under `docs/`,
and explicitly prohibited CU implementation, Apply/Archive, commit and push.
The context also excludes installation, new implementation changes, Sync,
AGENTS edits and modifications to existing changes.

Deliverables: [workflow](../openspec-workflow.md), [catalog](../use-cases/README.md),
[shared rules](../use-cases/shared-rules.md), [question register](../use-cases/decisions.md)
and [configuration](../../openspec/config.yaml). Original PDF content was taken
from the supplied synthesis, not independently re-read. Catalog scenarios describe
planned behavior, not accepted contracts or executed business tests.

## Checkout and existing evidence

- Initial branch `main`, tracking `origin/main`, with no ahead/behind reported.
  HEAD `96192587c03bd0897637ba238a0285b5f1588581`,
  `chore: add reproducible Docker development environment`.
- Initial status: only `?? docs/stage-05-context.md`. That user-owned input was
  read and preserved, never edited or added to the index.
- No nested AGENTS files found. Read relevant README/config/state, agent definition,
  generated skill guidance, manifests, lockfile headers, entry points and frontend
  configuration. Existing test filenames were inspected; CI directory is empty.
- Active changes: [MCP tasks](../../openspec/changes/configure-readonly-development-mcp/tasks.md)
  8/8 and [Docker tasks](../../openspec/changes/docker-development-environment/tasks.md)
  18/22. Docker 1.4, 2.4, 7.1, 7.2 remain pending; historical browser/SQL successes
  were not rerun. No main specs; `openspec/specs/` contains only `.gitkeep`.
- PostgreSQL and development MCP approvals supersede their earlier TBD status;
  driver/ORM/migrations/auth/hosting/memory and added lint/type tools remain open.
  Teacher approval of topic/ten CUs is still undocumented. No material contradiction
  with an approved business contract was found; no such contract exists here yet.

## Actual agents and tools

- Primary OpenCode agent: local read/glob, approved PowerShell/git/OpenSpec commands,
  patch editing, `quality-gate` skill, and the read-only scope delegate.
- `spec-analyst` was verified in `.opencode/agents/spec-analyst.md` and invoked in
  read-only mode. Prompt: contrast all ten CUs with checkout/approvals, identify
  contradictions and per-CU questions; do not resolve teacher/technical TBDs.
  Follow-up: inspect the drafted catalog/config/workflow for accidental scope or
  policy decisions. It never edited files or executed commands. Its inability to
  run Git/CLI is separate from the primary's actual command evidence below.
- Context7 discovered `/fission-ai/openspec` and returned project-config schema
  documentation for `schema`, `context`, `rules` and operation guidance. Purpose:
  verify supported fields, not change integrations. Client: OpenCode; external
  server origin: Context7, already configured as development MCP. Only public
  library names/configuration questions were sent, no project data or secrets.
  This is a real documentation call, not a new MCP setup/permission audit.
- CLI help/generated files/runtime instruction loading are the installed-version
  authority when upstream documentation differs. No tools/dependencies installed,
  no configuration/permission changes to agents or MCP. No Codex review claimed.

## Decisions and scope contrast

- Keep English repository documentation and stable CU IDs. Ten separate fiches,
  with shared rules defined once; planned scope, confirmed facts, inferences and
  TBDs are explicitly distinguished.
- `spec-analyst` accounted for 10/10 CUs and confirmed the technical-only scaffold.
  No new approved business rule was found. Questions were incorporated as Q00-Q23.
- Follow-up content contrast PASS for all ten fiches, especially CU07/CU08/CU09.
  It identified two minor traceability defects: an unrelated Q23 link in shared
  provenance and missing reciprocal Q16/CU08-S02 mapping. Both were corrected in
  one documentary correction pass; no invented failed test or runtime cycle.
- CU07 compatibility and difference presentation remain Q13/Q14; CU08 formula and
  grouping remain Q15/Q16. CU09 permissions, overlap and boundary/open-cut hours
  remain Q18/Q19/Q20; PDF details Q23. Numeric examples illustrate alternatives,
  not accepted clipping, union, summation or rejection rules.
- CU09 remains a stage 06 candidate, not a chosen or authorized implementation.
  Review must consider CU04/account/persistence dependencies first.
- New implementation change exemption: documentary preparation only, with no
  business behavior/API/architecture change. Existing changes/specs are untouched.
- Root README was intentionally not edited (outside scope). [Docs index](../README.md)
  indexes this record. Review and Verify are team steps, not invented CLI commands.

## Validation matrix and observed evidence

All commands were run by the primary from the repository root on 2026-11-07.
Successful commands below exited 0 unless described as read-only/manual methods.
The quality-gate skill was loaded before final verification; the requested initial
structural baseline was captured earlier. No functional PASS is inferred.

| Check / criterion | Mandatory? | Actual command or read-only method | Result / evidence / limitation |
| --- | --- | --- | --- |
| Checkout baseline | Yes | `git status --short --branch`; `git log -1 --format="%H%n%s%n%aI"`; `git status --porcelain=v1 --untracked-files=all` | PASS: branch/HEAD and sole pre-existing untracked input recorded above. |
| Installed CLI/schema/profile | Yes | `openspec --version`; CLI help; `openspec schemas --json`; `openspec config get profile`; `openspec config get workflows`; generated directory reads | PASS: 1.16.1, spec-driven, custom, six workflows. No Review/Verify command installed in inspected locations. |
| Active inventory | Yes | `openspec list --json`; `openspec list --specs --json`; `openspec context --json` | PASS: nearest local root, two active changes, zero main specs. Empty main-spec inventory is not coverage. |
| Structural baseline | Yes | `openspec validate --all --strict` before edits | PASS: 2/2 changes, 0 failures. MCP INFO: `skip_specs`, zero deltas accepted. No pre-existing structural failures observed. |
| Post-edit structural validation | Yes | `openspec validate --all --strict --json --no-interactive` and final exact `openspec validate --all --strict` | PASS: same two changes, 0 failures, 0 main specs; MCP INFO unchanged. No introduced structural failure. Does not validate catalog prose or business acceptance. |
| Project configuration load | Yes | Four read-only `openspec instructions <artifact> --change docker-development-environment --json` calls for proposal/specs/design/tasks; PowerShell `ConvertFrom-Json` assertions | PASS: all four responses contain the new catalog/teacher-approval context and exactly two rules each (8 rules). No Apply/Archive instruction execution or artifact edits. |
| Ten-ID/fiches/structure | Yes | PowerShell assertions over index rows, fiche filenames/titles and required sections | PASS: exactly CU01-CU10 once in index; 10 fiches, each with source/status, actor, preconditions, flow, alternatives, rules/dependencies and scenarios. |
| Scenario traceability | Yes | PowerShell splits scenario blocks, checks unique IDs, Given/When/Then and resolvable rule/question references; primary content review and delegate contrast | PASS: 33 scenario candidates, 24 unique questions Q00-Q23. Traceability is documentary, not 33 passing tests. TBD scenarios have no settled numeric/policy oracle. |
| Relative links / anchors | Yes | PowerShell resolves Markdown destinations from each changed/new document, checks files and heading anchors | See final check totals below. Includes the preserved stage context; historical unchanged records are link targets, not recursively audited. |
| Whitespace / edit scope | Yes | `git diff --check`; `git diff --cached --check`; explicit new-file whitespace checks and path allowlist assertions | See final check totals below. Git's LF-to-CRLF warning is informational; no whitespace error. |
| English/proposed status / source fidelity | Yes | Fiche-by-fiche primary review and read-only `spec-analyst` contrast against supplied source | Planned English catalog, no business policy accepted. Supplied Spanish source preserved. Final delegate disposition recorded below. |
| App unit/integration/lint/types/build/browser/runtime | No | NOT APPLICABLE for this documentary-only diff | No runtime/source/manifests/locks changed. Existing Docker lint/backend-type gates remain BLOCKED in their own change; no historical test result is claimed as a rerun. |
| Business acceptance / teacher approval | Future implementation gate | No business test or implementation attempted | BLOCKED for implementation: missing teacher approval and affected TBD decisions. Not a failure of authorized documentary preparation. |
| Human documentary acceptance | Yes, before progressing | Human review of catalog, questions and workflow | PENDING/BLOCKED for progression. This run stops ready for review, without claiming human approval. |

### Reproducing the separate checks

```powershell
openspec list --json
openspec list --specs --json
openspec validate --all --strict
openspec validate --all --strict --json --no-interactive
openspec instructions proposal --change docker-development-environment --json
openspec instructions specs --change docker-development-environment --json
openspec instructions design --change docker-development-environment --json
openspec instructions tasks --change docker-development-environment --json
git diff --check
git diff --cached --check
git status --short --branch
git ls-files --others --exclude-standard
```

The additional PowerShell assertions use `Get-Content`, `Get-ChildItem`, regex
matching and `Test-Path`: index IDs must equal CU01-CU10 in order; fiche titles
must match filenames; every scenario block must contain Trace/Given/When/Then;
referenced local rules, shared-rule/question anchors and relative destinations
must exist. Scan full new files for trailing whitespace, conflict markers and
missing/extra final blank lines, not just tracked diffs. Union tracked, staged
and untracked paths and require `openspec/config.yaml` or `docs/` only; assert
no diff to existing changes, main specs, source, manifests, AGENTS or root README.
These are local structural assertions plus content review, not a new test framework.

## Initial documentary checkpoint

- PASS: 10 unique index IDs, 10 independent fiches, 33 traced Given/When/Then
  scenario candidates, 24 unique questions. The analyst's two minor traceability
  corrections were incorporated; primary rechecked the affected mappings.
- PASS: 191 relative Markdown destinations, including 122 heading anchors,
  across 18 documents (including the unchanged user-supplied stage context).
- PASS: full-file whitespace/scope assertions cover 19 checkout paths: two tracked
  edits (`docs/STATE.md`, `openspec/config.yaml`), zero staged paths and 17 untracked
  files including the preserved source. Thus stage output is 16 new documents plus
  the two tracked edits; `git diff --stat` alone omits the new documents.
- PASS: STATE is 36 lines with five next actions; no existing change, main spec,
  code, manifest, lockfile, AGENTS or root README edit. Final HEAD/branch remain
  the initial baseline. No pre-existing or introduced structural failures observed.
- Delegate scope contrast: PASS, content-only; not functional, CLI or Codex
  verification. Human documentary acceptance remains pending. Teacher approval
  and affected business decisions still block future implementation.

No CU implemented; no change opened/applied/synced/archived, installation, commit,
push, database operation or application/network exposure. Existing Docker blockers
and all unknown business decisions remain visible in [STATE](../STATE.md).

## Closure checkpoint - U05 decisions

Recorded: 2026-11-07; checkout inspected at 05:31 and checks at 05:37 -03:00. Status: **READY FOR GLOBAL
HUMAN DOCUMENTARY REVIEW**, not globally accepted, implemented or archived.

### Authority and bounded edits

- User requested final documentary closure and explicitly approved eight rules in
  this conversation. [U05 evidence](../use-cases/decisions.md#u05---user-approval-evidence)
  identifies the instruction and approver; each register entry separates approved
  scope from remaining questions. The original synthesis was preserved unchanged.
- Edited nine existing documentation files: CU07/CU08/CU09, catalog index, decision
  register, shared rules, workflow, STATE and this record. No new files or changes
  were opened. The pre-existing config edit and other local documents are preserved.
- At entry: `main` tracking `origin/main`, HEAD
  `96192587c03bd0897637ba238a0285b5f1588581`; two unstaged tracked paths and 17
  untracked files, zero staged. This is not a clean checkout and was never reset.
- Preservation baseline: SHA256 over sorted `path:SHA256` lines for the ten
  out-of-edit incoming paths was
  `99DDA8B3FE8832EE36B4DC961B509585C20301684D5A33C3FBAA894EB7D13353`.
  Paths: `openspec/config.yaml`, `docs/README.md`, `docs/stage-05-context.md`,
  CU01-CU06 and CU10 fiches. Final comparison protects their existing local content.
- Documentation-only exemption remains: no implementation change is created by
  recording explicit decisions. No OpenSpec contract is applied/synced/archived;
  future accepted design artifacts must carry these decisions when authorized.

### Decisions and scenario oracles

- **Resolved within scope:** Q13 exact same-meter boundary dates, no comparison
  without both matches; Q19 keep overlapping entries and union their time per domicile.
- **Partial:** Q14 kWh/direction/equality; Q15 latest two valid same-meter readings;
  Q16 interval consumption and daily-average grouping; Q18 own-account domicile
  mandatory to save; Q20 period clipping and min(generation, period end) for open
  cuts; Q23 required PDF content. Their unapproved details remain explicitly TBD.
- CU07 fixtures cover exact/nonmatching dates, both difference directions and zero.
  CU08 fixes interval rows and base selection, never a projected kWh formula.
  CU09 covers mandatory own domicile, retained overlaps totaling 3 hours, November
  clipping to 2 hours, fixed-time open-cut caps of 5 and 2 hours, PDF content and
  a separately blocked broader permission scenario. Existing IDs are preserved.
- All sixteen other questions remain open, with their affected CUs/scenarios and
  reasons retained. Q00 remains the academic gate; no teacher approval evidence was
  found in the inspected local documents. CU09 remains only a stage 06 candidate.

### Verification method and results

The primary loaded `quality-gate`, inspected relevant instructions, manifests,
lockfile headers, entry points and test/build configuration, and selected separate
mandatory structural and documentary checks. App tests/build/runtime are NOT
APPLICABLE: no implementation, manifests, lockfiles or runtime configuration changed
in this closure. Existing Docker lint/type blockers are not waived or rerun.

CLI: installed OpenSpec 1.16.1; supported flags checked with `validate --help`.
Context7 public OpenSpec documentation confirmed structural-only validation and
`skip_specs` semantics; this OpenCode development-MCP call transferred only a public
library question, not repository data/secrets. No MCP/configuration permissions changed.
Primary content review is not a functional/security audit or teacher acceptance.
Read-only `spec-analyst` was invoked again after verifying its existing local
permissions. Prompt supplied all eight user rules and required a bounded approval,
TBD, provenance and scenario/arithmetic contrast, with no edits or execution.
Its result was content-only PASS with no corrections: all eight rules match U05,
numeric fixtures are correct, residual TBDs/Q00/global Review remain open. This is
independent documentary contrast, not a Codex, mechanical-check or security audit.

| Check / criterion | Mandatory? | Command / method from root | Current closure result |
| --- | --- | --- | --- |
| Incoming checkout and preservation | Yes | `git status --short --branch`; `git log -1 --format="%H%n%s%n%aI"`; SHA256 baseline/final comparison | PASS: main/HEAD unchanged, all ten out-of-edit paths byte-identical; two tracked edits, zero staged, 17 untracked retained. |
| OpenSpec active inventory | Yes | `openspec list --json`; `openspec list --specs --json` | PASS: MCP 8/8 and Docker 18/22; zero main specs. No working CU coverage inferred. |
| Strict structural baseline | Yes | `openspec validate --all --strict` before closure edits | PASS, exit 0: 2 changes, 0 failures; MCP INFO for `skip_specs`, no pre-existing structural failure. |
| Strict structural final | Yes | `openspec validate --all --strict` after closure edits | PASS, exit 0: change/configure-readonly-development-mcp and change/docker-development-environment, 2 passed/0 failed, zero main specs. MCP skip_specs INFO unchanged. No prior or introduced structural failures. Catalog prose/acceptance is not validated by this CLI. |
| IDs, scenario uniqueness and traceability | Yes | PowerShell regex/section/reference assertions over all ten fiches, index and register | PASS, exit 0: 10 IDs exactly once in index, 10 fiches, 38 globally unique Given/When/Then scenario candidates, valid local-rule/shared-rule/question references. No scenario execution claimed. |
| Approved/TBD state coherence and required coverage | Yes | Primary source-to-rule review, register-state assertions and read-only analyst scope/arithmetic review | PASS: 24 unique questions, 2 resolved/6 partial/16 open; eight U05 entries each have approved scope, pending scope and impact. Formula, validity, period limits, precision, lifecycle, broader permissions and PDF details remain TBD; index/STATE/workflow agree. |
| Relative links / heading anchors | Yes | Resolve every relative Markdown destination in all 18 stage documents and check target headings | PASS, exit 0: 211 destinations, including 147 heading anchors. No recursive audit of unchanged historical targets. |
| Full diff and new-file whitespace / scope | Yes | `git diff --check`; `git diff --cached --check`; whole-file whitespace/path checks on tracked, staged and untracked inventory | PASS, exit 0: all 19 incoming checkout paths checked, no scope/new-file/whitespace drift; STATE 36 lines/5 next actions. Informational LF-to-CRLF warnings only. |
| Application tests / runtime / implementation security | No | NOT APPLICABLE: documentation-only clarification, no access-control implementation | No runtime, database, frontend/backend test or Codex-security PASS is claimed. Future auth/isolation changes retain independent-review requirements. |
| Global human Review / teacher approval | Yes for progression | Human acceptance and Q00 evidence | BLOCKED for progression: rule-level U05 approval is not global Review or teacher approval. |

### Closure disposition

All required automated/documentary checks for preparing this review passed; no
functional checks or human acceptance are inferred. The primary also checked
resolved rule references against definitions and retained initial scenario IDs:
33 prior IDs remain, with CU07-S04/S05 and CU09-S07/S08/S09 added (38 total).
Full new-file content, not only Git's two-path tracked diff, was validated.
No new correction cycle was needed in this closure; earlier minor corrections
belong to the historical initial checkpoint. Final status remains ready for review,
not unconditionally complete, because the mandatory global human gate is pending.
The concrete global Review action is to explicitly accept the ten-fiche catalog,
shared rules, register and workflow as the stage 05 documentary baseline with
residual TBDs retained. Stage 06 implementation additionally needs Q00 evidence,
selection/authorization and affected technical/business decisions. No implementation,
new change, Apply, Sync, Archive, installation, commit or push is performed.

## Accepted baseline checkpoint - U06

Recorded 2026-11-07 from the user's explicit current instruction. **Stage 05 is
CLOSED as documentary preparation**, not archived and not a claim of working CUs.

- The user accepts the catalog, shared rules, register and workflow as the baseline
  with remaining TBDs. This is the previously missing global human Review action.
- **Q00 APPROVED on user confirmation:** the teacher approved all ten Energía Sur
  cases of use. No teacher approval date/channel is recorded; the timestamp of
  recording this confirmation is not the teacher's approval date.
- CU09 is **selected**, not merely a candidate, as the first stage 06 development.
  User authorizes its OpenSpec proposal/design for review only. The new Buenos
  Aires minute-time, validation, correction/closure, exclusive account permissions,
  positive-duration exclusion and PDF table rules are transcribed under
  [U06](../use-cases/decisions.md#u06---baseline-acceptance-and-cu09-proposal-authorization).
- Current stage 05 checks are recorded with the [CU09 proposal evidence](record-cu09-interruption-diary.md):
  separate documentary assertions and strict active-artifact validation, with old
  change files/input preserved. Earlier check counts are historical snapshots.
- Current checks PASS: 10 unique CU fiches, 44 traced catalog scenarios, 24 questions
  (6 approved/6 partial/12 open), 260 relative destinations/160 anchors across 25
  current documents/artifacts, full-file whitespace/scope and eleven preserved hashes.
  Strict OpenSpec final PASS 3/3 active changes, including the new proposed CU09
  change, with zero main specs. The newly introduced trace-section warnings were
  corrected before closure; initial baseline had 2/2 passing changes. None of this
  is functional acceptance or implementation of CU09.
- The initial scope prohibition against opening a change applied to stage 05
  preparation; this latest user request expressly authorizes the stage 06 proposal.
  No existing change was modified or archived; no Apply/Sync/runtime implementation.
- Auth/persistence/PDF technical choices and the CU09 proposal remain for human
  design review. Those future gates do not reopen accepted stage 05 or Q00.

Outcome: accepted documentary closure and authorized transition to CU09 proposal
review, with [proposal](../../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/proposal.md),
[design](../../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/design.md) and remaining
decisions explicitly separated from implementation permission.
