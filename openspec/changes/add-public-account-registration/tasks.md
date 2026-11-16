# Tasks

## 1. Backend account registration

- [x] 1.1 Add the typed registration input and sanitized 422/409 contracts; verify valid/invalid schema cases and extra role rejection in backend tests.
- [x] 1.2 Implement `POST /register` with allowed-Origin enforcement, scrypt hashing, explicit `user` role, no session issuance, no-store response, and unique-conflict handling; verify 201/403/409 behavior and credential-free responses.
- [x] 1.3 Add bounded registration rate limiting using the approved in-process policy; verify five attempts are allowed, the next returns 429 with `Retry-After`, and document the multi-instance/proxy limitation.
- [x] 1.4 Verify concurrent duplicate registration, stored hash only, login/session/logout, existing CLI-provisioned account compatibility, account isolation, and unchanged authenticated CSRF behavior using isolated synthetic PostgreSQL tests.

## 2. Frontend registration

- [x] 2.1 Add a typed registration API method and narrow `/register` CSRF exemption; verify request headers and response validation with frontend transport tests.
- [x] 2.2 Add accessible responsive `RegisterForm`, login/register switching, confirmation-password validation, duplicate/rate-limit/error feedback, and username retention; verify React Hook Form/Zod tests and clear transient passwords.
- [x] 2.3 Verify browser-storage non-persistence and the real browser flow registration → login → Mi cuenta → logout with Playwright and synthetic data.

## 3. Documentation and integrated verification

- [x] 3.1 Update README, authentication decisions, `docs/STATE.md`, and the change engineering record; verify the outdated no-public-registration claim is removed while CLI provisioning/promotion instructions remain.
- [x] 3.2 Run focused backend tests, Ruff, mypy, frontend tests, TypeScript, Oxlint, build, and strict OpenSpec validation; record each actual result and any isolated-PostgreSQL/browser prerequisites.
- [x] 3.3 Obtain independent security/scope review and QA acceptance review; resolve findings and rerun affected checks, leaving archive/commit/push/deploy untouched.

## 4. Broad regression and integrated acceptance follow-up

- [x] 4.1 Generate a fresh isolated diagnostic report, reproduce failures by affected module, correct the CU06/OCR test-environment setup, classify unrelated CU01/CU02 failures without changing their business rules, and run one complete backend confirmation suite.
- [x] 4.2 Complete synthetic real-browser account/domicile creation and isolation, logout/CSRF checks, CU09 PDF download/inspection, and account/domicile/record persistence after backend restart; obtain final QA and reviewer confirmation, while separately disclosing unrelated full-suite failures.
