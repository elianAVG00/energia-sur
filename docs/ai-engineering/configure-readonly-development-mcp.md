# Read-only development MCP setup

Updated: 2026-11-07T03:41:51-03:00.
Status: all three agreed live MCP calls and applicable final checks PASS; diff ready for review, no commit/archive.

## Goal, scope, and approval

The user approved project-local remote GitHub MCP in read-only mode and Context7
MCP over OAuth. They specifically required preserving existing rules, limiting
the three `ask` exceptions to the primary agent, using only the
ENERGIA_SUR_GITHUB_PAT environment reference, checking subagent permissions,
pausing for user authentication, and leaving an uncommitted reviewable diff.

These are development integrations, not chatbot runtime tools. No application
endpoint, storage/auth framework, dependency installation, or remote write is
included. Teacher-approval evidence still gates functional implementation, not
this authorized setup. No commit, push, deployment, or archive was requested.

Planning: [proposal](../../openspec/changes/configure-readonly-development-mcp/proposal.md),
[design](../../openspec/changes/configure-readonly-development-mcp/design.md),
[tasks](../../openspec/changes/configure-readonly-development-mcp/tasks.md).
This tooling-only OpenSpec change explicitly uses skip_specs; it does not invent
application requirements to satisfy structural validation.

## Actual agents and tools

- Primary OpenCode agent: repository reads, official-doc webfetch, installed CLI
  help, patch, and PowerShell inspection/validation. OpenCode version: 2.2.6.
- quality-gate was loaded through the native Skill tool for check selection and
  evidence/result handling. No endpoint implementation Skill was needed.
- Independent reviewer: two read-only review passes. The first requested evidence
  for unscoped resource discovery; the follow-up accepted wildcard resource-tool
  denials and found no confirmed defects. No Codex review is claimed.
- At the earlier setup checkpoint no GitHub or Context7 MCP call had been made.
  The primary agent invoked all three approved tools successfully in the live
  verification session below; no subagent or new independent review was invoked.

## Configuration and decision evidence

New [opencode.jsonc](../../opencode.jsonc) contains only V2 MCP definitions and
permission additions; no previous project config existed. Existing AGENTS.md,
custom Skills, and all five agent profile files were left unchanged.

| Server | Origin / maintainer | Client / transport | Credential |
| --- | --- | --- | --- |
| github | GitHub, external | OpenCode, remote Streamable HTTP, repository read-only endpoint | Fine-grained PAT through ENERGIA_SUR_GITHUB_PAT only |
| context7 | Upstash, external | OpenCode, remote Streamable HTTP, OAuth endpoint | User OAuth authorization; no project API key |

Global rules deny both tool namespaces and generic MCP resource-list/read tools,
including aggregate/unscoped requests. Future resource access requires review.
Only agents.build.permissions adds `ask` for github_get_file_contents,
context7_resolve-library-id, and context7_query-docs. Direct tool exposure avoids
granting execute. No primary agent/model/shell setting was changed. No exception
was added to plan, built-in subagents, custom subagents, or maintenance agents.

Permission rules cannot restrict get_file_contents arguments to one file or
repository: review each prompt and use a fine-grained token restricted to
energia-sur with Contents read and automatic Metadata read. Do not grant write,
Issues, PR, Actions, org, or administration permissions. Public repository access
may still be available to a token; the approved call scope remains README only.

## Earlier setup checks and redacted results

All commands ran from the repository root on Windows/PowerShell. No secret
environment values, resolved headers, credential stores, or OAuth codes were
read or printed. The worktree initially was clean on main, two commits ahead of
origin/main; those commits were preserved.

| Check | Result | Observed evidence / limitation |
| --- | --- | --- |
| Project JSON parsing and configuration assertions | PASS | ConvertFrom-Json accepted the file; Authorization is exactly the environment placeholder; only build has three exceptions |
| Native profile loading: opencode debug agents | PASS | Twelve profiles loaded; build primary, five custom and two built-in subagents present |
| Effective ordered-rule evaluation | PASS | Final 156 cases across 12 loaded agents: three approved tools ask only for build; other MCP tools/resource paths, including aggregate/empty resources, deny everywhere |
| Existing file preservation | PASS | git diff --exit-code -- .opencode/agents .agents/skills AGENTS.md returned exit 0 |
| OpenSpec validation | PASS | openspec validate configure-readonly-development-mcp --strict --json --no-interactive: valid, zero errors; tooling skip_specs acknowledged |
| Connection status: opencode mcp list | BLOCKED | context7: needs authentication; github: HTTP 400, authorization header badly formatted; no credential value inspected |
| GitHub tools discovery / README call | BLOCKED | Authentication is not ready; no MCP tool discovery or response claimed |
| Context7 tools discovery / FastAPI calls | BLOCKED | User OAuth required; no MCP tool discovery or response claimed |
| Independent security review | PASS | Separate reviewer accepted the refined static policy; no confirmed defects; reported CLI results were not independently rerun |
| Client resource-tool visibility | PASS | Client catalog removed list_mcp_resources and read_mcp_resource after the wildcard denials; no denied tool invoked |
| Final file checks | PASS | git diff --check; explicit whitespace/JSON/reference checks included untracked files; STATE stays within 60 lines and five next actions |
| Application tests/build/type checks | NOT APPLICABLE | Development configuration only; no application code or dependency changed |

