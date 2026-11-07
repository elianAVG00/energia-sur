# OpenSpec workflow and stage 05 boundary

Status: **accepted stage 05 documentary baseline under U06**, recorded 2026-11-07.
See the [catalog](use-cases/README.md), [evidence](ai-engineering/stage-05-sdd.md)
and [operational state](STATE.md).

## Installed conventions

- CLI `1.16.1`; package schema `spec-driven`, with `proposal`, `specs`, `design`
  and `tasks` artifacts. Project configuration uses supported `schema`, `context`
  and `rules` fields. No schema extension or generated asset refresh is needed.
- Global profile reads `custom`; selected workflows are `propose`, `explore`,
  `apply`, `update`, `sync`, `archive`. This is an observation, not a profile change.
- Six generated skills exist under both `.opencode/skills/` and `.agents/skills/`:
  `openspec-explore`, `openspec-propose`, `openspec-apply-change`,
  `openspec-update-change`, `openspec-sync-specs`, `openspec-archive-change`.
- `.opencode/commands/` contains matching `opsx-explore.md`, `opsx-propose.md`,
  `opsx-apply.md`, `opsx-update.md`, `opsx-sync.md`, `opsx-archive.md` files.
  File presence is not a fresh UI command-discovery test.
- Existing artifacts and agent instructions use English. Product-facing titles
  in the Spanish source are mapped to stable CU IDs, not replaced in scope.

## Explore -> Propose -> Review -> Apply -> Verify -> Archive

| Step | Installed mechanism or team procedure | Boundary / evidence |
| --- | --- | --- |
| Explore | `openspec-explore` skill / `opsx-explore` command file | Read context, compare scope and identify questions; no implementation. |
| Propose | `openspec-propose` / `opsx-propose`; CLI `new change`, `status`, `instructions` | Only when authorized: create the installed schema's required planning artifacts, then stop. A catalog fiche is not a change or approval. |
| Review | Team step, not an installed Review skill/CLI command | Explicit human acceptance of scope, critical decisions and artifacts before Apply. Record teacher approval of topic and ten CUs before business implementation. |
| Apply | `openspec-apply-change` / `opsx-apply` | A subsequent explicit implementation request and accepted contract are required. Do not carry implementation authorization forward from Propose. |
| Verify | Team step using `quality-gate`; CLI `validate` covers structure only | Record actual tests, applicable lint/types/build, integration/acceptance and independent review evidence. Missing mandatory checks are BLOCKED, not a pass. No installed `opsx-verify` or `openspec verify` is claimed. |
| Archive | `openspec-archive-change` / `opsx-archive`; CLI `archive` | Only with applicable successful gates and authorization; inspect sync state and permissions first. Archive does not retroactively approve behavior. |

`openspec-update-change` revises planning artifacts; `openspec-sync-specs` merges
authorized delta specifications. They are not substitutes for Review or Verify.
Generated skills and CLI capabilities do not broaden the user's authorization.
Configuration context/rules guide prompts; they do not technically enforce gates.

## Stage 05 closure and current proposal operation

Stage 05's catalog/config preparation did not create an implementation change.
U06 explicitly accepts its catalog, shared rules, register and workflow, closing
that documentary stage. Q00 is approved on the user's teacher-approval confirmation;
no teacher approval date/channel is recorded. CU09 is selected first for stage 06.

The active inventory now includes the CU09 proposal and two prior technical changes,
with zero main specifications. MCP has 8/8
checked tasks but remains unarchived; Docker has 18/22 with existing lint/backend
typing gates unresolved. Neither inventory nor strict structural validation
demonstrates a working business CU.

The [U06 evidence](use-cases/decisions.md#u06---baseline-acceptance-and-cu09-proposal-authorization)
supersedes those old blockers and authorizes only proposal artifacts under
`openspec/changes/record-cu09-interruption-diary/`, with related documentation and
context updates. Auth/persistence/PDF design choices must be explicitly reviewed.
Existing changes, main specs, runtime source, manifests/locks, AGENTS and tooling
configuration remain untouched. No Apply, Sync, Archive, installation, commit or
push is authorized. Stop after presenting the proposal/design for human review.
