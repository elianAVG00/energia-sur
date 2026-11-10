# AI Engineering record — CU08 consumption evolution and estimates

- **Change:** [view-cu08-consumption-evolution-and-estimates (archived)](../../openspec/changes/archive/2026-11-09-view-cu08-consumption-evolution-and-estimates/proposal.md)
- **Goal:** Implement CU08 "consultar evolución y estimación de consumo" end to end on top of the approved PROPOSE contract (D01–D11 + R01–R07), read-only and with no new persistence.
- **Specs/contract:** [main spec](../../openspec/specs/consumption-trends/spec.md), [delta spec](../../openspec/changes/archive/2026-11-09-view-cu08-consumption-evolution-and-estimates/specs/consumption-trends/spec.md), [design](../../openspec/changes/archive/2026-11-09-view-cu08-consumption-evolution-and-estimates/design.md), [tasks](../../openspec/changes/archive/2026-11-09-view-cu08-consumption-evolution-and-estimates/tasks.md), decisions [U15 / R01–R07](../../docs/use-cases/decisions.md).

## What was built

- **Backend:** `app/consumption.py` (pure `Decimal` domain: `build_intervals`, `build_estimate`, `canonical`, `below_minimum`, local-date/timezone helpers) and `app/consumption_api.py` (read-only `GET /meters/{id}/consumption-evolution` and `GET /meters/{id}/consumption-estimate`, `Auth`-only, `own_meter` 404, `Query(ge=1, le=90)` horizon, inclusive-overlap `from`/`to`). Router registered in `app/main.py`. No tables, migrations or dependencies.
- **Frontend:** `features/consumption/api.ts` (strict response guards), `format.ts` (BigInt half-up `roundTwoDecimals` + `< 0.01` `displayKwh`), and `ConsumptionPanel.tsx` (two views — consumo real kWh / promedio diario kWh/día — a dependency-free CSS bar chart, the 1–90 day estimate selector, date filter, "orientativa, no facturada", "poco representativo" and "< 0.01" indicators), mounted in `DomicileManagement.tsx`.
- **Charting (D11):** Recharts was evaluated, not installed. Recharts 2.x caps the React peer at 18 (conflict with React 19.3.1) and Recharts 3.x / d3 types are unverified against TypeScript 7.0.2; the documented dependency-free SVG/CSS fallback was implemented instead, preserving the pinned lockfiles.

## Decisions and approvals

- D01–D11 confirmed under U15; R01–R07 approved and recorded in the decision register. No new approvals were introduced. Sync/Archive/commit/push were not performed.

## Agents and tools

- Primary agent implemented and verified. Independent `reviewer` subagent performed a read-only audit.
- Verification used the project's Docker images: rebuilt `energia-sur-backend-checks:cu08` (verification target, current `uv sync` deps) and `energia-sur-frontend-checks:cu09`, plus the running `energia-sur-db-1` PostgreSQL with additive synthetic roles/databases.

## Checks and results (this run)

| Check | Result | Evidence |
| --- | --- | --- |
| Backend domain tests (`test_consumption.py`) | PASS 13 | real-UTC elapsed days, deterministic estimate, decreasing-latest no-fallback, zero, below-minimum, large-reading precision |
| Backend adapter tests (`test_consumption_api.py`) | PASS 6 | ownership 404, evolution intervals, inclusive date filter, reversed-range 422, estimate, insufficient/decreasing unavailable |
| Backend PostgreSQL/ASGI (`test_consumption_postgres.py`) | PASS 19 | evolution/estimate, whole-interval filter, decreasing/insufficient/zero, out-of-range 422, cross-account isolation |
| Backend Ruff | PASS | `ruff check app tests` — all checks passed |
| Backend mypy | PASS | `mypy app` — no issues in 32 source files |
| Frontend node tests | PASS 93/93 | `consumption-api` + `consumption-format` plus existing suite |
| Frontend Oxlint | PASS | 0 warnings/errors |
| Frontend TypeScript + build | PASS | `tsc --noEmit` and `vite build` |
| OpenSpec structural validation | PASS | `openspec validate --strict` on the change |
| E2E Chromium (`cu08.spec.ts`) | PASS 4/4 | main flow (two views + estimate 105 kWh + warning), decreasing, zero, cross-account 404 |

## Problems and corrections

- `Decimal` subtraction/multiplication/`format` round to the ambient context precision (28); fixed with per-call `localcontext` precision sized from `as_tuple().digits` in `canonical`, `_subtract`, `_daily_average`, `_multiply`. A 30-digit reading test exposed the subtraction rounding.
- FastAPI `Query(...)` defaults evaluate to `Query` instances on direct calls; switched to `Annotated[..., Query(...)]` so unit tests call the handlers directly.
- Frontend discriminated union lacked a shared discriminant; added `status: "available"` to the estimate success response.
- Playwright locators hit "strict mode violation" because values render in both the bar chart and the table; narrowed to `getByRole('cell', ...)`.
- Independent review found five MINOR issues (estimate-panel `< 0.01` gap, base-timestamp parse asymmetry, bar-width overflow, local-time display nuance, flag serialization coverage); all corrected except the local-time presentation nuance, which is recorded as an accepted cosmetic choice (local dates are Buenos Aires; full local time-of-day is not rendered).

## Residual risks / limitations

- **8-test global-suite diagnosis (environmental, not a CU08 regression):** the full 316-test backend suite in the ad-hoc checks-image run surfaced 8 CU05/CU06 failures. Root causes: (a) the 3 CU06 bill tests (`test_bill_postgres.py`) returned 503 because the run lacked an absolute `CU06_BILL_DIR` and a `CU06_CONFIRMATION_SECRET` of at least 32 bytes (`bill_api.py:93`); (b) the 5 CU05 photo/OCR tests (`test_photo_postgres.py`) needed `--ulimit core=0` and cgroup-v2 `memory.swap.max == 0` for `private_ocr_runtime()`, and the reconciliation tests failed closed (`PhotoRecoveryRequired`) because the reused test database held photo references from earlier runs while each ephemeral tmpfs volume started empty. Re-running the bill module (17/17 PASS) and the photo module (30/30 PASS) against a **fresh migrated database** with `CU06_BILL_DIR`, a ≥32-byte `CU06_CONFIRMATION_SECRET`, `--ulimit core=0`, swap disabled and fresh tmpfs volumes eliminated all 8 failures. `git status` confirms no CU05/CU06 source file was modified (only additive CU08 files plus a two-line router import/include in `main.py` and a two-line mount in `DomicileManagement.tsx`).
- Retained synthetic additive objects (roles/databases `cu08_*`, seeded accounts and QA containers) remain in the local cluster; no cleanup was performed.

## Status

CU08 is implemented, verified, synced and **archived** as `2026-11-09-view-cu08-consumption-evolution-and-estimates`. Sync created the `consumption-trends` main spec (15 requirements) and `openspec validate --specs --strict` / `--changes --strict` pass. Not authorized/performed: commit or push.
