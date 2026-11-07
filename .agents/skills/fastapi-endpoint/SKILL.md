---
name: fastapi-endpoint
description: Use before adding or changing a FastAPI endpoint under an accepted OpenSpec contract.
---

# Implement a FastAPI endpoint

All repository paths below are relative to the repository root, not this Skill's
directory. Write project documentation and reports in English. This procedure
does not grant permissions, approve requirements, or select technical TBDs.

## 1. Establish authorization and the contract

1. Read root and applicable nested AGENTS.md instructions, docs/STATE.md,
   openspec/config.yaml, and the relevant full specs, scenarios, design, tasks,
   source, and tests. Verify referenced resources exist before relying on them.
2. Check branch and working-tree status with `git status --short --branch` when
   shell access is permitted; preserve unrelated changes. If unavailable, ask
   the primary agent for the evidence rather than bypassing restrictions.
3. Verify documented teacher approval of the topic and ten use cases before
   functional implementation. Missing evidence means pending documentation,
   not rejection; request confirmation/evidence and pause affected coding.
4. Identify the accepted contract and approval evidence: method/path, request
   fields, response schema/statuses, business rules, validation, errors, access
   rules, and relevant scenarios. A draft, checked task, or valid OpenSpec file
   alone does not prove acceptance. Resolve missing or conflicting behavior.
5. For new behavior, API-contract, business-rule, or architecture changes, use
   the installed OpenSpec workflow and required planning artifacts before coding.
   Reuse applicable acceptance; bounded restoration of an existing contract may
   skip a new change only with the exemption recorded. This Skill never grants
   permission to scaffold artifacts or implement beyond the assigned scope.
6. State acceptance criteria, assigned files, risks, dependencies, and unresolved
   decisions. Request approval for applicable TBDs; do not select a database,
   ORM/migration system, auth mechanism, or test framework implicitly.

## 2. Implement the accepted behavior

- Inspect actual manifests, lockfiles, configuration, and README instructions
  before choosing dependencies or commands. Reuse existing module boundaries;
  report missing setup instead of inventing an entry point or installing tools.
- Keep handlers focused on HTTP transport. Keep authoritative calculations and
  business rules in backend logic, with external I/O separated. Do not add new
  architectural layers or dependency frameworks without approval.
- Use strong Python typing and explicit input/output schemas consistent with
  the approved framework version and API field names. Validate path, query,
  headers, and body inputs: required/optional fields, bounds, formats, units,
  and cross-field invariants as specified. Avoid unchecked coercion or hidden
  defaults that change the contract; do not suppress diagnostics to hide errors.
- Preserve the contract's status codes and error envelopes. Distinguish invalid
  input, missing resources, conflicts, denied access, and upstream failures only
  as defined by the accepted contract. Do not invent an error taxonomy; request
  clarification where missing. Never return stack traces, keys, or private data.
- When applicable, enforce authentication, role/permission rules, and resource
  ownership on the server. Do not trust frontend flags or user-supplied owner
  identifiers. Test cross-user access and avoid leaking resource existence where
  the contract forbids it. If no authorization is applicable, record why from
  the accepted scope; a missing auth decision is not a public-access approval.
- Handle upstream timeouts/failures and uncertain public data as specified;
  preserve provenance and freshness where relevant. Never fabricate live data.
- Before editing, inspect the selected agent's effective permissions and assigned
  file scope on every run. Edit only files allowed by both; return out-of-scope
  OpenSpec, shared-contract, or state updates to the primary agent. Do not access
  secrets or real personal records; use synthetic fixtures. Stop affected work
  for a material spec/design flaw.

## 3. Test and verify

Read `.agents/skills/quality-gate/SKILL.md` and build an applicability/evidence
matrix. Derive commands from actual approved project tooling; this Skill does
not prescribe pytest, an HTTP client, a server module, or installation commands.

Select meaningful tests for the accepted scenarios and affected regressions:
- Successful requests and exact response fields/statuses.
- Invalid/missing inputs, boundaries, cross-field rules, and error envelopes.
- Business rules independently from transport; deterministic synthetic fixtures.
- Missing/conflicting resources and external-service failure behavior.
- Authentication, authorization, ownership, and cross-user denial when applicable.
- Real route integration, including response serialization and exception mapping.
- Real frontend/backend paths for user-visible behavior when available; mocks
  and backend-only tests do not establish end-to-end success.

On every run, inspect backend source, accepted endpoint contracts, entry points,
manifests, lockfiles, and test configuration. Verify installed tool versions,
documented commands, and approval evidence for relevant tooling, storage, and
auth decisions; record missing prerequisites or unresolved decisions in the
authorized operational snapshot rather than assuming a fixed repository state.
Check the selected agent's effective execution permissions before each command.
Mandatory execution without prerequisites or permitted commands is BLOCKED,
not PASS or NOT APPLICABLE. If execution is denied, return commands/evidence
requests to an authorized primary agent without substituting another execution
tool or broadening permissions.

## 4. Handoff

Return changed files, accepted spec/scenario/task links, tests added, exact checks
and evidence labeled PASS/FAIL/BLOCKED/NOT APPLICABLE, risks, and required
decisions. Follow quality-gate correction/escalation and independent-review
requirements. Do not declare completion while mandatory checks/review remain
failed or blocked. Update tasks/state/process documentation only when authorized
and within file scope; otherwise return proposed updates. Do not commit or push.
