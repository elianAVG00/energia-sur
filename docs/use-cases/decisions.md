# Traceability and decision register

Status: **stage 05 documentary baseline accepted and closed under U06**; CU09 is
selected for the first stage 06 development. U07 approves its proposal/recommended
D0-D5 and authorizes Apply; U07-T approves the missing technical package in its
[contract](../../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/contract.md).
U08 resolves the historical-date floor and frontend lint alternative. Unrelated
scope/stack decisions are not implicitly approved. Verification and any
newly observed design edge remain separate from the user's approval.

## U05 - User approval evidence

**Approver:** the project user, in the 2026-11-07 conversation instruction beginning
“Finalizá el cierre documental de la etapa 05 de Energía Sur”, specifically its
eight-row decision table and the following scope/TBD restrictions. This entry is
the repository transcription of that instruction, not an external teacher record
or a fabricated approval identifier. Q13-Q16/Q18-Q20/Q23 below record the approved
rules in English; the user explicitly requested keeping the remaining uncertainties.
This evidence supersedes the initial checkpoint's all-TBD treatment only for the
specified rules. It does not globally accept the catalog or authorize stage 06.

## U06 - Baseline acceptance and CU09 proposal authorization

Recorded on 2026-11-07 from the user's current conversation instruction beginning
“Leé AGENTS.md, docs/STATE.md, la ficha CU09 y el registro de decisiones”. The user:

- Explicitly accepts the catalog, shared rules, register and workflow as the stage
  05 documentary baseline, and selects CU09 as the first stage 06 development.
- Confirms that the teacher approved all ten Energía Sur use cases: Q00 is approved
  on that user confirmation. The teacher's approval date and channel were not
  provided and are not recorded. The record date is not a teacher-approval date.
- Approves CU09 Buenos Aires time/minute recording, future-date rejection,
  end-after-start validation, positive-duration inclusion and hours/minutes totals;
  owner-account-only save/view/correct/close/export, including correction of open
  and closed cuts; descending-start PDF table and exact missing-end text “En curso”.
- Authorizes the CU09 OpenSpec proposal for review, not Apply or implementation.
  Auth mechanism, persistence integration and PDF generation still need design approval.

This evidence supersedes U05's remaining CU09 policy TBDs and prior missing-Q00/
candidate-only/global-Review blockers. It does not resolve unrelated CU questions.

## U07 - CU09 Apply and technical-package approval

The current user message explicitly approves the CU09 proposal and recommended
D0-D5 options, requests Apply/backend/frontend/minimum CU04, QA and independent
review, and permits independent work around real scoped blockers. In the subsequent
question the user chose **“Aprobar paquete técnico (Recommended)”**: optimistic
409 versioning, specified input limits, Python scrypt, eight-hour opaque sessions,
cookie/CSRF/Origin rules, compatible stable dependency pinning, Unicode ReportLab
PDFs, Playwright/pypdf, Ruff/mypy and compatible ESLint tooling. Exact accepted
contract/pins are in the linked OpenSpec contract. U08 later replaced the
incompatible ESLint/typescript-eslint choice with Oxlint 1.92.0. This is not
commit/push/Archive or deployment permission. It does not waive failed/incompatible
mandatory checks.

## U08 - CU09 historical floor and frontend lint alternative

Recorded on 2026-11-07 from the user's answers to the two blocking-decision
questions:

- Approves **1970-01-01 00:00 Buenos Aires** as the minimum accepted time for cut
  and report-period inputs. Earlier values return a sanitized 422. This replaces
  unbounded historical support so pre-standard offset seconds and fractional
  elapsed minutes are excluded rather than rounded or serialized approximately.
- Approves **Oxlint 1.92.0** as the pinned frontend lint gate, preserving TypeScript
  7.0.2 because stable typescript-eslint still requires TypeScript `<6.1.0`.

This is an implementation-contract decision, not commit/push/Sync/Archive or
deployment permission, and it does not waive any remaining check.

## U09 - Login boundary clarification and frontend-foundation direction

