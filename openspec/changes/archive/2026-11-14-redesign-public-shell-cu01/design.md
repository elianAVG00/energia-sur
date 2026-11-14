# Design

## Context

See `proposal.md` for motivation. The current shell (`frontend/src/layouts/AppLayout.tsx`)
is a `<main>` with an `<h1>` plus the fixed `ChatMount`; navigation and the account/logout
control live in `frontend/src/App.tsx`. Styles are Tailwind CSS 4 `@theme` tokens in
`frontend/src/styles.css` consumed by locally adapted shadcn/ui primitives in
`frontend/src/components/ui/`.

Constraints: React 19 + Vite + TypeScript, Tailwind 4, local shadcn/ui, Zustand, RHF/Zod,
Axios and Playwright already installed; no new dependency, registry reinstall or font may
be added (U26 D2/D3). U26 D5 splits the work: shell plus CU01 first, remaining screens
later. D6 moves logout to the header; D7 leaves the initial landing unchanged. U26 D1
forbids any technical/health panel. The single `ChatMount` is a fixed `z-10` aside and
must stay unique.

## Goals / Non-Goals

**Goals:**

- One shared, accessible shell (identity header, horizontal navigation, centred main,
  footer, skip link) that every view inherits without changing its functional content.
- Approved light tokens applied through semantic utilities only; a 1200 px container.
- A single header logout that reuses the existing handler; no duplicated control.
- Zero change to HTTP clients, stores, auth transport, validation or business rules.
- Stage B is implemented under U28 with the same presentation-only boundary.

**Non-Goals:**

- CU02, CU04–CU10, chat redesign, landing.
- Router, sidebar, drawer/hamburger, dark mode, external fonts, new UI dependency.
- Backend, API contracts, cookies/CSRF, Zustand behavior, audit or persistence changes.

## Decisions

### D1 — Tokens and type scale

Replace the `@theme` palette in `styles.css` with the approved values:

| Token | Value | Purpose |
| --- | --- | --- |
| `--color-background` | `#F8FAFC` | page background |
| `--color-foreground` | `#0F172A` | body text |
| `--color-card` | `#FFFFFF` | surfaces |
| `--color-card-foreground` | `#0F172A` | text on surfaces |
| `--color-primary` | `#0D6177` | CTAs, active nav, focus ring |
| `--color-primary-foreground` | `#FFFFFF` | text on primary |
| `--color-secondary` | `#E2E8F0` | secondary actions |
| `--color-secondary-foreground` | `#0F172A` | text on secondary |
| `--color-muted` | `#F1F5F9` | soft panels |
| `--color-muted-foreground` | `#475569` | secondary text |
| `--color-accent` | `#E6F2F5` | hover / active surface |
| `--color-accent-foreground` | `#0D6177` | text on accent |
| `--color-border` | `#E2E8F0` | borders |
| `--color-input` | `#64748B` | field borders (≥3:1) |
| `--color-ring` | `#0D6177` | visible focus |
| `--color-destructive` | `#AC2336` | preserved |

Rationale: semantic tokens keep primitives untouched and avoid hard-coded colors in
components. Alternative (per-component Tailwind colors) was rejected because it duplicates
the palette and drifts. `body` keeps `system-ui, sans-serif`; no `dark:` variants.
`:focus-visible` stays 2 px with 3 px offset. Compute and record real contrast ratios
(white on `#0D6177`, `#475569` on `#F8FAFC`, `#0F172A` on `#FFFFFF`) in the engineering
record rather than asserting them.

### D2 — Shell hierarchy

`AppLayout` becomes a flex column of `min-h-screen`:

```
skip link → SiteHeader (banner, sticky) → main#contenido (flex-1, max-w-[75rem])
          → SiteFooter (contentinfo) → ChatMount (unchanged, single)
```

The header is sticky (`border-b`, `bg-card/95`, `backdrop-blur`, `z-30`); the chat stays
`z-10`, so no overlap. `main` keeps `pb-36` to reserve end-of-page content clearance, gains
`id="contenido"`, `tabIndex={-1}` and `scroll-mt-24` for the skip link, and the footer
reserves `pb-28` so the collapsed chat never covers footer text. The container is
`mx-auto w-full max-w-[75rem] px-4 sm:px-6` (75rem = 1200 px). `PageHeader`
(title `h1` + optional description) is part of the layout so every view has exactly one
`h1`; the brand is non-interactive identity text, not a heading and not a link, because
the application has no router.

### D3 — Header, navigation and logout

`SiteHeader` receives `nav`, `showLogout`, `pending` and `onLogout`; `App.tsx` keeps the
view state and the existing `logout` handler, passing the same `<Button>` controls with
unchanged accessible names: `Cortes`, `Trabajos`, `Mi cuenta`, conditional
`Administración`. The active control gets `aria-current="page"` plus a visual active
style. Navigation wraps on narrow viewports; no sidebar, drawer or hamburger.

