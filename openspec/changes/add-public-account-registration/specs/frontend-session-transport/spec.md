# Spec Delta

## MODIFIED Requirements

### Requirement: Central cookie and CSRF request policy

The shared transport SHALL use the same-origin API with the cookie session. Login and public registration SHALL use browser Origin without a pre-authentication CSRF token; authenticated unsafe requests SHALL attach the session CSRF token. `POST /assistant/chat` is Origin-validated and CSRF-exempt only for that endpoint, through the dedicated streaming client. Destinations outside the same-origin API SHALL be rejected before credentials or tokens are sent; Origin SHALL NOT be forged and bearer auth SHALL NOT be introduced.

#### Scenario: Login and authenticated writes use distinct token policies

- **GIVEN** the approved U09/U36 backend boundary
- **WHEN** the frontend registers, logs in, and then creates, corrects, closes or logs out
- **THEN** registration and login send no pre-auth CSRF token and each authenticated write sends the current session token with cookie credentials

#### Scenario: Public assistant chat uses Origin without CSRF

- **GIVEN** an authenticated browser
- **WHEN** it sends a chat request to the public assistant endpoint
- **THEN** the request is accepted with Origin validation and no session CSRF token, and authenticated unsafe operations still require the token

#### Scenario: Untrusted destinations cannot receive private headers

- **GIVEN** an authenticated shared client
- **WHEN** an absolute, protocol-relative or traversing path resolves outside the permitted same-origin API
- **THEN** the request is rejected locally before network dispatch and neither cookies nor CSRF are forwarded there