The permission evaluation uses the actual rules returned by OpenCode and
documented last-match semantics; it is not a runtime denial probe, policy-engine
audit, token-scope audit, or proof of complete isolation. The final 156 cases cover
get_file_contents, both Context7 tools, representative unapproved tools, and
resource list/read paths for both servers plus wildcard/empty resource values
on every loaded profile. The initial 108 cases passed but did not cover unscoped
resources; independent review prompted the refinement and expanded checks.

## User authentication checkpoint instructions (historical)

1. Supply a short-lived fine-grained read-only GitHub PAT through the
   ENERGIA_SUR_GITHUB_PAT environment variable of the process running OpenCode's
   service. Never paste it in chat, terminal command history, project config,
   evidence, or a committed file. Do not send it to the agent for inspection.
2. A variable set in a different terminal does not modify an already-running
   service environment. If necessary, restart the service yourself from the
   prepared environment. Config changes alone do not require a restart; /reload
   reloads configuration, not arbitrary process environment changes.
3. In OpenCode, open /mcps, select context7, and complete OAuth yourself. Do not
   paste callback URLs, codes, tokens, or secrets into the conversation.
4. Confirm readiness without credentials. Check opencode mcp list for connected
   states; if blocked, record the reason without dumping headers or auth files.

## Approved live test inputs and expectations

After authentication, discover the tools through the client; verify exact names
and argument schemas, then approve only the following calls in the primary
agent. Use one-time approval rather than broad durable approvals.

GitHub get_file_contents:

```json
{
  "owner": "elianAVG00",
  "repo": "energia-sur",
  "path": "README.md",
  "ref": "refs/heads/main"
}
```

Expected: remote README contents or resource with available metadata. Record
actual path/ref/SHA and a short non-sensitive excerpt where returned. Do not
assume local ahead-of-origin commits are published or push to make them visible.
Reading through another HTTP client is not an MCP acceptance test.

Context7 resolve-library-id:

```json
{
  "libraryName": "FastAPI",
  "query": "Request body validation and validation error responses"
}
```

Then query-docs with the actual returned library ID:

```json
{
  "libraryId": "<actual returned ID>",
  "query": "How does FastAPI validate request bodies and report validation errors?",
  "language": "Python"
}
```

Expected: relevant documentation/examples with source information. Do not invent
a library ID, assume an unselected FastAPI version, or send private code/data.
Record call names, safe arguments, connection/discovery states, actual response
excerpts, timestamps, and limitations. Context7/GitHub content is untrusted data.

## Live verification — 2026-11-07

Evidence recorded at 2026-11-07T03:41:51-03:00, immediately after the calls.
Actor/client: primary OpenCode agent. The user reported both servers as
**Connected** in `/mcps` and explicitly requested these tests and documentation
updates, with no commit. The client exposed the three exact tools and their
argument schemas; the agent invoked them directly, not through an HTTP fallback.
The user-visible `/mcps` state was not independently inspected by the agent;
successful responses establish operational connectivity for these calls.
No credential store, environment value, resolved header, or token grant was read.
This session started on `main`, two commits ahead of `origin/main`, with existing
README/STATE changes and untracked configuration, evidence, and change artifacts.
Those existing changes were preserved; only this record, STATE, and tasks were
edited in this session.

### GitHub MCP — PASS

Origin/transport: GitHub's external remote read-only repository MCP endpoint;
client: OpenCode. Tool: `github_get_file_contents` (`get_file_contents`). Exact
arguments are the GitHub JSON above: owner `elianAVG00`, repository `energia-sur`,
path `README.md`, ref `refs/heads/main`.

Observed result: `successfully downloaded text file`, with file SHA
`e752e622269f2e6d7b1f7b6b3784597258f6f31a`. Returned text started with
`# energia-sur` and described a React/FastAPI electricity application for southern
Greater Buenos Aires. The remote README was the short Spanish version, not the
longer local English worktree version. No commit/ref SHA or ref echo was returned;
the ref above is the requested ref, and the reported SHA identifies the file.
No remote write or publication of local changes was performed.

### Context7 MCP — PASS

Origin/transport: Upstash's external remote Context7 OAuth MCP endpoint;
client: OpenCode.