The user explicitly approves clarifying CU09 login as backend-enforced trusted
allowed Origin only (no pre-authentication CSRF token), with CSRF plus Origin
retained for authenticated unsafe operations. This resolves independent finding M1;
regressions and recheck evidence belong in the CU09 engineering record.

The user also approves the frontend-foundation direction as a separate change:
reuse Vite/React/TypeScript; Tailwind and local shadcn/ui components; Zustand;
React Hook Form/Zod; centralized Axios with auth/CSRF interceptors; adopt CU09 first;
one floating-chat mount in the root layout, with LangChain/streaming deferred to
CU03. Installed OpenSpec workflow requires proposal review before a subsequent
Apply request. No Archive/commit/push is authorized.

## U10 - Frontend foundation Apply authorization

After the foundation artifacts were presented, the user explicitly requested
"Aplicá establish-frontend-foundation". This authorizes implementation of the
existing proposal/design/specs/tasks and the approved exact dependency direction,
not Archive, commit, push, deployment, destructive cleanup or CU03 runtime work.
The previous canceled attempt only performed read-only inspection; implementation
starts on this subsequent request. Preserve U09's already verified CU09 security
clarification without reopening it as a pending policy decision.

## U11 - CU04-scoped decisions and proposal authorization

Recorded from the user's 2026-11-08 instruction beginning "Rol: Modo PROPOSE estricto". The user approves the CU04-only Q03/Q08/Q09 rules below, additive migration after `0001_cu09`, optimistic concurrency, composite ownership FK and frontend composition, and authorizes the `manage-cu04-domiciles-meters` proposal and this documentation update. This is not acceptance of the complete artifacts, Apply, test execution, migration, sync, archive, commit or push. Alias validation and exact Unicode comparison are proposed refinements for human review. No approval extends these rules to other CUs.

## U12 - CU04 contract refinements and conditional Apply

Recorded from the user's current instruction beginning “Continuá el cambio OpenSpec `manage-cu04-domiciles-meters`”. The user approves for CU04: meter number required, 1–120 after trimming ASCII spaces, printable ASCII only, no controls or NUL; preserve leading zeroes, signs and internal spaces; ASCII lowercase uniqueness per account, including across domiciles, enforced consistently by backend and PostgreSQL under concurrency. Alias is optional null or trimmed text up to 120 characters, blank becomes null, controls/NUL rejected, Spanish accents allowed; it is not part of uniqueness. The six routes in the CU04 design are approved while existing domicile GET/POST stay unchanged. CU04 409 codes are `DUPLICATE_METER` and `VERSION_CONFLICT`, not message-based classification.

The user distinguishes physical meter number from customer number; a customer number often has 7–10 digits and can appear on the bill, but that is not a validation constraint. No `customer_number` persistence is approved. Its possible CU06 need is a future question and does not block CU04.

The user authorizes Apply of this change only after documentary validation, traceability and independent review pass without blockers or unresolved functional decisions. No sync, archive, commit or push is authorized.

## U13 - CU05 functional decisions and propose authorization

Recorded from the user's current instruction beginning “Rol: Modo PROPOSE (OpenSpec)”, together with the preceding CU05 OCR instruction. **CONFIRMED, CU05 only:** a required nonnegative integer kWh value and date no later than today; warn but allow decreasing readings; allow same-day readings at different times but reject identical date/time; allow editing value/date/photo but not reading deletion; retain stable meter ID and newest-first history. A photo is optional, at most one, JPG/PNG/WebP, maximum 5 MB. Photo bytes live in a persistent Docker volume managed by FastAPI, PostgreSQL stores metadata only, and access requires account ownership; no S3 or Cloudinary. On user request, OCR attempts the kWh register, excluding red fractional digits; a reliable result is editable and never auto-saved. Explicit confirmation is mandatory. On failure or low confidence, no suggestion and the exact message “No pudimos identificar con seguridad la lectura del medidor. Intentá subir una fotografía más clara o ingresá manualmente el valor en kWh” are required; manual entry remains available. No independent blur detector.

