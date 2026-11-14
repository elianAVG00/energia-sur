# Design

## Context

See `proposal.md` — Why. The shared shell, approved tokens and CU01 result card are
already implemented and archived (`redesign-public-shell-cu01`, U27/U28). CU02 keeps
its original single-card form and plain result list; CU10 keeps its plain source cards.
Both use the same local primitives, `state.ts` helpers and request scopes as the rest of
the frontend. No backend, HTTP client, store or authentication change is needed.

Constraints: React 19 + Vite + TypeScript, Tailwind CSS 4 with semantic tokens, local
shadcn/ui primitives, Playwright and Docker verification images already installed.
CU02's accepted definitive scope (U22) excludes date filters, planned start/end and
source reasons; the API returns null for those fields. M2, M3, the assistant overlay and
stale/unavailable totals are pre-existing findings outside this change.

## Goals / Non-Goals

**Goals:**

- Reuse the CU01 visual language: card hierarchy, state chips, soft panels, treated
  table, provenance block and mobile-first control stacking.
- Present CU02's real states and limitations without inventing dates, reasons or
  absence of works.
- Present CU10's real per-source state, errors and existing controls with a clearer
  hierarchy.
- Keep the diff presentation-only and auditable; no new dependency, token or shared
  component that couples CU01 with CU02/CU10.

**Non-Goals:**

- Date filters, planned dates, reasons, distances or agenda behavior.
- Backend, API, validation, authentication/CSRF, Zustand, HTTP client or scheduler
  changes.
- Fixing M2, M3, the floating-assistant overlay or totals presentation.
- Redesigning CU01, CU03, CU04-CU09, the landing page, header, footer or layout.
- New administrative tools, polling, role management or per-source enablement.

## Decisions

### D1 — Reuse tokens and local primitives; no new shared component

CU02 and CU10 consume the existing tokens and `Card`, `Button`, `Input`, `Label`,
`Alert` and `Table` primitives. Selects keep the existing local `SELECT_CLASS` pattern
used by CU01 (`min-h-10 w-full rounded-md border border-input bg-card px-3 ...`) instead
of adding `components/ui/select.tsx`. This avoids a premature shared abstraction and
keeps native select behavior unchanged.

Tone chips are local to each feature: a small `chip(tone)` helper with `attention`
(accent), `neutral` (muted) and `critical` (destructive) variants. CU01 is not
refactored; the small duplication is intentional because coverage/freshness and
source/outcome tones are feature semantics.

Alternative rejected: a shared `StatusChip`/`Select` used by CU01, CU02 and CU10. It
would touch the closed CU01 implementation and create coupling for no behavioral gain.

### D2 — CU02 card hierarchy

`ScheduledWorksPanel` becomes three presentation blocks while keeping all state,
handlers and request lanes:

1. "Consultar trabajos": zone filter, partido/localidad grid, primary "Consultar
   trabajos", secondary "Usar mi ubicación", area-loading/error and zone feedback.
2. "Buscar por dirección": address field, "Buscar dirección", the unchanged privacy
   note, address feedback and candidate zones.
3. Initial panel when there is no result, loading, error or candidate list.

Presentation-only `errorScope` and `messageScope` flags route the existing `error` and
`searchMessage` strings to the card that produced them, exactly as CU01 does. No message
string, handler, request or state transition changes.

### D3 — CU02 result card

New `ScheduledWorksResultCard.tsx` receives the validated `ScheduledWorksResult` and
holds no state or requests. It renders:

- state heading and granularity/coverage/freshness chips;
- the existing normative description and alerts (degraded source, stale/unavailable,
  dates/reason/announced limitations, proximity note);
- a "Zona y alcance de los datos" panel with the queried coverage zone, planned start
  and planned end as "No publicado", and a short note that the reason is shown per work;
- the existing five-column works table with `scope="col"`, a minimum width, the shared
  focusable scroll region and a small-screen scroll hint;
- the existing provenance fields and source link.

The card reads `planned_start_at`/`planned_end_at` only to display a value if a future
source ever publishes one; under the accepted contract both are null, so the fields
render as "No publicado" and no value is invented. The wording is distinct from the
existing limitation sentence and from the table's "No publicado por la fuente" reason
cell, so strict existing locators are not duplicated. Date fields are omitted when the
result has no works.

### D4 - CU10 card hierarchy (implemented under U30)

