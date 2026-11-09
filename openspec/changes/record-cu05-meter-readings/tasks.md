# Tasks: CU05 meter readings

BUILD is explicitly authorized by the user, including D14/D15, synthetic image tests and the M1 abstention decision. Missing real-photo evidence remains pending; other security and reliability gates are not waived.

Checkpoint (2026-11-08): 14/15 tasks verified, with only 2.4 open. Photo create/read/replace/remove, POST-only OCR abstention, the CU05 frontend, a real browser-to-backend synthetic-photo reading, reload and post-restart photo/reading persistence have synthetic evidence. The independent static review was obtained; H1/H2/M2/L1/L3/L6 are fixed, L5 documented, and L2/L4 accepted as low risks. The remaining 2.4 work is the matched photo-volume backup/restore drill and a production-like environment restart. OCR success, Tesseract invocation and representative accuracy remain unverified and are not approved; see the engineering record.

Latest BUILD instruction supersedes the earlier closure decision: M1 permits abstention on uncertainty but requires a real Tesseract attempt when safe admission permits. Clearly separable red fractions are excluded. The prior 14/15 checkpoint is historical; OCR and verification tasks were reopened. The endpoint now invokes a bounded worker and Tesseract on suitable crops; remaining safety and accuracy limitations are recorded below.

## 1. Review and contract gates

- [x] 1.1 Review the specified timestamp, lower-reading comparator and API contract; verify boundary, duplicate and ownership scenarios are unambiguous.
- [x] 1.2 Reconcile the implemented manual-selection/heuristic OCR contract: no independent identity guarantee, explicit user review and correction, synthetic red-fraction checks and no unsupported accuracy claims.
- [x] 1.3 Review photo publication/recovery and coordinated backup protocol and confirm target runtime support for memory, locking and durability; verify partial-failure and concurrent-access scenarios. The matched backup/restore drill remains part of 2.4.
- [x] 1.4 Record the user's explicit BUILD authorization and approved dependencies; verify it covers the reconciled contract.

## 2. Readings and private photos

- [x] 2.1 Implement reviewed additive reading metadata and persistence; verify validation, ordering, edit, no deletion, stable IDs and concurrent exact-duplicate tests.
- [x] 2.2 Implement private photo-volume integration and recovery strategy; verify size/decoded limits, replacement failures, safe cleanup and restart persistence using only permitted fixtures.
- [x] 2.3 Implement account-owned API and confirmation rules; verify foreign/missing resources, CSRF/Origin and no unconfirmed mutation with synthetic integration tests.
- [x] 2.4 Verify coordinated backup and restoration in an isolated Docker environment: synthetic PostgreSQL and photo volume restored together, DB and backend restarted, and the restored synthetic photo was retrieved through the authenticated API. See engineering evidence.

## 3. OCR and frontend

- [x] 3.1 Implement real opt-in Tesseract OCR with OpenCV preprocessing and deployment-wide supervision; OCR image validation now runs inside admission. Focused saturation and parent-death-during-decode tests, existing limits and synthetic OCR passed.
- [x] 3.2 Verify synthetic success, red-fraction exclusion, ambiguous/failure cases and the real API path. The previously misread synthetic canvas regression now reads correctly. The real image abstains; user explicitly accepts that limitation, without treating a provisional reference as verified.
- [x] 3.3 Implement accessible reading/history/edit UI and opt-in OCR interaction; verify explicit confirmation, editable suggestion, lower-reading warning and manual recovery with component tests.

## 4. Integration and closure evidence

- [ ] 4.1 Resolve the independent review's conflict between the unconditional red-fraction prohibition in the delta and heuristic detection in the design/implementation; user decision required before syncing.
- [x] 4.2 Rerun applicable checks after OCR integration; record evidence. Backend 207, frontend 75, focused Chromium, lint and type checks passed; see engineering record.
- [x] 4.3 Exercise real frontend/backend OCR success and abstention, photo, history and confirmation in authenticated DEV. Both synthetic browser flows passed after the review fixes; real-photo abstention remains an accepted limitation.
- [x] 4.4 Conduct one focused independent security/data-isolation review. Reviewer session `ses_e3f74ea88ffeULFU1uKGs5P3sK` reported three findings; decode admission and crop status were corrected and tested, while the red-fraction contract conflict remains open under 4.1. No second review was requested.