**Subsequent clarification:** D01–D13 below approve local Tesseract/manual crop, UTC seconds, per-meter uniqueness and selected photo/concurrency rules. Residual contract details remain in the [design](../../openspec/changes/record-cu05-meter-readings/design.md). U13 supersedes U06's CU05 photo-required/no-OCR baseline only; it does not settle other CUs or authorize Apply, installation, migrations, Sync or Archive.

## CU05 D01–D13 - Approved documentary review decisions

Recorded from the user's instruction beginning “Rol: Modo REVIEW documental (OpenSpec)”. The user supplied the identifiers in groups, not a one-to-one mapping; this register preserves that grouping rather than inventing individual assignments.

- **D01, D02, D03, D04, D10 — OCR and processing:** Docker-local Tesseract without external APIs, manually cropped region, opt-in editable suggestion and confirmation, exact U13 fallback on failure or uncertainty, 5 MB limit, no automatic retries. Only the example photo supplied via a simulated local path may be used for OCR image tests; it must not enter Git or artifacts. Distinguish success, abstention, engine failure and coverage limits. No sample path or photo was supplied in this review.
- **D05, D06, D07 — time/data:** persist UTC normalized to seconds; display America/Argentina/Buenos_Aires; no future dates; PostgreSQL uniqueness per meter and exact instant; warning but allow confirmed decreasing readings; no physical replacement.
- **D08, D09, D13 — files/storage:** OCR temporary photos remain in memory, not persisted before confirmation. Retain the old photo through successful replacement transaction and clean it afterward; coordinate simple Docker volume and PostgreSQL backups. The subsequent technical review proposes a concrete crash-safe protocol requiring independent review and runtime verification.
- **D11, D12 — API/concurrency:** meter-scoped REST and separate OCR endpoint; authenticated private photo access, Origin/CSRF and CU04 ownership isolation; every PATCH, including unchanged, checks and increments version, stale versions return 409 `VERSION_CONFLICT`.

These decisions preserve U13 and CU04/CU09; they do not authorize APPLY, tests, installation, migrations, Sync, Archive, commit or push. A single image does not prove representative OCR accuracy; residual safety and executable-contract gaps are tracked in design.

## CU05 technical review clarification

In the subsequent technical-review request and confirmation, the user selected **always abstain when a red fractional digit is detected**, even if separable; this supersedes only the earlier CU05 scenario suggesting the black digits in that case. The user confirmed for the proposed contract 5,000,000 bytes, 20 million pixels, 5 seconds, 256 MiB per engine process, one concurrent OCR job, immutable durable objects before versioned DB publication, coordinated cleanup and paused-write backup, meter-scoped routes and offset-aware second-resolution timestamps rejecting fractions and future instants. Exact payloads and recovery refinements are documented in [design](../../openspec/changes/record-cu05-meter-readings/design.md) for review. This does not authorize implementation, tests, installation or migration; an OCR suggestion still requires reliable identification, and missing evidence cannot be waived by confirmation.

## CU05 D14–D15 and BUILD authorization

The user subsequently authorized BUILD and approved **D14:** decimal-string `value_kwh` throughout APIs/frontend and exact PostgreSQL storage, including OCR; **D15:** stable account/meter/payload-scoped transactional create idempotency, with `409 IDEMPOTENCY_KEY_REUSED` for the same key and different payload. On a subsequent technical-limit question the user approved at most 131072 ASCII digits, with 422 above the limit. Synthetic image tests are authorized; the real photograph is not available and its test remains pending without blocking BUILD solely for that reason. No Sync, Archive, commit, push or other CU is authorized. See [design](../../openspec/changes/record-cu05-meter-readings/design.md) for transport details.

## CU05 photo validation clarification

During photo implementation the user approved declaring the existing locked Pillow 13.0.0 as a direct dependency and a separate maximum of 40,000,000 decoded pixels per image frame for stored photos. The existing 20,000,000-pixel OCR limit remains unchanged; the 5,000,000-byte photo limit still applies. This does not approve unbounded in-process decoding, external transfer or any weakening of photo isolation.

## CU05 M1 - OCR may abstain (closure decision)

