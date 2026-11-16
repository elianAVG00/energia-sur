# Spec Delta

## MODIFIED Requirements

### Requirement: Explicit login Origin and authenticated mutation CSRF boundary

The backend SHALL require an explicitly allowed trusted Origin for login and public registration. Missing, `null`, malformed or foreign origins SHALL be rejected with 403 without issuing a session cookie or creating an account. Login and registration SHALL NOT require a pre-authentication CSRF token. Every authenticated operation that modifies state SHALL require both an allowed Origin and a valid session-bound CSRF token; missing/invalid tokens SHALL yield 403 without modifying records or revoking the session. These rules reflect U09 and U36.

#### Scenario: Login rejects an untrusted or absent Origin
- **GIVEN** valid synthetic credentials and no authenticated session
- **WHEN** login is submitted with absent, null, malformed or foreign Origin
- **THEN** the backend returns 403, issues no session cookie and leaves the caller unauthenticated

#### Scenario: Trusted login establishes the authenticated CSRF boundary
- **GIVEN** valid synthetic credentials and an explicitly allowed Origin
- **WHEN** login is submitted without a CSRF token
- **THEN** login succeeds and returns the session-bound token for authenticated unsafe requests

#### Scenario: Registration rejects an untrusted or absent Origin
- **GIVEN** valid registration data and no authenticated session
- **WHEN** registration is submitted with absent, null, malformed or foreign Origin
- **THEN** the backend returns 403, creates no account and issues no session cookie

#### Scenario: Trusted registration does not require a pre-authentication token
- **GIVEN** valid registration data and an explicitly allowed Origin
- **WHEN** registration is submitted without a CSRF token
- **THEN** account creation may succeed without issuing an authenticated session

#### Scenario: Every authenticated mutation rejects missing or invalid CSRF
- **GIVEN** an authenticated account and its domicile and ongoing cut
- **WHEN** logout, domicile creation, cut creation, correction or closure is submitted with missing or invalid CSRF
- **THEN** each request returns 403 and leaves the session, domiciles, cuts and versions unchanged
