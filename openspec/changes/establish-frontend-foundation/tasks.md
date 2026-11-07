# Tasks

Technology direction is approved by U09. The subsequent explicit request
"Aplicá establish-frontend-foundation" authorizes Apply after artifact presentation.
Implementation task boxes require actual completion and evidence.
See [design](design.md) for exact proposed additions and preserved toolchain pins.

## 1. Review and locked setup

- [x] 1.1 Obtain review of these artifacts and a subsequent Apply request; record authorization without treating proposal existence as implemented behavior.
- [x] 1.2 Inspect installed tool/CLI help and optional peers, pin approved Tailwind/shadcn helpers/Zustand/RHF/resolver/Zod/Axios, regenerate npm lock and verify strict npm ci without force/legacy peers or changes to React/TS/Vite/Node/npm pins.
- [x] 1.3 Add Tailwind Vite/CSS setup and any required alias/components configuration; update Docker allowlist/copies and README setup, verifying locked verification-image build and existing health proxy configuration.

## 2. Shared shell and local components

- [x] 2.1 Add only needed reviewed local shadcn/ui primitives and cn utility with source/license notes; verify strict types, visible focus, label/error associations and component imports without unchecked casts or dependency creep.
- [x] 2.2 Extract one AppLayout around existing login/CU09/HealthPanel and one deferred ChatMount; verify exactly one mount through auth/domicile transitions, explicit unavailable status and no chat requests or fake answers, documenting the CU03 seam.
- [x] 2.3 Adapt CU09 presentation to shared primitives/Tailwind without changing actions or accessible names; verify loading/error states, table overflow and narrow/desktop layout checks without an extra browser suite.

## 3. Shared memory state

- [x] 3.1 Add typed memory-only session/selection store factories and React selectors; add Node tests for reset/logout/401/account/domicile switches and absence of private browser persistence, documenting state ownership.
- [x] 3.2 Integrate store generations with existing request scopes and keyed editor revision resets; test that late old-session success/401 cannot rehydrate old data or clear a new login and that same-version discard resets the draft.

## 4. Centralized Axios transport

- [x] 4.1 Implement a testable restricted Axios instance with same-origin API destination validation and request/response interceptors; adapter tests must prove current-token writes, token-free login/GET, cookie credentials, no forged Origin and rejection of external/traversing destinations before dispatch.
- [x] 4.2 Preserve typed status/error/timeout/cancellation and DTO/ownership validation in the CU09 adapter; add Node tests for 401/403/404/409/422/503, malformed success, stale generations, no unsafe replay and no raw credential logging.
- [x] 4.3 Preserve authenticated PDF blobs and bounded safe JSON-blob error handling; add tests for PDF MIME/empty/error/cancel cases and document how other CUs reuse the transport instead of creating parallel clients.

## 5. CU09 form adoption and reuse

- [x] 5.1 Move login and new-domicile forms to React Hook Form/Zod with accessible errors and pending protection; schema/transport tests verify approved bounds/payloads, transient password clearing and no stored credentials.
- [x] 5.2 Migrate create/correct/close/period forms with typed null mapping, backend-error feedback and preserved reset identity; test optional fields, limits, invalid drafts, domicile/account changes and 409 discard without duplicating backend date/union calculations.
- [x] 5.3 Deliver docs/frontend-foundation.md with reusable layout/component/store/form/adapter patterns, CU09 examples, backend authority and the single CU03 mount; link from README and verify all documented paths/commands exist.

## 6. Integrated gates and review

- [x] 6.1 Run all affected Node/schema/store/transport tests, Oxlint, strict TS/build, locked builds/drift rejection and backend security regressions; record actual PASS/FAIL/BLOCKED/NOT APPLICABLE evidence without claiming browser success from mocks.
- [x] 6.2 Run exactly one quick Chromium CU09 workflow with two synthetic accounts and actual downloaded PDF validation, preserving CU09-S01–S15/AD-S01–S02 oracles; record scope/limits and report any failure before additional browser reruns.
- [x] 6.3 Obtain separate read-only review of session/reset/interceptor/security/ownership regressions and disposition findings; verify no mandatory gate remains failed/blocked before implementation closure.
- [x] 6.4 Validate OpenSpec strictly, reconcile tasks/STATE/README/engineering evidence and links, and leave the change ready for human review without Archive/commit/push.

## Workflow follow-up

- All 18 implementation tasks are evidenced in the engineering record; ready for human review, not archived. Latest actual check results and limitations are recorded there, not inferred from checkboxes.
- CU09's U09 security clarification is a separate verified update, not proof this foundation has been implemented.
- LangChain, message handling, streaming and chatbot memory are deferred to CU03.
- Archive, commit, push, deployments and destructive cleanup require separate authorization.