The user resolved M1 from the independent review: the OCR may abstain whenever it cannot identify the reading with sufficient confidence, without adding unnecessary complexity or claiming unverified precision. Manual kWh entry and explicit confirmation always remain available and authoritative. The fail-closed implementation that returns the exact U13 fallback without invoking Tesseract is therefore accepted for closure, and the delta spec/design were revised to permit safe abstention. A future suggestion requires documented register-identity and red-fraction evidence; a real meter photo and representative accuracy remain pending and are not approved. No Sync, Archive, commit or push is authorized by this decision.

## U14 - CU07 revised matching and comparison authorization

Recorded on 2026-11-09 from the user's instruction beginning "Continuá el PROPOSE de
CU07 con las nuevas decisiones funcionales aprobadas". The user **replaces** the
exact-boundary rule of Q13/CU07-R1 with:

- Compare CU05 readings with structured CU06 bill data only, always for the same
  meter and owning account.
- Exact boundary dates compare directly.
- Otherwise allow an approximate comparison only with explicit confirmation in a
  modal.
- Accept readings whose `America/Argentina/Buenos_Aires` local date is within ±7
  days inclusive of each billed-period boundary.
- When multiple candidate readings exist, the user must manually select the start and
  end readings.
- Do not interpolate, prorate or estimate consumption.
- Show the real reading dates and a visible warning when the periods differ.
- Do not calculate when compatible readings are missing or the end reading is lower
  than the start reading.
- Show recorded consumption, billed kWh and the exact kWh difference, with no
  percentage.
- Keep CU07 read-only: no new tables, migrations or PDF extraction.

The user also requires a simple candidate/confirmation contract validated in the
backend (selected IDs, dates, ownership and confirmation), not only in the modal, and
requests tests for exact match, 7/8-day tolerance, multiple candidates, confirmation,
zero consumption, decreasing readings and cross-account isolation. This authorizes
the CU07 proposal and documentation update for review; it does not authorize Apply,
code, migrations, Sync, Archive, commit or push.

## U15 - CU08 consumption evolution and estimate PROPOSE authorization

Recorded on 2026-11-09 from the user's current instruction beginning "Rol: Modo
PROPOSE ESTRICTO (OpenSpec)" for CU08. The user confirms eleven decisions
(D01–D11) for CU08 only and authorizes the `view-cu08-consumption-evolution-and-estimates`
proposal and this documentation update for review; this is not Apply, code,
installation, migration, Sync, Archive, commit or push.

**CONFIRMED, CU08 only:**

- **D01:** deterministic estimate = (daily average of the last valid interval) × chosen days; no AI or historical averages. "Last valid interval" = the last chronological interval (two most recent readings by `recorded_at` UTC), validity reused from CU05 per R01.
- **D02:** manual 1–90 day horizon selector.
- **D03:** irregular intervals use real elapsed time between readings; no exact-month requirement.
- **D04:** decreasing readings shown as "not calculable" (no negative consumption, not an estimate base) without blocking the rest of the history.
- **D05:** internal UTC computation (including same-day readings); UI in `America/Argentina/Buenos_Aires`.
- **D06:** zero-kWh intervals and zero-kWh estimates are accepted.
- **D07:** two separate views — real consumption (kWh) and daily average (kWh/day) — with a clear visual distinction between historical and estimated.
- **D08:** source is CU05 readings only; no CU06 bills or CU07 rules mixed in.
- **D09:** backend uses `Decimal`; UI shows two decimals plus the warning "orientativa, no facturada".
- **D10:** filter by own meter and date range with account isolation.
- **D11:** evaluate Recharts in `design.md`; on stack conflicts, propose alternatives and leave the chart library as TBD.

**Residual TBDs (resolved by R01–R07 below):** the seven items — (1) strict
"valid reading" definition, (2) behavior on a decreasing last interval, (3)
corrected/out-of-order/replaced readings, (4) extreme projections from very short
intervals, (5) visual filter rule on range-crossing intervals, (6) rounding vs.
real zeros, (7) UI with 0/1/no valid pair — are now approved as R01–R07 and
recorded immediately below.

This resolves Q15 (projection formula via D01, base selection via R01–R03) and Q16
(period limit via D02, presentation/filter/empty-state via R04–R07); the chart
library remains TBD under D11.