Logout becomes a single text button in the header with `disabled={pending}`. It is removed
from the account view but `Cuenta: {username}` stays exactly where tests expect it
(`cu05-history.spec.ts`). The header must not repeat that text, because those locators are
strict. Session errors (login and failed logout) render above the current view instead of
only inside the account view, so a failed revocation stays visible from Cortes or
Trabajos. No username/avatar menu; alternatives (dropdown, icon-only) were rejected as
unnecessary surface and new behavior.

### D4 — Footer

`SiteFooter` renders static attribution: "Energía Sur · Portal ciudadano para usuarios de
Edesur en Zona Sur" and "Cortes y trabajos: datos públicos del ENRE." It contains no
health, environment, API or session information and no academic wording. The source note
does not claim that every source is exclusively ENRE.

### D5 — Stage B boundary (CU01)

`OutagesPanel.tsx` keeps all state, handlers, `scope`, request logic and user-facing
messages. Only its JSX is reorganized: a "Consultar cortes" card (same ids `outage-filter`,
`outage-partido`, `outage-localidad`, same labels, actions and status messages), a "Buscar
por dirección" card (same id `outage-address`, privacy note and candidates) and a
presentational `OutagesResultCard` that receives `OutagesResult` and reuses `state.ts`
helpers (chips, stat tiles, provenance, table). No change to `api.ts`, `state.ts`,
geolocation, validation or HTTP. This keeps the diff auditable and lets Stage A ship
independently. Implemented under U28; two presentation-only scope flags render the same
error and status texts next to the flow that produced them, without changing any message,
request or handler logic.

### D6 — Adaptation of `dashboard-01`

Taken: top header, card-based hierarchy, soft surfaces, compact type, stat tiles, treated
table, responsive stack. Discarded: sidebar, breadcrumbs, charts, range filters, avatar
menus, dark mode, sample data and any new dependency. The result is a citizen portal, not
an enterprise dashboard.

### D7 — Verification and visual comparison

`frontend/e2e/visual-capture.spec.ts` runs only when `VISUAL_CAPTURE=1`, writes to
`VISUAL_DIR`, uses synthetic API mocks and captures login, Cortes (initial and mocked
result) and Trabajos at 1440×900, 820×1180 and 390×844. Baseline is captured from the
pre-change tree; after screenshots use the same viewports and data. Comparison is manual
side by side (no pixel-diff dependency), documented in the engineering record.
`redesign-shell.spec.ts` covers landmarks and palette tokens, exactly one active
section, one `h1` per view, identity header, admin-only and anonymous nav states,
navigation at 390 px, one logout with its POST plus failed-logout feedback, skip link
and keyboard nav, no `/api/health`, single chat mount and horizontal overflow.

### D8 — Spec hygiene

Each requirement description stays under 500 characters (layout 494, header 450, visual
400, footer 231) because strict validation checks merged main specs at archive time; the
previous archive surfaced this. MODIFIED keeps the existing requirement block whole.

### D9 — Decision and documentation trail

U27 records the approved Stage A/Stage B split, the visual tokens, the header logout move
and the unchanged landing. `docs/ai-engineering/redesign-public-shell-cu01.md` records
prompts, agents, commands, evidence and corrections; `README.md`,
`docs/frontend-foundation.md` and `docs/STATE.md` are reconciled.

## Risks / Trade-offs

- Token/primitives restyle reaches CU02/CU04–CU10 → limit primitive edits to radius,
  spacing and color; capture Trabajos; run mocked regressions.
- `cu05-history` depends on exact `Cuenta: synthetic` → keep the text in the account view,
  never duplicate it in the header.
- `cu09` uses exact `Cerrar sesión` → exactly one button, same name and handler.
- `cu10` expects conditional `Administración` → preserve the condition and name.
- CU01 E2E depends on headings, ids and messages → Stage A does not touch CU01; Stage B
  must keep them and pass `cu01.spec.ts`.
- Sticky header/skip-link focus obscured → `scroll-mt-24`, `main tabIndex={-1}`.
- Fixed chat covers footer/content → keep `pb-36` on main and `pb-28` on the footer, then
  re-check the mobile/desktop captures.
- Session error feedback becomes invisible after logout moves to the header → render
  session errors above the current view and cover the failed-logout path in Playwright.
- Accidental logic edits → audit diff for `api.ts`, `state.ts`, `lib/http*`, `diary*`,
  `stores/`; expect no changes there.
- Requirement text over 500 chars at archive → measured during design; re-validate strict
  after any wording correction.

## Migration Plan

No data or API migration. Apply tokens and shell first, then move navigation/logout, then
run gates and capture "after". Rollback is a revert of frontend files; behavior and data
remain untouched.

## Open Questions

None blocking. Stage A shipped first; Stage B was authorized by U28 and implemented with the
same presentation-only boundary.
