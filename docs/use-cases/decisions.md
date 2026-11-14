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

**Subsequent clarification:** D01–D13 below approve local Tesseract/manual crop, UTC seconds, per-meter uniqueness and selected photo/concurrency rules. Residual contract details remain in the [design](../../openspec/changes/archive/2026-11-13-record-cu05-meter-readings/design.md). U13 supersedes U06's CU05 photo-required/no-OCR baseline only; it does not settle other CUs or authorize Apply, installation, migrations, Sync or Archive. Its red-fraction wording (“excluding red fractional digits”) is refined, not repealed, by the [2026-11-13 resolution](#cu05-red-fraction-contract-resolution-2026-11-13): exclusion applies only when the fraction is clearly separable, and no absolute guarantee is claimed.

## CU05 D01–D13 - Approved documentary review decisions

Recorded from the user's instruction beginning “Rol: Modo REVIEW documental (OpenSpec)”. The user supplied the identifiers in groups, not a one-to-one mapping; this register preserves that grouping rather than inventing individual assignments.

- **D01, D02, D03, D04, D10 — OCR and processing:** Docker-local Tesseract without external APIs, manually cropped region, opt-in editable suggestion and confirmation, exact U13 fallback on failure or uncertainty, 5 MB limit, no automatic retries. Only the example photo supplied via a simulated local path may be used for OCR image tests; it must not enter Git or artifacts. Distinguish success, abstention, engine failure and coverage limits. No sample path or photo was supplied in this review.
- **D05, D06, D07 — time/data:** persist UTC normalized to seconds; display America/Argentina/Buenos_Aires; no future dates; PostgreSQL uniqueness per meter and exact instant; warning but allow confirmed decreasing readings; no physical replacement.
- **D08, D09, D13 — files/storage:** OCR temporary photos remain in memory, not persisted before confirmation. Retain the old photo through successful replacement transaction and clean it afterward; coordinate simple Docker volume and PostgreSQL backups. The subsequent technical review proposes a concrete crash-safe protocol requiring independent review and runtime verification.
- **D11, D12 — API/concurrency:** meter-scoped REST and separate OCR endpoint; authenticated private photo access, Origin/CSRF and CU04 ownership isolation; every PATCH, including unchanged, checks and increments version, stale versions return 409 `VERSION_CONFLICT`.

These decisions preserve U13 and CU04/CU09; they do not authorize APPLY, tests, installation, migrations, Sync, Archive, commit or push. A single image does not prove representative OCR accuracy; residual safety and executable-contract gaps are tracked in design.

## CU05 technical review clarification

In the subsequent technical-review request and confirmation, the user selected **always abstain when a red fractional digit is detected**, even if separable; this supersedes only the earlier CU05 scenario suggesting the black digits in that case. The user confirmed for the proposed contract 5,000,000 bytes, 20 million pixels, 5 seconds, 256 MiB per engine process, one concurrent OCR job, immutable durable objects before versioned DB publication, coordinated cleanup and paused-write backup, meter-scoped routes and offset-aware second-resolution timestamps rejecting fractions and future instants. Exact payloads and recovery refinements are documented in [design](../../openspec/changes/archive/2026-11-13-record-cu05-meter-readings/design.md) for review. This does not authorize implementation, tests, installation or migration; an OCR suggestion still requires reliable identification, and missing evidence cannot be waived by confirmation.