`AdminPanel` keeps all state, handlers and request scopes; its internal `SourceCard` is
extracted to a presentational `SourceCard.tsx`. Each card shows title, scheduling and
last-attempt chips, a status grid (last attempt, outcome, last success, current
interval), an error panel, a lock-contention note, a "Configuración" section with the
interval selector and save control, and an "Acciones" section with the retry control.
Feedback keeps its exact success/warning/error strings and carries a presentation-only
`action` flag so save results render under "Configuración" and retry results under
"Acciones". No new action is added.

### D5 — Tone semantics

No success/green token exists. `attention` (accent) marks a verified dimension or a
real successful outcome; `neutral` marks configuration, unknown or unverified data; and
`critical` marks a real error, degraded source, unavailable freshness or out-of-coverage.
Informational limitations may use an accent-tinted `Alert` via `className` but keep the
same text and existing role; the shared `Alert` primitive is not modified.

### D6 — Accessibility and announcements

Keep one `h1` from the layout, labelled fields, `aria-describedby` for filter/address
help, `aria-labelledby` for candidate zones, visible focus, keyboard operation and the
existing table scroll region. Do not add new `aria-live` regions or duplicate existing
state text. The result card keeps its pre-existing `aria-live="polite"` section; M2 is
documented, not fixed. The shared `Table` label remains unchanged (M3).

### D7 — Verification and evidence

Add a gated `visual-capture-works-admin.spec.ts` (`VISUAL_CAPTURE=1`, `VISUAL_DIR`) with
synthetic API mocks. Capture CU02 initial, reported works, no works, stale/degraded,
unverified coverage and query error; capture CU10 normal and failed-attempt states.
Viewports: 1440×900, 820×1180 and 390×844 where they add responsive evidence. Baseline
`before/` is captured before UI edits; Stage A writes `etapa-a/` and Stage B writes
`etapa-b/`.

Add `redesign-works-admin.spec.ts` for cross-cutting checks: palette tokens, one `h1`,
landmarks, no horizontal overflow at the three widths, one chat mount and no `/api/health`.
Extend `cu02.spec.ts` and `cu10.spec.ts` with new cases without editing existing ones.

### D8 — Spec hygiene

MODIFIED requirement descriptions stay under 500 characters (CU02 477, CU10 460) because
strict validation checks them. Requirement blocks are copied whole and only extended.
Validate strict before touching frontend code and again at closure.

### D9 — Decision and documentation trail

U29 records interpretation A, the Stage 0/A authorization and the no-date-filter rule;
U30 remains reserved for Stage B. The engineering record captures prompts, agents,
commands, evidence, reviewer findings and corrections. `STATE.md` stays at most 60 lines
and corrects the stale "nothing pushed" statement using `git ls-remote` evidence.

## Risks / Trade-offs

- Adding date filters or real dates by literal interpretation → U22 conflict; rejected
  by U29 and covered by a test that asserts zero date inputs.
- Duplicating a phrase used by a strict `getByText` locator → use "No publicado" in the
  scope panel and keep each existing limitation/state phrase exactly once.
- Changing ids, labels, button names or messages → existing `cu02`/`cu10` tests fail;
  diff review and unchanged suites are mandatory.
- Touching `api.ts`/`state.ts` for presentation → contract risk; only existing helpers
  are imported; the diff audit must show no changes there.
- Shared primitive changes rippling to CU05/CU06/CU09 → do not modify `Alert`, `Table`,
  `Input`, `Button` or `Card`; only use their existing props and `className`.
- Sticky header/chat in full-page captures → reset scroll before captures and freeze
  transitions, as in `visual-capture-cu01-states.spec.ts`.
- Stale Vite module graph in Docker → rebuild/recreate the `frontend` service and verify
  the served component before E2E and captures.
- M2/M3/overlay/totals are noticed during review → document as pre-existing and do not
  fix incidentally.
- Playwright strict-mode failures from duplicate text → keep one copy of each existing
  message and run the full focused set.

## Migration Plan

No data/API migration. Stage 0 adds artifacts, the capture spec and baseline evidence.
Stage A changes only CU02 presentation and its tests. Stage B changes only CU10
presentation and its tests. Rollback is a revert of the affected frontend files;
behavior, data and contracts remain untouched. No commit, push or archive is part of
this change.

## Open Questions

None blocking. U30 authorizes Stage B; its independent review is the remaining
pre-closure check.
