# Spec Delta

## Purpose

Allow visitors to create ordinary Energía Sur accounts through the application while preserving the existing authentication, session, and account-ownership boundaries.

## ADDED Requirements

### Requirement: Validate public registration input

The system SHALL accept a username of 3-32 ASCII letters, digits, underscores, periods, or hyphens, and a password of 12-128 characters. Registration SHALL reject invalid fields and extra role or privilege fields with 422.

#### Scenario: Valid registration input
- **WHEN** a visitor submits a username and password within the accepted limits
- **THEN** the request is eligible for account creation

#### Scenario: Invalid username, password, or extra role
- **WHEN** a visitor submits a username or password outside the accepted format/length or includes an extra role field
- **THEN** the request returns 422 and creates no account

### Requirement: Create a user account without exposing credentials

The system SHALL create a unique account with role `user`, store only a password hash using the existing password-hashing policy, and return 201 with the account identifier, username, and role only. It SHALL NOT create an authenticated session or return a password or password hash.

#### Scenario: Successful registration
- **GIVEN** a valid unused username and password
- **WHEN** the visitor submits registration
- **THEN** a user account is persisted and the 201 response contains no password, password hash, session, or CSRF token

#### Scenario: Existing provisioned account remains compatible
- **GIVEN** an account created by the existing controlled CLI
- **WHEN** its owner submits valid credentials to login
- **THEN** the existing login/session flow remains successful

### Requirement: Enforce uniqueness under concurrent registration

The system SHALL return 409 for an existing username and SHALL rely on database uniqueness to ensure concurrent requests cannot create duplicate accounts.

#### Scenario: Duplicate username
- **GIVEN** an account already exists for the submitted username
- **WHEN** another visitor submits that username
- **THEN** registration returns a sanitized 409 and creates no additional account

#### Scenario: Concurrent duplicate username
- **GIVEN** two valid registration requests for the same previously unused username
- **WHEN** both requests attempt account creation concurrently
- **THEN** exactly one succeeds and the other returns a sanitized 409

### Requirement: Require trusted Origin for public registration

The system SHALL require an explicitly allowed Origin for registration and SHALL NOT require a pre-authentication CSRF token. An absent, `null`, malformed, or untrusted Origin SHALL return 403 without creating an account.

#### Scenario: Registration with trusted Origin and no CSRF token
- **GIVEN** valid registration input and an allowed Origin
- **WHEN** the visitor submits the request without a CSRF token
- **THEN** registration may succeed without setting an authenticated session cookie

#### Scenario: Registration without an allowed Origin
- **GIVEN** otherwise valid registration input
- **WHEN** the request has an absent, `null`, malformed, or untrusted Origin
- **THEN** the server returns 403 and creates no account

### Requirement: Limit repeated registration attempts

The system SHALL allow at most five registration attempts per client address within a rolling 15-minute window and SHALL return 429 with `Retry-After` when that limit is exceeded.

#### Scenario: Excessive registration attempts
- **GIVEN** five registration attempts from one client address within 15 minutes
- **WHEN** that client submits another valid registration request in the window
- **THEN** the server returns 429 with `Retry-After` and does not create an account

### Requirement: Preserve controlled provisioning and role boundaries

The existing CLI provisioning path SHALL remain available. Public registration SHALL assign only role `user`; administrator promotion SHALL remain restricted to the controlled backend CLI.

#### Scenario: Public registration cannot create an administrator
- **GIVEN** a visitor submits registration input
- **WHEN** the visitor attempts to supply an administrator role
- **THEN** the extra field is rejected and no administrator account is created

#### Scenario: CLI provisioning remains available
- **GIVEN** an operator uses the existing controlled provisioning command
- **WHEN** the command provisions an account
- **THEN** it continues to create an account independently of public registration