**Historical — superseded.** The always-abstain-on-red rule was replaced by the subsequent OCR BUILD instruction (exclude clearly separable red fractions, abstain on an uncertain boundary) and finally settled by the [2026-11-13 red-fraction resolution](#cu05-red-fraction-contract-resolution-2026-11-13). The paragraph is retained as decision history; it is not a current normative rule.

## CU05 D14–D15 and BUILD authorization

The user subsequently authorized BUILD and approved **D14:** decimal-string `value_kwh` throughout APIs/frontend and exact PostgreSQL storage, including OCR; **D15:** stable account/meter/payload-scoped transactional create idempotency, with `409 IDEMPOTENCY_KEY_REUSED` for the same key and different payload. On a subsequent technical-limit question the user approved at most 131072 ASCII digits, with 422 above the limit. Synthetic image tests are authorized; the real photograph is not available and its test remains pending without blocking BUILD solely for that reason. No Sync, Archive, commit, push or other CU is authorized. See [design](../../openspec/changes/archive/2026-11-13-record-cu05-meter-readings/design.md) for transport details.

## CU05 photo validation clarification

During photo implementation the user approved declaring the existing locked Pillow 13.0.0 as a direct dependency and a separate maximum of 40,000,000 decoded pixels per image frame for stored photos. The existing 20,000,000-pixel OCR limit remains unchanged; the 5,000,000-byte photo limit still applies. This does not approve unbounded in-process decoding, external transfer or any weakening of photo isolation.

## CU05 M1 - OCR may abstain (closure decision)

The user resolved M1 from the independent review: the OCR may abstain whenever it cannot identify the reading with sufficient confidence, without adding unnecessary complexity or claiming unverified precision. Manual kWh entry and explicit confirmation always remain available and authoritative. The fail-closed implementation that returns the exact U13 fallback without invoking Tesseract is therefore accepted for closure, and the delta spec/design were revised to permit safe abstention. A future suggestion requires documented register-identity and red-fraction evidence; a real meter photo and representative accuracy remain pending and are not approved. No Sync, Archive, commit or push is authorized by this decision.

**Historical in part — superseded.** The subsequent OCR BUILD instruction required a real Tesseract attempt, and the [2026-11-13 resolution](#cu05-red-fraction-contract-resolution-2026-11-13) settled the red-fraction contract. M1's core principle is preserved: safe abstention remains valid and manual entry/confirmation remain authoritative.

## CU05 red-fraction contract resolution (2026-11-13)

**Approved rule (definitive):** the OCR may mask red fractional digits that are clearly separable and suggest only the remaining integer reading when the integer/fraction boundary is unambiguous. When that boundary is uncertain, the OCR must abstain and return the approved fallback message. An OCR suggestion is never saved automatically: the owner must review and manually confirm the value before it enters the history. The system does not guarantee detecting every fractional digit, especially when its colour is ambiguous, faded or indistinguishable from the integer digits. Explicit manual confirmation is mandatory.

**Supersession:** this decision replaces only the absolute interpretation that the OCR could never accidentally include a fractional digit. It supersedes the "always abstain when a red fractional digit is detected" clarification above and the delta's unconditional prohibition, and it preserves the subsequent OCR BUILD instruction's conditional exclusion, M1's safe abstention and U13's manual-confirmation authority. It does not change the requirement to store accumulated readings as nonnegative integer kWh, and it does not change the CU07/CU08 contracts, which consume previously confirmed and persisted readings.

**Why documentation changed, not software:** `backend/app/ocr_worker.py` implements heuristic colour masking and abstains when a red region is not strictly to the right of all integer ink; `backend/tests/test_ocr_worker.py` covers clearly separable red exclusion and ambiguous-boundary abstention. Fixed thresholds cannot prove that every fractional digit is detected, so the software already matched this decision and only the documentary guarantee was wrong.

**Scope and authorization:** this resolution is documentation-only; no backend, OCR, frontend or test behavior was modified. The 2026-11-13 instruction explicitly authorized the documentation correction, the OpenSpec validation, the sequential Sync/Archive of both CU05 changes (base change first, isolation second) and the documentation updates, and prohibited commit and push; no commit or push was performed. Sync/Archive outcome (18 + 3 = 21 requirements, 38 + 6 = 44 scenarios) is recorded in [STATE.md](../STATE.md) and the [engineering record](../ai-engineering/record-cu05-meter-readings.md).

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

## U16 - CU01 current outages decisions and traceability

Recorded from the user's 2026-11-10 REVIEW/REVISE instructions for CU01, which approved the
complementary decisions T1–T3 and required the independent-review fixes. The user approved
for **CU01 only**:

- **D1:** HTTPS with a legacy-TLS `SSLContext` isolated to the ENRE client, keeping certificate
  and hostname verification.
- **D2:** query by partido, localidad and address via GeoRef.
- **D3:** show medium-tension, low-tension and preventive categories when applicable, without
  presuming all are active; programmed cuts stay in CU02.
- **D4:** a verifiable Edesur coverage catalog combined with ENRE data.
- **D5:** PostgreSQL stores the last valid snapshot, its normalized records and execution history.
- **D6:** an initial five-minute refresh via the backend scheduler, coordinated with a PostgreSQL
  advisory lock.
- **D7:** `httpx` + JSON5, conditioned on demonstrated compatibility with the real JavaScript;
  never execute remote code.
- **D8:** freshness fresh ≤15 min, stale ≤60 min, unavailable >60 min or no valid data; keep the
  last valid snapshot on failure or `N/A`.
- **D9:** browser geolocation with consent and reverse geocoding, without persisting unnecessary
  coordinates.
- **D10:** show the official global total and per-record figures, without summing localities or
  deduplicating via unverified heuristics.
- **D11:** public access and differentiated states: loading, reported outages, no reports, stale,
  unavailable, out of coverage, geographic errors.
- **T1:** GeoRef is centralized in the backend, mandatory Buenos Aires/CABA territorial scoping,
  ambiguity resolution, and explicit degradation to partido when no localidad is known; personal
  coordinates are never persisted or logged.
- **T2:** a versioned territorial catalog with provenance and verification date; distinguish
  `covered`, `out_of_coverage` and `coverage_unverified`, where absence means unverified, never
  out of coverage.
- **T3:** record D1–D11 and T1–T3 in this register and resolve Q01/Q02/Q04/Q07 only as far as the
  approved decisions support, keeping genuinely undefined aspects explicitly pending.

These decisions authorize the CU01 OpenSpec proposal and its documentation corrections only. They
do not authorize implementation, migrations, dependency installation, Sync, Archive, commit or push.
The ENRE feed contract was verified read-only on 2026-11-10 (live payload, UTF-8, `Last-Modified`
refresh, legacy TLS requirement); the GeoRef forward/reverse shapes were probed read-only the same
day. Unverified items stay listed as pre-BUILD blockers in the change's `tasks.md`.

## U17 - CU01 BUILD 1 authorization

Recorded from the user's 2026-11-10 instruction beginning "BUILD 1 — CU01: Integración ENRE y
backend". The user authorizes the first functional stage of `implement-current-outages-cu01`:
ENRE acquisition, JSON5 parsing, PostgreSQL snapshot persistence, the five-minute advisory-locked
refresh and the public partido/localidad query API. Explicitly excluded from this stage: GeoRef,
browser geolocation, the definitive territorial coverage catalog and the full visual interface.
The user requires stopping if JSON5 cannot interpret a real fixture, forbids Sync, Archive, commit
and push, and forbids declaring CU01 complete at the end of this stage.

This authorization covers BUILD 1 only. It does not authorize BUILD 2/3, does not resolve the
coverage-catalog or GeoRef↔ENRE mapping blockers, and does not authorize implementation of CU02,
CU03, CU09 or CU10.

## U18 - CU01 BUILD 2 authorization

Recorded from the user's 2026-11-10 instruction beginning "BUILD 2 — CU01: GeoRef y cobertura
territorial". The user authorizes the territorial backend stage of
`implement-current-outages-cu01`: a centralized GeoRef adapter (forward addresses and reverse
coordinates, Buenos Aires/CABA scope, verified GeoRef↔ENRE naming rules, ambiguity, degradation
to partido, granularity reporting), the versioned Edesur coverage catalog with `covered`,
`out_of_coverage` and `coverage_unverified`, and integration with the BUILD 1 snapshot/API.

The user explicitly excludes the React interface and the browser GPS flow, forbids replacing the
ENRE integration or the GeoRef provider without approval, forbids Sync, Archive, commit and push,
and forbids declaring CU01 complete. Coverage must not be asserted from absence, and insufficient
evidence must remain `coverage_unverified`.

This authorization covers BUILD 2 only. It does not authorize BUILD 3, does not supply the
definitive Edesur concession enumeration and does not authorize CU02/CU03/CU09/CU10 changes.

## U19 - CU01 BUILD 3 authorization

Recorded from the user's 2026-11-10 instruction beginning "BUILD 3 — CU01: Frontend público y
verificación E2E". The user authorizes the public CU01 interface and end-to-end verification:
partido/localidad selection from `/outages/areas`, GeoRef address search, consented browser
geolocation, candidate selection, partido degradation messaging, all normative availability and
coverage states, official source/update/totals presentation, and the narrow public-POST exception
in the shared HTTP client.

The user requires that CU01 never be presented as complete while blocking functional defects
exist, forbids direct browser access to ENRE/GeoRef, forbids altering CU04–CU09 behavior, forbids
Sync, Archive, commit and push, and requires an independent review plus separate reporting of
pre-existing CU05/OCR problems.

This authorization covers BUILD 3 only. It does not resolve the coverage-catalog enumeration
(task 0.4) or the unobserved media/preventivo shapes (task 0.1), and does not authorize CU01
closure, Sync or Archive.

## U20 - CU01 final verification and closure preparation

Recorded from the user's 2026-11-10 instruction beginning "VERIFY & CLOSE — CU01: Current
Outages". The user accepts the two remaining limitations as documented exceptions and authorizes
preparing the formal closure of `implement-current-outages-cu01`:

- **0.1 (ENRE unobserved categories):** stop waiting for populated `cortesServicioMedia` /
  `cortesPreventivos` captures. Accept the limitation only because the parser handles unknown
  collections and extra keys safely, fails closed on invalid structures, preserves the last valid
  snapshot, and never presents invented data. Synthetic fixtures are not production evidence; no
  claim is made that populated categories were verified live.
- **0.4 (territorial catalog):** approve the current versioned nine-localidad catalog with its
  documented provenance. Unverified zones remain `coverage_unverified`; do not expand coverage or
  assert negative results without evidence.

This authorization covers verification and closure preparation only. It does not authorize Sync,
Archive, commit, push or deployment, does not authorize starting CU02, and does not convert the
0.1/0.4 exceptions into verified production behavior.

## U21 - CU02 reduced scope and PROPOSE authorization

Recorded from the user's 2026-11-10 PROPOSE instruction for CU02, which accepts a reduced,
demonstrable version of the use case and authorizes only documentation and OpenSpec artifacts.

**Verified evidence (2026-11-10):** the ENRE `data_EDS.js` feed returned HTTP 200 with
`Last-Modified` advancing every ~6 minutes and four `cortesProgramados` rows (partido,
localidad, subestacion_alimentador, usuarios, normalizacion), all with
`normalizacion: 'Sin datos'` and no start date, end date, reason or coordinates.
`cortesComunicados` was empty in every live sample and in all inspected archived captures
from 2019 to 2026; one archived capture (2026-01-14) proves that `normalizacion` can carry a
full date-time (estimated restoration only). The Edesur `ed.edesur.com.ar/api/utils/outage-report`
endpoint returned HTTP 500 ("Error al consular el servicio") or timed out, is reported failing by
the official page itself, and has no archived payload; its `fechaInicio`/`fechaFin` contract is
visible only in the page JavaScript. ENRE therefore remains the only operational source and it
does not publish a future agenda.

**Approved reduction (D1):** CU02 SHALL use ENRE `cortesProgramados` as the operational source
of reported scheduled works. `cortesComunicados` is evaluated and counted but its rows are not
displayed because no populated shape has ever been observed. The Edesur `outage-report` API is
not integrated while unavailable.

**D1-D8 approved for the demo:**

- **D1:** ENRE only; `cortesProgramados` displayed, `cortesComunicados` counted but not
  displayed; no Edesur integration.
- **D2:** query by partido with optional localidad through the CU01 GeoRef adapter and coverage
  catalog in read-only mode; no distances or geographic precision asserted.
- **D3:** overlap filtering, horizon and the upcoming/in-progress split are kept as a future
  rule, enabled only with real verified dates. This version exposes no date filters, does not
  classify records temporally and does not infer an end from `normalizacion`.
- **D4:** independent snapshot tables, fetch-run history and advisory lock; reuse of the existing
  ENRE transport/parser patterns without touching CU01.
- **D5:** reason shown only when published; otherwise "No publicado por la fuente".
  `normalizacion` is an estimated restoration time, never a planned end.
- **D6:** provenance preserved per source; no heuristic deduplication or territorial sums.
- **D7:** CU01 coverage catalog reused read-only; no entries added.
- **D8:** independent public "Trabajos" view reusing the shell; CU01 and CU09 unchanged.

**U21 historical limitation (superseded for delivery by U22):** CU02-R1's date
filtering, planned start, planned end and proximity were not implemented in the U21
reduction; the reason was unsatisfied by the source. CU02-S01 was satisfied only for
its area/source part, CU02-S02 by the fail-closed states, and CU02-S03 remained
blocked. Q04 became PARTIAL for CU02 (ENRE approved for the reduced scope; Edesur not
authorized) and Q05 remained TBD for the dated rule. This paragraph is preserved as
history; U22 establishes the definitive scope and treats those items as out of scope,
not pending.

## U22 - CU02 definitive scope redefinition

Recorded from the user's 2026-11-10 FINALIZE instruction. The user approves the
definitive scope: **"CU02 — Consultar trabajos de mantenimiento eléctrico informados
por ENRE."** The delivered functionality is the public consultation of the maintenance
works ENRE reports for Edesur, with partido/localidad filtering, address/GPS
assistance, feeder, affected users, published restoration estimate, provenance,
three-valued coverage and availability states.

The original academic proposal (upcoming works filtered by dates, with planned
start/end, reason and proximity) is preserved in the CU02 fiche and in U21 as
historical context. It is **not the delivered scope**. Future agenda, temporal
filters, planned start/end, unpublished reasons and distances are **out of scope by
design**, not pending tasks; ENRE does not publish them and no value is invented.

This decision supersedes the "reduced/incomplete" framing of U21 for delivery. It does
not add behavior, change CU01 or modify CU05/CU06. No teacher approval of this
redefinition is claimed; academic conformity remains a separate decision. It
authorizes documentation, OpenSpec sync/archive and a CU02-only commit; no push.

## U23 - CU03 integrated assistant decisions and PROPOSE authorization

Recorded from the user's 2026-11-10 PROPOSE instruction for CU03 (`implement-integrated-assistant-cu03`).
The user confirms for **CU03 only**:

- **D1 - Guided RAG:** the assistant grounds procedural guidance on an approved Edesur
  Markdown guide; the guide content is pending delivery and is not invented (superseded by
  the Subsequent delivery paragraph below). Q06 becomes PARTIAL (identity decided; content
  and retrieval/citation granularity pending).
- **D2 - Vector storage:** PostgreSQL 18.6 with pgvector; an additive migration enables
  the extension and the guide/memory tables.
- **D3 - Read tools:** the assistant uses read-only tools over the CU01/CU02 cached
  snapshots; no query-time ENRE/GeoRef call and no write tool.
- **D4 - Memory:** temporary public memory (in-memory, bounded, short-lived) and
  persistent memory only for authenticated users, account-scoped and owner-clearable.
  This supersedes the earlier "persistent assistant memory TBD".
- **D5 - Streaming:** responses stream over SSE (`text/event-stream`).
- **D6 - Sources:** every data-bearing answer cites official sources with organism and link.
- **D7 - Fallback:** provider/tool/rate-limit/empty-index failures return an identifiable
  static fallback and unsupported questions an identifiable refusal (resolves the CU03
  part of Q07; exact Spanish wording remains a review detail).
- **D8 - Limits:** per-client rate limit (429 + `Retry-After`), timeouts, and
  message-length and token/context/output limits.
- **Transport security:** `POST /assistant/chat` is public and CSRF-exempt only for that
  endpoint, with server-side Origin validation and abuse protection; authenticated unsafe
  operations keep their existing Origin and CSRF requirements. The
  `frontend-session-transport` adaptation is documented for review without changing its
  current contract.
- **MCP:** CU03 uses internal read tools and does not expose development MCP servers; an
  external MCP server is deferred to CU10 as a proposal, not implemented or verified here.

These decisions authorize the CU03 OpenSpec proposal and this documentation update for
human review. They do not authorize Apply, code, dependency installation, migration,
Sync, Archive, commit or push. Q00 remains approved; the Edesur guide delivery and the
pgvector image digest/role verification remain open pre-BUILD items.

**Subsequent delivery (2026-11-10):** the user supplied
`backend/knowledge/guia-oficial-edesur.md` (`document_id` `energia-sur-kb-edesur-001`,
version `1.0.0`, `last_verified_at` `2026-11-10`). It resolves the content-pending part of
Q06; revalidation of time-sensitive data and the procedures the guide marks incomplete
remain pending. The guide content is not modified.

## U24 - CU10 source-supervision decisions and propose authorization

Recorded from the user's 2026-11-11 instruction beginning "Continuá con **CU10 —
Supervisar la actualización automática de fuentes**". The user approves for **CU10
only** the seven decisions below and authorizes the `supervise-source-refresh-cu10`
OpenSpec proposal (proposal, design, specs, tasks) for human review; this is not Apply,
code, migration, dependency, Docker-config, commit, push, Sync or Archive authorization.

- **D1 - Promotion:** an existing account is promoted to `admin` only through a
  controlled backend CLI command, with no user/role management UI, no self-assignment
  and no hardcoded credentials.
- **D2 - Authorization:** only `admin` accounts may read source status, trigger a retry
  or change an interval; FastAPI enforces authentication (401) and role (403) from the
  stored account, never from a client-supplied role, and mutations keep the existing
  Origin and CSRF checks.
- **D3 - Persistence:** each source's interval is stored in PostgreSQL, applied by the
  existing scheduler without restarting the backend, and preserved across restarts;
  only a minimal additive migration is introduced.
- **D4 - Allowed intervals:** exactly 5, 10, 15, 30 and 60 minutes, independent per
  source, validated on the server and in the database; the five-minute default
  preserves the current cadence.
- **D5 - Retry concurrency:** a retry while the same source is already updating returns
  HTTP 409, is not queued, does not interrupt the running acquisition and reuses the
  existing PostgreSQL advisory locks, so it also holds across processes/instances; the
  two sources remain independent.
- **D6 - Optimistic configuration:** an interval change carries a configuration version
  and is applied atomically; a stale version returns HTTP 409 and never overwrites the
  newer value.
- **D7 - Status:** each source reports its last attempt, outcome, last successful
  update, last-attempt error when present and configured interval, derived from the
  existing fetch-run and snapshot records; a failed attempt never erases the last
  success.

**Confirmed wording:** roles are stored and compared as lowercase `user`/`admin`; the
60-minute option is kept and its interaction with the CU01/CU02 freshness thresholds is
documented without changing those thresholds or public contracts; the manual retry is
synchronous and reuses the existing acquisition, with no queues or new workers.

**BUILD 2 confirmation (2026-11-13):** the user approved a ~25-second client deadline
exclusively for the manual retry, with the shared client keeping its 10-second default;
a client timeout is treated as an unconfirmed result and followed by a real status GET,
never as a successful or failed acquisition.

**Scope note:** CU10 adds no MCP integration. The academic minimum of two MCP servers
including an external one is already met by the verified development integrations
(GitHub and Context7, both external); U23's deferral of an external MCP to CU10 is
therefore read as satisfied by those integrations, and this reading is flagged for human
confirmation. CU10 does not implement Q22 backoff or per-source enable/disable.

This authorization covers the CU10 proposal only. It does not authorize implementation,
migrations, user promotion, Docker or dependency changes, Sync, Archive, commit or push.

## U25 - CU10 Apply, BUILD 2 and closure authorization

Recorded from the user's CU10 instructions. The 2026-11-11 BUILD 1 instruction authorized
the backend implementation, additive migration, synthetic promotion and focused tests. The
2026-11-13 BUILD 2 instruction authorized the frontend admin view, the 25-second retry-only
client deadline, the no-new-MCP reading, the 60-minute interval and the synchronous retry,
including a synthetic QA account for E2E. The final 2026-11-13 closure instruction
authorizes the final review, OpenSpec Sync and Archive of `supervise-source-refresh-cu10`
and the necessary documentation updates.

It does not authorize commit, push, deployment, changes to CU01/CU02 public contracts or
unrelated CU05/CU06/CU04/CU09 fixes. The pre-existing CU05/CU06 backend failures and the
CU05 history E2E failure remain separate debt.

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
  hosting remains TBD and persistent assistant memory is decided by U23 (mechanism;
  the Edesur guide is delivered v1.0.0, 2026-11-10). CU09 tooling approvals and Oxlint
  under U08 are recorded in the corresponding contract.
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
**PARTIAL - CU01, U16 + D2/T1/T2/U20:** the supported inputs are partido, optional localidad and
address, resolved through a backend GeoRef adapter scoped to Buenos Aires/CABA, with candidate
selection for ambiguous addresses and explicit degradation to partido when no localidad is
resolved; coverage uses the approved versioned nine-localidad catalog. **Pending:** only the
definitive Edesur enumeration (accepted 0.4 limitation; `out_of_coverage` unimplemented) and the
exact Q02 copy. The GeoRef↔ENRE mapping is verified (0.3) and the address/location modes are
implemented.
**Impact:** CU01-S01 has a determinate partido/localidad oracle; the exact fallback copy stays Q02.

### Q02
**PARTIAL - CU01/CU02, U16 + T1:** ambiguous addresses require explicit candidate selection;
denied geolocation performs no query and no repeated permission request, preserving the
no-implicit-fallback constraint. **U22, CU02:** candidate selection and the denied-consent
fallback are implemented in the delivered UI; the fail-closed states (CU02-S04) are delivered.
**Pending:** only any copy refinement outside the delivered flow.

### Q03
**PARTIAL - CU04-CU09. Approved for CU09 by U06:** only the account with the registered
domicile may save, view, correct, close or export its cuts (Q18).
U07/U07-T approve opaque server sessions, controlled provisioning and the contract's
cookie/CSRF/hash details for CU09 and its minimum CU04 slice.
**U11, CU04:** a domicile belongs to one account and a meter to one domicile; ownership is checked via that domicile's account. Only its owner manages either using the existing opaque session; writes require trusted Origin and CSRF. Foreign or nonexistent resources return 404. No roles or Edesur ownership verification are introduced.
**Pending:** other CUs' roles/ownership behavior remains unspecified. CU04's historical isolation checks and review are recorded in [STATE](../STATE.md); CU05 requires its own independent review and isolation evidence.

### Q04
**PARTIAL - CU01, U16 + D1/D5/D8/T2:** the ENRE `data_EDS.js` feed is verified accessible and is
the provisional CU01 primary source; provenance exposes the source URL, a `Last-Modified`-based
source update time, the UTC fetch time, a freshness class and an internal fetch-run history reserved for CU10; coverage
provenance is part of the versioned catalog. **U22, CU02:** ENRE `cortesProgramados` is the
approved source for the definitive CU02 scope; `cortesComunicados` is counted but not displayed,
and Edesur is out of scope. **Pending:** CU03 terms remain open; CU10 (U24) supervises the two existing
ENRE sources and adds none. CU02 has no pending source decision.

### Q05
**CLOSED for CU02 - U22:** the definitive scope excludes the future agenda, temporal
filters, start/end and proximity; those items are out of scope by design, not pending.
The original dated proposal is preserved in the CU02 fiche and U21 as historical
context. **Pending:** none for CU02; any dated capability would require a new proposal.

### Q06
**PARTIAL - CU03, U23; content delivered:** the approved guide is
`backend/knowledge/guia-oficial-edesur.md` (`document_id` `energia-sur-kb-edesur-001`,
version `1.0.0`, `last_verified_at` `2026-11-10`), ingested at article granularity
(`CA-01`, `PA-01`, ...) with `source_name`/`source_urls` metadata. **Pending:** periodic
revalidation of time-sensitive data and the procedures the guide itself marks incomplete;
the staleness threshold and embedding model are Apply-time confirmations.
**Impact:** CU03-S01 has a concrete content oracle; stale or incomplete items must be
disclosed, not filled.

### Q07
**PARTIAL - CU01, U16 + D8/D11:** freshness is fresh ≤15 min, stale ≤60 min and unavailable >60
min or no valid snapshot; a degraded/`N/A` source keeps the last valid snapshot, and stale or
unavailable are explicit states rather than empty results. **U22, CU02:** the unavailable,
stale, no-works and unverified-coverage fallback UX is specified and implemented.
**U23, CU03:** the assistant returns an identifiable static fallback for
provider/tool/rate-limit/empty-index failures and an identifiable refusal for unsupported
questions; exact Spanish wording remains a presentation detail. **Pending:** no
fallback-UX alternative remains open for CU01/CU02/CU03; the no-invention constraint is
unchanged.

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
**PARTIAL - CU10, U24 (resolves the CU10 scope):** an existing account is promoted
through a controlled backend CLI, `admin` is checked server-side from the stored role,
and only `admin` may read status, retry or change intervals; unauthenticated and
non-admin requests are rejected, and the administrative surface is not exposed to the
assistant/chatbot. **Pending:** no action-matrix alternative remains for CU10; broader
role policy for other CUs stays unspecified. **Impact:** CU10-S01/S02/S03 have a
determinate authorization oracle.

### Q22
**PARTIAL - CU10, U24 (resolves the supervised scope):** the two existing ENRE sources
are supervised; intervals are 5/10/15/30/60 minutes; a concurrent retry returns 409
without queueing; the manual retry is synchronous. **Pending/out of scope:** a backoff
policy and per-source enable/disable are not implemented by CU10. **Impact:** CU10-S02
has a determinate interval/retry/concurrency oracle for the two existing sources.

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
