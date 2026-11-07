# CU09 interruption diary - stage 06 proposal record

Status: **PROPOSAL/DESIGN FOR HUMAN REVIEW; APPLY BLOCKED**. Recorded 2026-11-07.
Links: [proposal](../../openspec/changes/record-cu09-interruption-diary/proposal.md),
[design](../../openspec/changes/record-cu09-interruption-diary/design.md),
[tasks](../../openspec/changes/record-cu09-interruption-diary/tasks.md),
[domicile delta](../../openspec/changes/record-cu09-interruption-diary/specs/account-domiciles/spec.md),
[diary delta](../../openspec/changes/record-cu09-interruption-diary/specs/interruption-diary/spec.md).

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
| Final structural validation | Yes | `openspec validate --all --strict` | PASS, exit 0 after one correction: MCP, Docker and CU09 changes, 3/3, zero main specs. CU09 contains 2 delta specs/10 requirements/17 scenarios. MCP skip_specs INFO unchanged; no existing change failed. Not catalog prose or working-CU validation. |
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
