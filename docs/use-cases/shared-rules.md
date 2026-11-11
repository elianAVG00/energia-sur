# Shared planned rules

All P/T/U05/U06 references resolve through the [source key](README.md). These shared
rules are accepted as the U06 documentary baseline, not executed implementation
contracts. The register distinguishes approved rules from residual design decisions.

## SR01 - Public access

**P:** outage queries, scheduled works and chat are public (CU01-CU03); visitors
do not need an account for those functions. Location input/consent and resolution
details remain [Q01](decisions.md#q01) and [Q02](decisions.md#q02).

## SR02 - Account-bound personal information

**P:** CU04-CU09 concern an account holder's personal records. **AGENTS constraint:**
preserve server-side authorization and ownership; never expose another person's
records or provider keys. This is not approval of an auth mechanism, sharing model
or other CUs' detailed per-address matrix. **U05 + U06, CU09:** only the account with
the registered domicile may save/view/correct/close/export its cuts
([Q18](decisions.md#q18)); U07/U07-T approve CU09's session/auth technology in its
[contract](../../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/contract.md).
Broader Q03 decisions remain pending. Negative scenarios define constraints;
actual isolation evidence is recorded separately in CU09's engineering record.

## SR03 - Provenance and uncertainty

**P:** public sources are ENRE/Edesur, GeoRef helps locate addresses, official
guides support the assistant, and the public-data update date is visible.
**AGENTS constraint:** preserve provenance/timestamps/uncertainty and never invent
live outages, charges or successful refreshes. Feed availability, refresh semantics,
staleness threshold and timezone remain [Q04](decisions.md#q04),
[Q05](decisions.md#q05) and [Q07](decisions.md#q07).

## SR04 - User-supplied personal evidence

**P:** the user supplies addresses, meters, readings/photos, bills and diary
records; they are distinct from automatically acquired public data. **AGENTS
constraint:** use synthetic/redacted examples; do not transfer real bills, photos,
addresses or secrets without explicit authorization. File policies and lifecycle
remain [Q09](decisions.md#q09), [Q11](decisions.md#q11) and
[Q12](decisions.md#q12). **U13, CU05 only:** optional photo and user-requested OCR
are approved with explicit confirmation and manual fallback; no OCR provider or
external transfer is approved. Other evidence types remain unaffected.

## SR05 - Automatic public-data acquisition

**P:** public data acquisition is automatic; CU10 supervises/retries/configures
enabled sources rather than replacing acquisition with manual business-data entry.
Exact sources, interval/retry limits, administrator authorization and concurrency
remain [Q04](decisions.md#q04), [Q21](decisions.md#q21) and
[Q22](decisions.md#q22). No scheduler or connector is implemented by this catalog.

## SR06 - Approval and delivery boundary

**T:** ten CUs proposed before development, teacher approval before business
implementation, at least seven working end to end, integrated framework-based
chat and at least two MCP tools/servers including one external. Development MCP
evidence is distinct from chatbot integration and must not expose privileged tools
to the app. [Q00](decisions.md#q00) is approved on the user's U06 confirmation of
teacher approval of all ten Energía Sur CUs, without recording a teacher date/channel. The approved stack
now includes CU09's approved auth, ORM and migrations under U07/U07-T; U23 decides the
CU03 persistent-memory mechanism, and the Edesur guide is delivered (v1.0.0, 2026-11-10)
and ingested at article granularity; hosting and other CUs' unresolved decisions remain
pending.