## CU08 R01-R07 - Approved residual decisions

Recorded on 2026-11-09 from the user's current instruction beginning "Rol: Modo
REVIEW FINAL Documental (OpenSpec)". The user approves the seven residual decisions
for CU08 only and authorizes updating the PROPOSE artifacts for human review; this
is not Apply, code, installation, migration, Sync, Archive, commit or push.

- **R01:** reading validity is reused from CU05 (confirmed stored readings: nonnegative integer, nonfuture, second-resolution UTC); no additional CU08 filter.
- **R02:** if the last chronological interval is decreasing, no estimate is shown and older intervals are NOT searched as a fallback base; historical decreasing intervals remain visible as "not calculable".
- **R03:** readings are always ordered by `recorded_at` UTC using current stored values (edits included); physical meter replacement is not managed.
- **R04:** sub-24-hour intervals are still computed but flagged in the UI as "poco representativo" (not representative).
- **R05:** date-range filtering uses inclusive overlap; an interval that crosses or touches the range is included whole, with its real endpoint dates visible, without clipping, interpolation or proration.
- **R06:** a computed value that is positive but rounds to "0.00" at two decimals is shown as "< 0.01" so it is not confused with a real zero; `Decimal` is used without loss and the two-decimal display uses half-up rounding.
- **R07:** zero or one reading shows an empty state with no estimate.

These complete CU08's functional decisions alongside D01–D11. The chart library
remains TBD under D11.

## Confirmed facts versus inferences

### CU05 subsequent OCR BUILD instruction

The user subsequently requires a real local Tesseract attempt on the manually selected register region, and permits excluding clearly separable red fractional digits; uncertain results still abstain and require manual confirmation. This supersedes the earlier always-abstain-on-red rule and the M1 permission to close without invoking Tesseract. Previously approved security and resource limits remain unchanged. Synthetic tests are authorized; a real local photo remains pending. No Sync, Archive, commit or push is authorized.

### CU05 worker security acceptance

The user subsequently accepts the OCR worker security topic and requests documenting abstention on the supplied real photograph as a known limitation. This records human acceptance, not an assertion that a new independent review occurred or that resource/privacy safeguards were waived. The user has not authorized Sync, Archive, commit or push.

- **C:** React/TypeScript, Vite/npm, FastAPI/Uvicorn/uv and PostgreSQL in Docker
  are decided in the [Docker design](../../openspec/changes/docker-development-environment/design.md).
  Driver, ORM, migrations and application/database connection are excluded there.
- **C:** backend LangChain + OpenAI is the assistant direction, not installed
  business functionality. CU09/CU04 use approved server sessions and PostgreSQL;
  hosting and persistent assistant memory remain TBD. CU09 tooling approvals
  and Oxlint under U08 are recorded in the corresponding contract.
- **C:** [MCP evidence](../ai-engineering/configure-readonly-development-mcp.md)
  records GitHub read-only and Context7 development calls. That is not proof of
  chat functionality or a fresh permission/token audit.
- **U05:** exact-date matching/no comparison without matches, kWh difference with
  direction/equality, latest valid reading pair, interval grouping, own-account
  domicile required to save, overlap union, report clipping/effective open-cut end
  and PDF content are approved as detailed below. No interpolation is authorized.
- **U06:** stage 05 baseline acceptance, academic Q00 confirmation and the bounded
  CU09 policies above are approved; CU09 is chosen for stage 06 proposal review.
- **I/TBD:** CU08 projection and unrelated reading/period rules are not inferred
  from CU09/CU04 approvals.
- **Historical stage 05:** the earlier checkpoint had zero main specs. CU04/CU09
  now have archived changes and current main specs; see [STATE](../STATE.md).
  A checked task or structural PASS cannot approve unimplemented fiches.

## Questions, motivation and blocked scope

### Q00
**APPROVED - academic prerequisite, U06:** the user confirms that the teacher
approved the ten Energía Sur use cases. The academic prerequisite is satisfied on
that confirmation; no teacher approval date or channel is recorded.
**Pending:** none for Q00; proposed design/implementation approval is a separate gate.
**Impact:** Q00 no longer blocks CU09 or the other CUs; it does not authorize Apply.

