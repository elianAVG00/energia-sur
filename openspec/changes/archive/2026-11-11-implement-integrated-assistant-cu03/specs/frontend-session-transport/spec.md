# Spec Delta

## MODIFIED Requirements

### Requirement: Central cookie and CSRF request policy

The shared transport SHALL use the same-origin API with the approved cookie session.
Login SHALL rely on browser-supplied Origin without a pre-auth CSRF token. Authenticated
unsafe requests SHALL attach the current session-bound CSRF token. The public
`POST /assistant/chat` is an Origin-validated public endpoint: it is exempt from the
session CSRF token even when a session cookie is present and uses the dedicated
streaming client, not the shared mutation transport. The transport SHALL reject
destinations outside the same-origin API boundary before sending credentials or tokens
and SHALL NOT forge Origin or introduce bearer auth.

#### Scenario: Login and authenticated writes use distinct token policies

- **GIVEN** the approved U09 backend boundary
- **WHEN** the frontend logs in and then creates, corrects, closes or logs out
- **THEN** login sends no pre-auth CSRF token and each authenticated write sends the current session token with cookie credentials

#### Scenario: Public assistant chat uses Origin without CSRF

- **GIVEN** an authenticated browser
- **WHEN** it sends a chat request to the public assistant endpoint
- **THEN** the request is accepted with Origin validation and no session CSRF token, and authenticated unsafe operations still require the token

#### Scenario: Untrusted destinations cannot receive private headers

- **GIVEN** an authenticated shared client
- **WHEN** an absolute, protocol-relative or traversing path resolves outside the permitted same-origin API
- **THEN** the request is rejected locally before network dispatch and neither cookies nor CSRF are forwarded there
