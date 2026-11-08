# Shared frontend session and transport boundary

## Purpose

Keep shared frontend identity and transport consistent with the backend cookie,
Origin and CSRF contract, preventing cross-account state leakage during CU reuse.

## ADDED Requirements

### Requirement: Memory-only shared session lifecycle

Shared session/CSRF and selected-domicile state SHALL exist only in application
memory. Passwords SHALL remain transient form values, not shared state. Logout or
session expiry SHALL clear account-owned UI data and invalidate in-flight requests.
Browser storage SHALL NOT persist credentials, session tokens, CSRF or diary data.

#### Scenario: Logout or expiry clears private context
- **GIVEN** a session with selected domicile, private rows and in-flight requests
- **WHEN** the session is logged out or expires
- **THEN** shared private state and drafts are cleared, requests are invalidated, and delayed responses cannot repopulate the previous account's UI

#### Scenario: Domicile switch cannot restore an old draft
- **GIVEN** an open editor or summary for domicile D
- **WHEN** the user selects another own domicile E
- **THEN** D's editor, summary and pending result updates are discarded and no D draft appears under E

### Requirement: Central cookie and CSRF request policy

The shared transport SHALL use the same-origin API with the approved cookie
session. Login SHALL rely on browser-supplied Origin without a pre-auth CSRF token.
Authenticated unsafe requests SHALL attach the current session-bound CSRF token.
The transport SHALL reject destinations outside the same-origin API boundary before
sending credentials or tokens and SHALL NOT forge Origin or introduce bearer auth.

#### Scenario: Login and authenticated writes use distinct token policies
- **GIVEN** the approved U09 backend boundary
- **WHEN** the frontend logs in and then creates, corrects, closes or logs out
- **THEN** login sends no pre-auth CSRF token and each authenticated write sends the current session token with cookie credentials

#### Scenario: Untrusted destinations cannot receive private headers
- **GIVEN** an authenticated shared client
- **WHEN** an absolute, protocol-relative or traversing path resolves outside the permitted same-origin API
- **THEN** the request is rejected locally before network dispatch and neither cookies nor CSRF are forwarded there

### Requirement: Preserve safe transport outcomes and cancellation

The shared transport SHALL retain status-aware 401/403/404/409/422/503 feedback,
validate untrusted successful payloads and reject stale/mismatched ownership data.
It SHALL support timeouts, request cancellation and non-empty authenticated PDF
blobs. It SHALL NOT log credentials, retry unsafe requests automatically, or turn
an unconfirmed logout into a claimed server-side revocation.

#### Scenario: Errors preserve their actionable meaning
- **GIVEN** a private API request
- **WHEN** the backend returns 401, 403, 404, 409, 422 or 503
- **THEN** the frontend exposes the corresponding safe session/authorization/unavailable/conflict/validation feedback without logging the raw request or automatically replaying a mutation

#### Scenario: A stale unauthorized response cannot clear a newer session
- **GIVEN** an old account request remains pending while a new session is established
- **WHEN** the old request returns 401 or a late success
- **THEN** it neither clears the new session nor installs old-account data

#### Scenario: PDF cancellation and failed content are explicit
- **GIVEN** a period PDF request
- **WHEN** it is canceled or returns an error/empty/non-PDF response
- **THEN** no successful download is claimed and the typed cancellation or safe failure is surfaced without exposing internal request details