### Q01
**TBD - CU01:** Which address/device/locality inputs and GeoRef resolution/coverage
are supported? Needed to define matching; blocks CU01-S01's exact search oracle.

### Q02
**TBD - CU01/CU02:** What happens on ambiguous location, unavailable geolocation
or denied consent? Avoid implicit fallback/permission requests; blocks CU01-S02
and CU02-S02's location-error behavior.

### Q03
**PARTIAL - CU04-CU09. Approved for CU09 by U06:** only the account with the registered
domicile may save, view, correct, close or export its cuts (Q18).
U07/U07-T approve opaque server sessions, controlled provisioning and the contract's
cookie/CSRF/hash details for CU09 and its minimum CU04 slice.
**U11, CU04:** a domicile belongs to one account and a meter to one domicile; ownership is checked via that domicile's account. Only its owner manages either using the existing opaque session; writes require trusted Origin and CSRF. Foreign or nonexistent resources return 404. No roles or Edesur ownership verification are introduced.
**Pending:** other CUs' roles/ownership behavior remains unspecified. CU04's historical isolation checks and review are recorded in [STATE](../STATE.md); CU05 requires its own independent review and isolation evidence.

### Q04
**TBD - CU01/CU02/CU03/CU10:** Which official endpoints, terms, coverage and refresh
provenance are usable, and how are last attempt and last successful update exposed?
Blocks reliable live-data and CU10-S01/S02 acceptance; no connector is presumed.

### Q05
**TBD - CU02:** What upcoming horizon, date-range boundaries, timezone, distance
definition and nearby threshold apply? Needed for filters/proximity; blocks
CU02-S01/S03's exact results.

### Q06
**TBD - CU03:** Which official guides and retrieval/citation granularity are accepted?
Needed for grounding; blocks CU03-S01's source acceptance oracle.

### Q07
**TBD - CU01/CU02/CU03:** What staleness threshold and unavailable-source behavior
are approved? Blocks CU01-S03, CU02-S02 and CU03-S02's exact fallback responses.
The no-invention constraint remains in force without selecting that UX.

### Q08
**PARTIAL - CU04:** U07/U07-T approve the CU09 prerequisite's stable domicile ID,
account binding and trimmed 1-300-character display_address, register/list/select,
without a meter or legal-address verification.
**U11, CU04:** a domicile has zero to many meters, each with a stable ID, number and optional alias. Number is 1–120 characters after trim, case-insensitive for uniqueness, and excludes NUL; uniqueness is per account. Duplicate domiciles remain allowed with a UI warning. Existing meter-free CU09 use is preserved.
**U12:** approved ASCII-only number normalization, alias validation and per-account concurrent uniqueness are specified above. No approval is implied for other CUs or physical-meter identity verification.

### Q09
**PARTIAL - CU04-CU09. Approved for CU09 by U06:** the owner account can correct
open and closed cuts using the same date validation, and close ongoing cuts.
**U11, CU04:** correct address, meter number and alias without changing IDs; do not delete, transfer or physically replace domiciles/meters. CU09 cuts retain their domicile ID; future PDFs display the current address.
**U13, CU05:** reading correction is allowed, reading deletion is not; photo edit is allowed and its detailed lifecycle remains TBD. **CU06:** the user approved bill correction without bill deletion or domicile/meter reassignment; see Q12. **Pending:** broader reassignment/deletion, physical meter replacement, retention and other linked-file policies; reopening a closed cut by removing its end remains unspecified.

### Q10
**PARTIAL - CU05, U13 and D05–D07:** nonnegative integer kWh, nonfuture date, warning without blocking decreases, UTC seconds displayed in Buenos Aires, and uniqueness per meter/exact instant. **TBD:** timestamp input and future-instant interpretation, warning comparator, equal/out-of-order readings, rollover and CU07 implications. **CU08 resolved by R01/R03:** CU08 reuses CU05 validity and orders by `recorded_at` UTC with current values, without managing physical replacement.

