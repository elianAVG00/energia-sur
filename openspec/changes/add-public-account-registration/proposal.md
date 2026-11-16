# Proposal

## Why

Visitors cannot currently create an account even though Energía Sur's authenticated account features are available through the application. Public self-registration makes those features reachable without weakening the existing opaque-session, authorization, or account-isolation boundaries.

## What Changes

- Add public account registration using a username and password, with server validation, scrypt hashing, trusted-Origin enforcement, duplicate handling, and bounded abuse protection.
- Keep account creation available through the existing backend CLI and make public registrations `user` accounts only.
- Add an accessible frontend registration form and a login/register switch. Successful registration returns the visitor to login without creating a session.
- Reconcile the prior controlled-provisioning-only statement: CLI provisioning remains supported, but is no longer the exclusive account-creation path. Existing role promotion remains CLI-only.
- Preserve cookie sessions, CSRF protection for authenticated mutations, public CU01-CU03 access, and CU04-CU09 ownership rules. No database migration or new dependency is expected.

## Capabilities

### New Capabilities
- `account-registration`: Public self-registration and its validation, persistence, Origin, duplicate, and abuse-protection contract. This is a transversal authentication capability, not an additional use case.

### Modified Capabilities
- `interruption-diary`: Extend the existing authentication boundary to require an explicitly allowed Origin for registration, without a pre-authentication CSRF token.
- `frontend-session-transport`: Define registration as a public same-origin unsafe request that sends browser Origin, omits a pre-authentication CSRF token, and does not persist credentials.

## Impact

Affected areas are the existing FastAPI authentication route/schema/security modules and account model, focused backend tests, the React login form/application/API transport, frontend tests, authentication decision documentation, README, operational state, and one engineering record. The existing `es_accounts.username` unique constraint and role default are sufficient. The proposed rate limiter is process-local and therefore does not aggregate requests across backend instances.
