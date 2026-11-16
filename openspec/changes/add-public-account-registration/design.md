# Design

## Context

See [proposal.md](proposal.md) for motivation and scope. The current authentication adapter already validates login Origin, verifies scrypt hashes, persists opaque sessions, and enforces CSRF plus Origin for authenticated mutations. `es_accounts.username` is unique, `role` is constrained to `user`/`admin` and defaults to `user`, and the existing CLI provisions accounts using the same hash function. The frontend uses one in-memory session store and a centralized same-origin Axios client.

## Goals / Non-Goals

**Goals:**
- Use the existing account row, password-hash format, request/response conventions, no-store behavior, frontend form primitives, and HTTP transport.
- Keep registration independent from login/session creation and keep administrator promotion controlled by the CLI.
- Make abuse protection bounded and testable without introducing shared storage or dependencies.

**Non-Goals:**
- Account verification, recovery, email, CAPTCHA, public role selection, automatic login, session changes, and full CU04-CU09 changes.
- A new migration, rate-limit persistence, distributed coordination, or changes to public CU01-CU03 access.

## Decisions

### Registration contract and account creation

Add `POST /register` to the existing authentication router, exposed through the existing `/api` frontend proxy. A dedicated Pydantic input bounds usernames to 3-32 ASCII characters matching letters, digits, underscore, period, or hyphen, and passwords to 12-128 characters. Usernames retain their submitted case and PostgreSQL's existing exact unique constraint remains authoritative. The response is `201` with only account `id`, `username`, and literal role `user`; it never returns or echoes the password/hash.

Perform a friendly existing-name lookup, then insert a new Account with `role="user"` explicitly. Catch only the PostgreSQL unique-constraint conflict for the username so concurrent registration receives the same sanitized 409 as the pre-check; roll back before returning. Other persistence failures use the existing sanitized service-unavailable handling. Reuse `hash_password()` and preserve the existing CLI path unchanged.

**Alternative considered:** relying only on the lookup would race under concurrent requests. The database unique constraint must remain the final arbiter; no application lock or new migration is needed.

### Origin and CSRF boundary

Require the exact configured allowed Origin before attempting registration. Do not require a pre-authentication CSRF token, matching the approved U09 login boundary. Registration creates no session and sets no cookie. Login, session, logout, and all authenticated unsafe requests retain their existing behavior, including Origin and session-bound CSRF on authenticated writes.

### Abuse protection

Reuse the existing bounded, lock-protected in-process rate-limiter mechanism, with an independent registration policy of five attempts per client IP in a 15-minute rolling window and `429` plus `Retry-After` when exceeded. Derive the client key from the ASGI connection address only; do not trust caller-supplied forwarding headers. Bound and prune limiter state as the existing mechanism does.

This is intentionally local-process protection. Limits do not aggregate across workers/instances, and reverse proxies that do not provide a trusted client address can cause clients to share one key. A distributed limiter or proxy-address policy requires a later approved infrastructure decision.

### Frontend interaction

Add `RegisterForm` with username, password, and confirmation fields using the established React Hook Form/Zod and local UI primitives. It validates confirmation before transport. Login/register mode switches are buttons within the existing account view. The registration API method uses the same-origin HTTP client, whose request interceptor must explicitly exempt `/register` from authenticated CSRF while retaining cookie credentials and browser-generated Origin. No explicit Origin header is forged.

On success, clear both password values, show a confirmation, switch back to login, and retain the entered username. On server errors, provide clear duplicate, rate-limit, and generic safe feedback. Credentials remain transient form values and are never placed in Zustand, browser storage, logs, or URLs.

## Risks / Trade-offs

- [Concurrent duplicates] → rely on the PostgreSQL unique constraint and translate only its username conflict to 409.
- [Registration abuse across several instances] → explicitly document the per-process limitation; do not imply distributed protection.
- [Credential leakage through transport errors] → preserve the client's sanitized error wrapper and never retain raw Axios errors or form passwords after submission.
- [Existing-account compatibility] → do not alter uniqueness semantics, hash format, CLI provisioning, account schema, sessions, roles, or ownership queries.

## Migration Plan

No schema migration is required. Deploy the backend route and frontend client together; existing provisioned accounts continue to use login and CLI provisioning. Registration failures do not create a session or partially persist an account. A rollback can remove the public UI/route without modifying persisted accounts; already-created user accounts remain valid and are not deleted.