### Q11
**PARTIAL - CU05, U13 and D01–D04/D08–D10/D13:** optional single photo, JPG/PNG/WebP up to 5 MB; private volume and PostgreSQL metadata; opt-in local Docker Tesseract and manual crop, in-memory preconfirmation processing, explicit confirmation and manual fallback. **TBD:** confidence oracle, byte convention, decoded limits, crash recovery and detailed errors. No external photo transfer is approved.

### Q12
**PARTIAL - CU06, user PLAN instruction:** start and end dates are required and start
must not follow end; billed kWh is nonnegative with up to three decimal places; one
PDF/JPG/PNG file up to 5 MB is required; ARS amount is optional with up to two decimal
places. Reject identical meter/period duplicates; warn about overlaps but allow explicit
confirmation. Permit correction of period, kWh, amount and file with stable bill ID;
no domicile/meter change or deletion. Access is private and account-isolated. No OCR,
automatic extraction, tariff calculation or CU07 comparison. These functional decisions
are approved by the user's conversation, not inferred from other CU approvals.

**Proposed for Review, user PROPOSE instruction:** inclusive endpoints, 5,000,000-byte
limit, nonnegative ARS amount, private storage and safe validation, duplicate/overlap
concurrency and optimistic versioning. The [CU06 design](../../openspec/changes/archive/2026-11-09-record-cu06-electricity-bills/design.md)
sets out exact protocols and numeric limits. The user subsequently approved Review and
Apply, selected `pypdf` for bounded PDF validation and explicitly accepted its documented
limitations. Runtime verification and the single independent implementation review passed;
the change was archived on 2026-11-09 and the [main specification](../../openspec/specs/electricity-bills/spec.md)
is synchronized. Q13's exact boundary-date rule is preserved.

### Q13
**SUPERSEDED - CU07, U14 (replaces the U05 exact-match rule):** candidate readings
are those of the same meter whose Buenos Aires local date is within ±7 days
inclusive of each billed boundary. Exact boundary dates compare directly; other
in-window pairs require explicit confirmation. No tolerance beyond ±7 days,
interpolation or proration is authorized.
**Pending:** no matching alternative remains open. Reading validity (Q10),
bill-period representation (Q12) and auth (Q03) remain separate dependencies.
**Impact:** CU07-S01-S05 and the U14 scenarios have determinate matching outcomes;
multiple candidates require manual selection (U14).

### Q14
**PARTIAL - CU07, U05 + U14. Approved:** display recorded consumption, billed kWh and
the exact difference in kWh, identifying whether recorded or billed consumption is
higher, or that there is no difference. **Percentage is explicitly excluded.**
**Pending:** exact Spanish wording/rounding of warnings and no-comparison messages
remains a presentation detail under Q14.
**Impact:** CU07-S01/S04/S05 and the U14 scenarios cover recorded-higher,
billed-higher, equality and zero consumption; fractional values are displayed
exactly without a percentage.

### Q15
**PARTIAL - CU08, U05. Approved:** use the two latest valid readings of the same
meter as the estimation base.
**Pending:** resolved by U15/D01 and R01–R03 — the base is the last chronological
interval (two most recent readings by `recorded_at` UTC, current values); a
decreasing latest interval yields no estimate with no fallback to older intervals.
Latest-pair selection does not approve linear extrapolation beyond the horizon.
**Impact:** CU08-S02 has a determinate base-selection and projection outcome;
validity is reused from Q10/CU05 as-is (R01).

### Q16
**PARTIAL - CU08, U05. Approved:** show evolution by interval between readings,
with interval consumption in kWh and daily average in kWh/day.
**Pending:** resolved by U15/D01–D05 and R04–R07 — the 1–90 day horizon, real
elapsed time, UTC/Buenos Aires, the sub-24-hour "poco representativo" flag, the
inclusive-overlap filter, the "< 0.01" presentation and the 0/1-reading empty state
are all decided. Exact Spanish wording of warnings remains a presentation detail.
**Impact:** CU08-S01/S02/S03 have determinate outcomes; the projection formula and
presentation rules are now set.

