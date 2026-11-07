---
name: quality-gate
description: Use before verification or closure to select checks, record evidence, and handle failures or blockers.
---

# Select and run the quality gate

All repository paths below are relative to the repository root, not this Skill's
directory. Write reports and project documentation in English. This Skill guides
verification; it does not grant shell access, approve tooling, or relax AGENTS.md.

## 1. Inspect scope and establish the check matrix

Read applicable AGENTS.md instructions, docs/STATE.md, accepted specs/scenarios,
relevant change artifacts, changed files, tests, actual manifests/lockfiles,
configuration, and README sections. Inspect only relevant dependencies and no
secrets. Confirm branch/status and preserve unrelated work. Distinguish prior
reported evidence from checks actually performed in this run.

For each acceptance criterion and risk, select checks before executing them:

| Change or risk | Applicable evidence |
| --- | --- |
| Documentation or Skills | File scope, accurate links/facts, English text, structure/frontmatter, client parsing/discovery if applicable |
| Backend/API or business rules | Contract/scenario tests, validation/errors, unit and route integration tests, lint/type checks |
| Frontend/UI | Component/integration tests, lint/type checks, production build, real API interaction |
| User-visible behavior | Real affected frontend/backend paths and acceptance scenarios; distinguish mocks from end-to-end evidence |
| OpenSpec artifacts | Installed structural validator plus human acceptance evidence; one does not replace the other |
| Auth, data isolation, security policy | Negative/security/regression checks and mandatory independent reviewer, Codex, or human review |
| Destructive migrations or breaking API/architecture | Explicit approval, recovery/compatibility evidence, regression checks, mandatory independent review |
| Agent/MCP/tool integration | Loaded configuration, effective permissions, permitted real invocation, redacted provenance/results; static rules do not prove isolation |

Mark mandatory checks explicitly. Documentation-only changes without functional
impact may exclude application tests with a concrete justification. If mandatory
tooling, prerequisites, credentials, permissions, or review are missing, mark
BLOCKED rather than treating absence as non-applicability. Never read credentials
merely to establish context; request approved synthetic/test setup when needed.

## 2. Resolve commands from evidence

Use PowerShell-compatible commands from the repository root. Inspect installed
versions and CLI help before changing tooling/dependencies. Read each script
and its effects before executing it; inspect transitive script calls relevant
to safety. Record the source manifest/script/config and required working directory
for each command. Do not invent npm scripts, pytest settings, application modules,
ports, or migration commands. Do not install or upgrade tools to fill a gap
without approval, or run network/service/destructive checks outside authorization.

On every run, inspect frontend/ and backend/ source, package manifests,
application entry points, lockfiles, test/lint/build configuration, and CI
workflows. Verify installed tools and documented commands against those files.
Check approval evidence for applicable test frameworks, database, ORM/migrations,
auth, hosting, MCP, and chatbot-memory decisions. Record missing setup and
unresolved choices in the authorized operational snapshot, not as fixed facts
in this procedure.

Before using the following inspection examples, confirm a Git repository exists,
OpenSpec is installed and initialized where needed, CLI help supports the flags,
and effective permissions allow execution. They are not application tests or
blanket approvals:

```powershell
git status --short --branch
git diff --check
git diff --stat
openspec list --json
openspec list --specs --json
openspec validate --help
```

`git diff` omits untracked content and, without `--cached`, staged changes.
Inspect new files explicitly and include staged checks when relevant; do not
mistake an empty diff for a clean gate. Avoid showing unrelated sensitive diffs.

When relevant specs/changes exist, check the installed CLI help before using this
structural-validation example; adapt it to supported options and approved scope:

```powershell
openspec validate --all --strict --json --no-interactive
```

Use the installed workflow's scope/store arguments when applicable. With no
specs/changes, record that there is no structural target, not that requirements
passed. Inventory/list commands prove only inventory, not structural correctness
or accepted/working behavior. No initialization or archive is part of this gate.

For Skills, check an exact SKILL.md entry file, delimited YAML frontmatter,
non-empty name/description strings, a matching lowercase kebab-case directory
ID, and a non-empty English procedure. Validate YAML with an existing parser or
the installed client's loader; a regex check alone is not full YAML validation.
Distinguish file validity, client discovery, actual loading, and real use. Do not
duplicate custom Skills into generated directories to force discovery.

On every run, inspect the selected agent's effective shell, Skill-loading,
file-read, and other relevant tool permissions before using them. A Skill cannot
override those rules. If Skill loading is denied, read a local Skill file only
when file-read permissions allow it. Return command/evidence requests to the
primary agent when execution is denied; do not use Code Mode, MCP, a different
agent, or another tool to bypass a denial. If no authorized runner exists,
execution remains BLOCKED. Review exact narrow allowlists before changing
permissions; never enable broad shell access just to obtain a pass.

## 3. Execute and retain evidence

Run the smallest relevant checks first, then affected integration/regression and
acceptance checks. Record actual results, not intended commands. For each check
capture: criterion/risk, mandatory status, command or read-only method, directory,
tool version where relevant, execution time, exit code where available, expected
and actual outcome, redacted output/evidence reference, actor, and limitations.
For manual checks record files/lines or reproducible steps and observed results.
Never fabricate logs, iterations, approvals, reviewer independence, or results.

Use this report shape, adapting fields without dropping evidence:

| Check / criterion | Mandatory? | Command or method / context | Result | Evidence / limitation / next action |
| --- | --- | --- | --- | --- |

Store detailed evidence in the authorized process record for a significant
OpenSpec change and link tasks/specs rather than copying requirements. Update
STATE.md with a concise operational snapshot only within authorized file scope;
otherwise return proposed updates. Never include keys or real personal records.

## 4. Interpret results and correct failures

- **PASS:** The check actually ran and the observed evidence meets its stated
  criterion. A zero exit code is insufficient if intended assertions never ran.
- **FAIL:** The check ran and exposed a defect, failed assertion, invalid
  structure, or unmet criterion. Include a reproducer and expected/actual result.
- **BLOCKED:** A required check could not run or produce adequate evidence due
  to missing tooling, setup, permissions, dependencies, approval, or independent
  review. Identify the smallest action/decision needed and who must provide it.
- **NOT APPLICABLE:** The check is genuinely outside the affected scope/risk;
  give a specific reason. This is not a workaround for missing prerequisites.

Fix observed failures only within authorized scope; rerun affected checks and
retain evidence of each attempt. Escalate after three unsuccessful correction
and verification cycles for the same unresolved failure; changing agents or
renaming the issue does not reset the count. Stop earlier for stalled progress,
missing permission, or required scope/spec/architecture decisions. Escalation
includes the reproducer, attempted corrections, remaining impact, and smallest
decision/action needed. Do not weaken tests or requirements to make checks pass.

## 5. Close only with sufficient evidence

Require independent reviewer, Codex, or human review for auth/data isolation,
security-policy, destructive-migration, or breaking API/architecture changes.
Verify that the reviewer is separate and callable; unavailable mandatory review
is BLOCKED. Use judgment for other changes and label self-review honestly.

Never declare implementation complete or archive while mandatory checks,
acceptance criteria, critical security checks, or mandatory independent review fail or
remain blocked. Report what passed, failed, was blocked, or was excluded, with
limitations and pending approvals. Sync/archive only through the installed
authorized workflow after verification succeeds. Fix evidence links after moves.
Commits, pushes, deployment, and external exposure require their own approval.
