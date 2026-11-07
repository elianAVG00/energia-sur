# Planned use-case catalog

Status: **ACCEPTED DOCUMENTARY BASELINE - stage 05 CLOSED under U06**. Catalog,
shared rules, register and workflow are accepted with their explicit TBDs. This is
not an implemented product or acceptance of the CU09 change design. CU09 is chosen
as the first stage 06 development; only its OpenSpec proposal is authorized now.
The current app remains a technical scaffold. The target of at least seven working
CUs does not remove the other three from the proposed ten-CU scope.

## Sources and classification

- **P**: product proposal, `Elian Gonzalez- Grupo 18 - Propuesta de TP Integrador
  (1).pdf`, pp. 1-2, as summarized in [stage context](../stage-05-context.md),
  sections “Producto y requisitos docentes” and “Catálogo funcional de referencia”.
- **T**: `Lineamientos TP.pdf`, pp. 1-2, summarized in the same context: prior
  teacher approval, ten proposed CUs, at least seven interactive working CUs,
  integrated AI chat, at least two MCP tools/servers including one external.
- **C**: confirmed development decisions/evidence in [README](../../README.md),
  [Docker design](../../openspec/changes/docker-development-environment/design.md)
  and [MCP design](../../openspec/changes/configure-readonly-development-mcp/design.md).
  These confirm the technical direction, not business acceptance.
- **U05**: the user's 2026-11-07 documentary-closure instruction and eight-decision
  table, recorded in [approval evidence](decisions.md#u05---user-approval-evidence).
  It approves specified rules, not teacher approval or global catalog acceptance.
- **U06**: the current user's baseline acceptance, CU09 policies/selection and
  confirmation that the teacher approved all ten Energía Sur CUs; see
  [evidence](decisions.md#u06---baseline-acceptance-and-cu09-proposal-authorization).
  Teacher approval date/channel are not recorded; no Apply is authorized.
- **I**: an explicitly labeled inference or proposed defensive alternative for
  review, not an approved addition to P. **TBD**: no documented decision; see the
  [question register](decisions.md). No implied policy may fill a TBD.

The supplied Markdown synthesis is the working source; the PDFs were not
independently re-read in this run. `Grupo 18.pdf` is a hardware-store example,
not a source for this product. Q00 is approved on the user's U06 teacher-approval confirmation.

## Index: exactly one fiche per ID

| ID | Fiche | Actor | Source / status |
| --- | --- | --- | --- |
| CU01 | [Query current outages in an area](cu01.md) | Visitor or account holder | P / accepted documentary baseline; implementation planned |
| CU02 | [Query upcoming scheduled works](cu02.md) | Visitor or account holder | P / accepted documentary baseline; implementation planned |
| CU03 | [Get guidance from the integrated assistant](cu03.md) | Visitor or account holder | P / accepted documentary baseline; implementation planned |
| CU04 | [Manage personal addresses and meters](cu04.md) | Account holder | P / accepted documentary baseline; implementation planned |
| CU05 | [Record a meter reading with a photo](cu05.md) | Account holder | P / accepted documentary baseline; implementation planned |
| CU06 | [Record an electricity bill](cu06.md) | Account holder | P / accepted documentary baseline; implementation planned |
| CU07 | [Compare recorded consumption with a bill](cu07.md) | Account holder | P + U05 / approved matching and kWh difference; residual TBDs |
| CU08 | [View consumption trends and estimates](cu08.md) | Account holder | P + U05 / approved base and grouping; projection formula TBD |
| CU09 | [Record and query an interruption diary](cu09.md) | Account holder | P + U05 + U06 / SELECTED first for stage 06; change design pending review |
| CU10 | [Supervise automatic source refresh](cu10.md) | Administrator | P / accepted documentary baseline; implementation planned |

Each fiche contains source/status, actor, preconditions, main flow, alternatives,
local rules, dependencies and traceable Given/When/Then scenarios. Shared rules
are defined once in [shared rules](shared-rules.md). Scenario IDs are documentary
acceptance candidates, not executed tests. **PLANNED** marks planned implementation
under this accepted documentary baseline; **REVIEW** marks an inference; **BLOCKED/TBD**
requires a decision before a determinate acceptance oracle can be written.
**APPROVED RULE** marks a U05/U06-backed result for the stated synthetic fixture;
it does not claim executed acceptance, resolution of other TBDs or an implemented CU.
The register has 24 questions: six approved within scope, six partial and twelve open.
Q00 is satisfied; unapproved implementation design decisions remain separate gates.

## Review and next transition

Use the [question register](decisions.md) to record explicit answers, rationale,
approver and evidence before promoting affected rules. CU09 is now selected and its
[proposal](../../openspec/changes/record-cu09-interruption-diary/proposal.md) and
[design](../../openspec/changes/record-cu09-interruption-diary/design.md) await review using
the [workflow](../openspec-workflow.md). Keep `openspec/specs/` for current behavior;
do not copy these drafts there. [Stage 05 evidence](../ai-engineering/stage-05-sdd.md)
separates CLI structure checks from documentation checks and future acceptance.
U06 supplies the formerly missing global documentary acceptance. Stage 05 closure
is not Archive of an OpenSpec change. Approve the new change's design and request
Apply separately before implementation; unrelated catalog TBDs remain unchanged.