### Q17
**APPROVED - CU09, U06:** use Buenos Aires local time and record times to the minute.
Reject future cut dates; if an end is supplied it must be strictly after the start.
The owner may correct both open and closed cuts under the same date validation,
and close ongoing cuts. Summary effective ends do not modify stored closure.
**Pending:** no timezone/minute/date-validation/correction-policy alternative remains
in Q17; U07/U07-T accept the named-zone/minute payload, server clock and optimistic
concurrency contract. U08 explicitly sets the minimum at 1970-01-01 00:00 Buenos
Aires and rejects earlier inputs with 422, so ancient second-level offset transitions
are excluded rather than silently rounded or handled by an approximate transport.
Reopening by clearing a closed end remains Q09, not an inferred permission.
**Impact:** CU09-S01/S02/S10/S11/S12 now have determinate policy outcomes.

### Q18
**APPROVED - CU09, U05 + U06:** saving requires selecting a domicile registered in
the account. Only that account may save, view, correct, close and export its cuts.
No selection/another account's domicile fails the save requirement; all listed
cross-account actions are forbidden. No household sharing is authorized.
**Pending:** no action-matrix alternative for these five operations; session/enforcement
design is approved for CU09 by U07/U07-T, and domicile reassignment/deletion remains Q09.
**Impact:** CU09-S03/S09 define allowed/forbidden operations; implementation still
needs actual auth/persistence/isolation verification, not a new ownership policy.

### Q19
**APPROVED - CU09, U05:** keep both overlapping records. For one domicile's total,
count shared time only once: 10:00-12:00 and 11:00-13:00 total **3 hours**.
**Pending:** no retain-versus-reject or sum-versus-union choice remains in Q19.
U06 fixes minute precision and hours/minutes totals; this does not reopen union counting.
**Impact:** CU09-S04/S06 have determinate record-retention and total-hours outcomes.

### Q20
**APPROVED - CU09, U05 + U06:** count only the segment inside the queried period.
For an ongoing cut, use the earlier of summary-generation time and period end as
effective end. A cut from 31 October 23:00 to 1 November 02:00 contributes **2 hours**
to November. Apply same-domicile union counting (Q19) to the clipped segments.
Use Buenos Aires minute-resolution time, exclude cuts without positive duration
inside the period, and display the total in hours and minutes. A boundary-touching
cut contributing zero minutes is excluded. Keep union counting per domicile.
**Pending:** no clipping/effective-end/inclusion/unit alternative remains in Q20;
period input/clock/concurrency recommendations and refinements are approved by
U07/U07-T. U08 resolves the ancient second-offset/fractional-minute edge described
in Q17 by rejecting inputs before 1970-01-01 00:00 Buenos Aires with 422; the
fractional-minute guard remains defense in depth for stored or out-of-band data.
**Impact:** CU09-S04/S05/S07/S08/S13/S14 have concrete results; summary effective end
never closes the cut. Q17 separately authorizes owner closure/correction.

### Q21
**TBD - CU10:** How is the administrator role assigned and checked, and which actions
are allowed? Blocks CU10-S03 and access preconditions for CU10-S01/S02. Public chat
must not gain privileged development or administration tools.

### Q22
**TBD - CU10:** Which sources are enabled and what interval bounds, retry/backoff and
concurrent-run rules are permitted? Blocks CU10-S02's precise reconfiguration/retry oracle.

### Q23
**PARTIAL - CU09, U05 + U06. Approved:** the PDF includes domicile, period, dates, times
and status of each interruption, and total hours without service. Include observations
and complaint number when supplied. Use a table ordered by start descending;
the end column reads exactly “En curso” when no closure exists. Total is hours/minutes.
U07/U07-T approve ReportLab on-demand delivery, packaged Unicode font, row splitting
and repeated headers. No persistent PDF files are required by the application.
**Pending:** cosmetic styling and any extra per-cut contribution breakdown beyond
the accepted fields; no generator/library decision remains open. Actual downloaded
PDF inspection is verification evidence, not a repeated stack decision.
**Impact:** CU09-S06/S07/S15 define content/order/ongoing text; U07-T approved the
technical generation stack recorded in the contract, not a new permission matrix.
A report supports a complaint; it does not submit it or guarantee utility acceptance.
