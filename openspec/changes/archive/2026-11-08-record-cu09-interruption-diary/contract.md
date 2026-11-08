# CU09 accepted Apply transport and security contract

Authority: U07 approves the proposal/recommended D0-D5 options. In the subsequent
question the user chose **“Aprobar paquete técnico (Recommended)”**, explicitly
authorizing the missing concurrency, limits, scrypt/session/CSRF parameters,
compatible stable dependency pinning, Unicode PDF, Playwright/pypdf and lint/type
tool choices. Recorded 2026-11-07; no commit/push/Sync/Archive approval.
A later same-day decision approved a 1970-01-01 Buenos Aires minimum date and
Oxlint 1.92.0 for frontend lint, replacing the incompatible typescript-eslint pin.
U09 explicitly approves the security clarification: login requires a trusted
allowed Origin; authenticated unsafe operations require both Origin and a valid
session-bound CSRF token. No anonymous/pre-authentication CSRF token is required.

## Approved detail package

- Optimistic record versioning; stale edits/closure return 409, without overwriting.
- Domicile display_address: trim, 1-300 characters. Optional observations at most
  4000, complaint_number at most 120. No legal-address verification/deduplication.
- Python scrypt, random salts; opaque server sessions last 8 hours, stored token
  hashes, HttpOnly cookie, SameSite=Lax, Secure under HTTPS. Login requires an
  explicit allowed Origin, rejecting absent, `null`, malformed or foreign origins.
  Authenticated unsafe requests require both an allowed Origin and a valid
  synchronized session-bound CSRF token. Login does not require a CSRF token.
- Controlled local account provisioning, no public registration/reset/switch endpoint.
- ReportLab on-demand PDF with packaged Unicode font and repeated table header.
- Playwright browser QA, pypdf extraction, Ruff/mypy and Oxlint 1.92.0 for frontend
  lint with TypeScript 7.0.2 preserved; never ignore peer restrictions.
- Cut and report-period times before 1970-01-01 00:00 Buenos Aires are rejected
  with a sanitized 422. From that floor onward named-zone offsets are whole minutes,
  so exact transport and integer-minute totals need no historical rounding rule.

Implementation parameters within the approved security package: scrypt N=131072,
r=8, p=1, 16-byte salt, 64-byte result, bounded 256 MiB max memory; session/CSRF
tokens use 32 random bytes. Session cookie name `energia_sur_session`, path `/`.
Allowed development origins are loopback 5173, configurable as explicit origins
for approved alternate local ports; no wildcard, CORS bypass or frontend secret.
No passwords/tokens/database URL are logged or placed in shared configuration.

## Shared JSON representation

Requests reject extra fields. IDs are server-generated strings. All responses are
typed and contain no credential, session-token hash or other account's data.
Datetime inputs are minute-local ISO `YYYY-MM-DDTHH:MM` interpreted by the backend
as Buenos Aires, or aware ISO instants with zero seconds/fractions. Responses use
Buenos Aires offset-aware ISO timestamps at minute resolution. Supplied cut and
period times must be at or after 1970-01-01 00:00 Buenos Aires; earlier values
return 422. Only cut timestamps are forbidden in the future; a future report end
is allowed.

- Account: `{id, username}`.
- Session: `{account: Account, csrf_token: string}`. CSRF retrieved through the
  authenticated same-origin session request, kept in memory only.
- Domicile: `{id, display_address}`; account identity comes solely from the session.
- Cut: `{id, domicile_id, start_at, end_at: string|null, observations: string|null,
  complaint_number: string|null, version: number, status: "ongoing"|"closed"}`.
- Summary: `{domicile: Domicile, period_start, period_end, generated_at, timezone,
  total_minutes, total_hours, remaining_minutes, entries: Cut[]}`. Totals are
  authoritative backend results; entries contain only positive intersections.

## Routes (frontend uses same-origin /api prefix)

| Method/path | Input | Response |
| --- | --- | --- |
| POST /login | `{username,password}`, explicit trusted allowed Origin; no pre-auth CSRF token | Session, 200, rotated cookie; untrusted/missing Origin: 403 |
| GET /session | Session cookie | Session, 200; otherwise 401 |
| POST /logout | Cookie + allowed Origin + valid X-CSRF-Token | 204, revoke session and clear cookie |
| GET /domiciles | Cookie | Domicile[] |
| POST /domiciles | `{display_address}`, Origin + X-CSRF-Token | Domicile, 201 |
| GET /domiciles/{id}/interruptions | Cookie | Cut[] ordered by start descending |
| POST /domiciles/{id}/interruptions | `{start_at,end_at,observations,complaint_number}`, Origin + CSRF | Cut, 201 |
| PATCH /interruptions/{id} | Full cut input plus `{version}`, Origin + CSRF | Cut, 200; no reopening/reassignment |
| POST /interruptions/{id}/close | `{end_at,version}`, Origin + CSRF | Cut, 200 |
| GET /domiciles/{id}/summary | `period_start`, `period_end` query, cookie | Summary, 200 |
| GET /domiciles/{id}/report.pdf | Same period queries and cookie | Authenticated PDF download, 200 |

Unauthenticated: 401; foreign/missing object: identical 404; invalid dates/body/range:
422; missing/untrusted Origin on login or any unsafe operation: 403; absent/wrong
CSRF on authenticated unsafe operations: 403; stale version: 409; unavailable
database/PDF service: safe 503 without internals. Errors use `{detail: string}`,
including sanitized validation errors; don't echo sensitive inputs. Private responses
are non-cacheable. `/health` preserves exact storage-free 200 `{"status":"ok"}`.

Create/correct/close applies the same minute/future/order validation. Correction
of a closed record cannot remove its existing end; explicit close rejects already
closed records. A single captured/floored server clock governs each report; no
client generation clock is accepted. Reads/filtering/PDF scope are always derived
from the authenticated account and owned domicile, never caller account IDs.

## Verified initial pins and compatibility caveat

Registry metadata verified before installation: SQLAlchemy 2.1.8 (Python >=3.11),
psycopg 3.3.8 (binary extra), Alembic 1.20.1, ReportLab 5.1.0, Ruff 0.17.4,
mypy 2.4.1, pypdf 7.0.0, Playwright 1.65.0, Oxlint 1.92.0.
Python runtime remains 3.13.18; React/TS/Vite/npm pins are preserved.
Latest stable typescript-eslint 8.72.1 still declares TypeScript >=4.8.4 <6.1.0,
incompatible with existing TypeScript 7.0.2. Do not install it using force/legacy
peers or downgrade TypeScript silently. The approved alternative is pinned Oxlint
1.92.0, which parses TypeScript independently of the `typescript` package.