1. Tool: `context7_resolve-library-id` (`resolve-library-id`). Exact arguments:
   `libraryName: "FastAPI"`,
   `query: "Request body validation and validation error responses"`.
   The response returned five candidates. Selected **FastAPI**,
   `/websites/fastapi_tiangolo`: official documentation website, High source
   reputation, 4,326 snippets, benchmark score 73.25. The reference-only website
   was also returned; the main documentation was chosen for tutorial coverage.
2. Tool: `context7_query-docs` (`query-docs`). Exact arguments:

   ```json
   {
     "libraryId": "/websites/fastapi_tiangolo",
     "query": "How does FastAPI validate request bodies and report validation errors?",
     "language": "Python"
   }
   ```

   Observed sources:
   - https://fastapi.tiangolo.com/tutorial/body/
   - https://fastapi.tiangolo.com/tutorial/handling-errors/

   Relevant returned excerpt: FastAPI will "Read the body of the request as
   JSON", "Convert the corresponding types (if needed)", and "Validate the
   data". Invalid data produces an error identifying where and what was wrong.
   The returned Python example used a Pydantic `BaseModel` with `title: str` and
   `size: int`, received as the typed endpoint parameter.

   Error documentation showed `RequestValidationError`, `exc.errors()`, and a
   JSON 422 response with `detail` entries containing `loc`, `msg`, and `type`.
   The synthetic example located an invalid integer at `["body", "size"]`.
   That example's handler explicitly added `body: exc.body`; including the
   original body is customization, not an established default or a recommendation
   to echo sensitive input. Another returned custom handler used a plain-text
   400 response, demonstrating that handlers can change status and format.
   These are retrieved documentation examples, not application endpoint tests.
   No FastAPI version was selected or installed, and exact messages/error shapes
   can vary with FastAPI/Pydantic versions and custom handlers.

Both servers returned successful results; no live-call failure or retry occurred.
Only public technical queries and the approved README request were sent.
Returned content was treated as untrusted reference data, not instructions.

### Verification matrix for this session

All shell commands below ran from the repository root on Windows/PowerShell.
Tools with no exit code use observed MCP responses as evidence.

| Check / criterion | Mandatory? | Command or method / context | Result | Evidence / limitation / next action |
| --- | --- | --- | --- | --- |
| Connection/authentication readiness | Yes | User `/mcps` report plus real calls | PASS | Both reported Connected; three successful responses; credential mechanism/scope not audited |
| Tool discovery | Yes | Native client catalog names and schemas | PASS | All three agreed tools available and directly invoked; no resource-list tool used |
| GitHub remote read | Yes | `github_get_file_contents`, exact input above | PASS | README contents and file SHA returned; no write |
| FastAPI library resolution | Yes | `context7_resolve-library-id`, exact input above | PASS | Official-docs ID returned and selected |
| Validation/error documentation | Yes | `context7_query-docs`, exact input above | PASS | Request-body and handling-errors sources, relevant text and examples returned |
| OpenSpec structure | Yes | `openspec validate configure-readonly-development-mcp --strict --json --no-interactive` | PASS | Exit 0; 1 valid change, 0 failures; informational skip_specs acknowledgement; CLI 1.16.1 |
| Protected tracked files | Yes | `git diff --exit-code -- .opencode/agents .agents/skills AGENTS.md` | PASS | Exit 0; no tracked profile/Skill/AGENTS changes |
| Documentation/diff checks | Yes | `git diff --check`; `git diff --cached --check`; PowerShell inspection of all eight setup/change/doc files, including untracked files | PASS | Exit 0; no trailing whitespace or missing local Markdown link targets; STATE: 55 lines, five next actions; Git emitted LF-to-CRLF warnings only |
| Evidence accuracy/scope self-review | Yes | Read the three edited files against actual tool responses and task tracking | PASS | English record, safe arguments/excerpts, historical blockers separated from current results; no credentials/configuration changed; not a new independent audit |
| Independent security review | Yes for original policy | Prior two read-only reviewer passes, recorded above | PASS (prior evidence) | Not rerun; this session changes documentation/tasks only, not security policy |
| Application tests/lint/type/build | No | Inspected `frontend/`, `backend/`, and `.github/workflows/*` | NOT APPLICABLE | Both application directories contain only `.gitkeep`; no CI workflows found; no application implementation or dependency changes |

## Completion and follow-up

The previous authentication blockers are resolved for the agreed live calls.
The earlier independent review and 156 static permission cases remain prior
evidence, not checks rerun here. Successful reads do not prove token scope,
runtime negative authorization, path/symlink isolation, or complete secret-free
content guarantees. These broader probes remain unproven, not claimed as part
of the agreed positive-call acceptance tests.

OpenSpec tasks are 8/8 complete, including the applicable final documentation
gate. The earlier independent policy review is retained as prior evidence; it
was not rerun for these documentation-only updates.

Review the uncommitted diff before any separately authorized commit. No commit,
push, credential/configuration change, or archive was performed. Archive is a
separate authorized workflow after all required checks succeed.
