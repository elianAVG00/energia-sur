# meter-readings Specification

## Purpose

Enable account holders to maintain private confirmed kWh readings for their own meters, with optional photo and cautious OCR assistance.

## Requirements

### Requirement: Confirm valid readings before saving
The system SHALL require explicit confirmation before saving a reading. Its accumulated kWh SHALL be a nonnegative integer represented as a decimal string in API requests, responses and OCR suggestions and stored exactly. Inputs SHALL contain 1–131072 ASCII digits; longer strings SHALL return 422. Trace: CU05-R1, U13, D14 and technical limit approval.

#### Scenario: Manual reading without a photo
- **GIVEN** an owned meter and a valid nonfuture reading date
- **WHEN** the owner enters 0 kWh without a photo and confirms
- **THEN** the reading is saved for that meter

#### Scenario: Invalid value or future date
- **WHEN** an owner submits a missing, negative or fractional kWh value or a future date
- **THEN** the system rejects the submission without changing reading history

#### Scenario: Decimal digit limit
- **WHEN** an owner submits 131073 ASCII digits as `value_kwh`
- **THEN** the system returns 422 and does not mutate reading history

#### Scenario: Unconfirmed data
- **WHEN** the owner enters or edits a valid reading without confirming
- **THEN** no new reading or change is incorporated in history

### Requirement: Prevent duplicate reading date and time
PostgreSQL SHALL enforce one reading per meter and exact UTC instant normalized to seconds, including concurrent creates and edits. Different times on the same day and the same instant on different meters SHALL be allowed. Trace: U13, D05–D07.

#### Scenario: Same day and different times
- **GIVEN** a reading for an owned meter at 10:00
- **WHEN** its owner confirms a reading for that meter on the same day at 11:00
- **THEN** both readings are retained

#### Scenario: Exact timestamp conflict
- **GIVEN** a reading for an owned meter at a date and time
- **WHEN** another reading for that meter is created or edited to that exact date and time
- **THEN** the system rejects the conflict without overwriting either reading

#### Scenario: Concurrent duplicates and different meters
- **WHEN** two requests with distinct idempotency keys create readings for the same meter and normalized instant concurrently, and another meter has a reading at that instant
- **THEN** exactly one same-meter reading is created and the other request conflicts; the other meter's reading remains allowed

### Requirement: Normalize reading time
The system SHALL accept offset-aware ISO timestamps with seconds and no fractions, store UTC seconds and display `America/Argentina/Buenos_Aires`. Future instants SHALL be rejected. Trace: D05–D07 and technical review.

#### Scenario: Display local time
- **WHEN** a reading at 2026-11-07 15:00:00 UTC is displayed
- **THEN** its displayed Buenos Aires time is 2026-11-07 12:00:00

### Requirement: Warn on decreasing readings
When an entered reading is lower than the most recent earlier reading for that meter, excluding itself on edit, the UI SHALL warn the owner and allow confirmation and saving. Trace: CU05-S03, U13 and technical review.

#### Scenario: Save a decreasing reading
- **GIVEN** an earlier reading of 100 kWh for an owned meter
- **WHEN** the owner enters a later reading of 90 kWh
- **THEN** a warning is shown and the owner can confirm and save 90 kWh

### Requirement: Maintain meter reading history
The system SHALL list a meter's readings from newest to oldest, allow the owner to edit value, date and photo, and preserve the stable meter ID. It SHALL NOT offer reading deletion. Trace: U13, Q09.

#### Scenario: History and correction
- **GIVEN** two confirmed readings at different times for an owned meter
- **WHEN** the owner lists them and confirms a valid correction to the older reading
- **THEN** history is ordered newest first and the corrected reading remains linked to the same meter ID

#### Scenario: Deletion unavailable
- **WHEN** an owner manages a reading
- **THEN** no reading-deletion operation is offered

### Requirement: Optional photo constraints
A reading SHALL have at most one optional photo. The system SHALL accept JPG, PNG or WebP images up to 5 MB and 40,000,000 decoded pixels per frame and SHALL reject unsupported or oversized photos without saving an invalid attachment. Trace: U13, Q11 and subsequent user approval.

#### Scenario: Allowed and rejected attachments
- **WHEN** an owner supplies a valid supported image within the limit
- **THEN** it can be attached to the confirmed reading
- **WHEN** the supplied image is unsupported or exceeds 5 MB
- **THEN** the invalid attachment is rejected

### Requirement: Protect account-owned readings and photos
The system SHALL authorize reading, photo and OCR operations against the meter's owning account on the server. It SHALL prevent another account from reading or modifying the data. Authenticated state-changing operations SHALL enforce trusted Origin and session CSRF. Trace: SR02, SR04, U13.

#### Scenario: Cross-account access
- **GIVEN** account A owns a meter, reading and photo and B is another account
- **WHEN** B attempts to list, create, edit, retrieve the photo or request OCR for A's resources
- **THEN** access is denied without disclosing private data or changing A's records

#### Scenario: Foreign missing and mismatched resources
- **GIVEN** an authenticated account with valid request security credentials
- **WHEN** it requests a missing, foreign or mismatched meter, reading or photo, including through OCR
- **THEN** each returns the same 404 without disclosing resource existence or changing data

#### Scenario: Rejected unsafe request
- **WHEN** an authenticated mutation is submitted without valid CSRF or with an untrusted Origin
- **THEN** it is rejected without changing readings or photos

### Requirement: Persist photo privately
Photo bytes SHALL be stored in a persistent Docker volume managed by FastAPI; PostgreSQL SHALL store photo metadata rather than photo bytes. S3 and Cloudinary SHALL NOT be used. Photo access SHALL be private and ownership-checked. Trace: U13, Q11.

#### Scenario: Persistent private photo
- **GIVEN** a confirmed reading with a valid photo
- **WHEN** the application is restarted with its persistent volume and database intact
- **THEN** its owner can retrieve the photo and another account cannot

### Requirement: Protect unconfirmed photo processing
Before confirmation, an OCR photo and its derivatives SHALL remain in memory only, SHALL NOT be persisted or enter history, and SHALL be accessible only to the authorized account. Trace: SR04, U13, D08–D09.

#### Scenario: Unconfirmed OCR photo is not a resource
- **GIVEN** A requests OCR without confirming a reading
- **WHEN** another account requests access to A's meter or OCR request data
- **THEN** it receives no photo data and no reading is added to history; no staged-photo retrieval resource exists

#### Scenario: OCR privacy controls unavailable
- **WHEN** the runtime cannot verify that swap and core dumps are disabled for the API process
- **THEN** OCR abstains before the endpoint buffers the request body and does not start the engine

### Requirement: Preserve photos during replacement
The system SHALL retain the old photo until the replacement transaction succeeds, then clean up the old photo without affecting another reading. Failures SHALL NOT leave a confirmed reading pointing to an unavailable replacement. Trace: D08–D09, D13.

#### Scenario: Definitely rolled-back replacement
- **GIVEN** a confirmed reading with an existing photo
- **WHEN** replacement is definitively rejected or its transaction is rolled back
- **THEN** the old photo remains available and the reading is unchanged

#### Scenario: Indeterminate commit result
- **WHEN** the connection is lost during replacement commit and its outcome is unknown
- **THEN** both objects are retained until the transaction resolves and committed references can be checked; the client reconciles the reading version before retrying

#### Scenario: Cleanup failure after commit
- **WHEN** a committed replacement is followed by an old-photo cleanup failure
- **THEN** the new photo remains available and cleanup can be safely recovered without deleting live data

### Requirement: Restrict external photo transfer
Photo bytes and derivatives SHALL NOT be transferred to external services during upload, OCR, diagnostics or evaluation without the necessary explicit authorization. Trace: SR04, U13.

#### Scenario: OCR and diagnostics without transfer approval
- **GIVEN** an owner requests OCR and no external photo transfer is authorized
- **WHEN** the photo is processed or an error is diagnosed
- **THEN** neither the photo nor its derivatives are sent to an external service

### Requirement: Opt-in OCR suggestions with safe abstention
On request, local Tesseract SHALL attempt OCR on the user's intended kWh crop when safety permits. The system does not independently prove register identity. Only results passing its checks SHALL be editable suggestions; otherwise use the exact fallback. Suggestions SHALL NOT be saved without confirmation; manual entry SHALL remain available. Trace: U13, D01–D04, D10, M1 and subsequent BUILD instructions.

#### Scenario: Review and correct suggestion
- **GIVEN** a photo whose owner selects the kWh register
- **WHEN** the owner requests OCR and receives a suggestion
- **THEN** the owner can change the value and must explicitly confirm before it is saved

#### Scenario: Multiple detected digit sequences
- **GIVEN** a selected crop producing multiple detected digit sequences
- **WHEN** OCR evaluates the sequences
- **THEN** it produces no suggested value

#### Scenario: Selected identifier resembles a register
- **GIVEN** a selected identifier that looks like a confident digit sequence
- **WHEN** OCR cannot independently distinguish it from a register
- **THEN** a suggestion may be incorrect and the owner must review and confirm the actual kWh reading

#### Scenario: Insufficient confidence or unavailable evaluation
- **GIVEN** a crop whose digit segmentation or engine result fails the implemented checks
- **WHEN** the owner requests OCR
- **THEN** no value is suggested, the exact fallback message is displayed, and manual entry and confirmation remain available

### Requirement: Mask clearly separable red fractional digits
OCR SHALL mask clearly separable red fractional digits and suggest only the integer value when that boundary is unambiguous; when it is uncertain, OCR SHALL abstain with the exact fallback. A suggestion SHALL NOT be saved without explicit owner confirmation. Red-ink detection is heuristic, so no absolute exclusion guarantee is claimed. Trace: U13 and the 2026-11-13 human decision superseding the earlier absolute prohibition and the always-abstain clarification.

#### Scenario: Red fractional digit
- **GIVEN** a register showing black integer digits 12345 and a red fractional digit 6
- **WHEN** the owner requests OCR and the red digit is clearly separable
- **THEN** OCR may suggest 12345 from the integer digits, the fractional digit is excluded from the suggested value, and the suggestion is not saved before the owner confirms it

#### Scenario: Indistinguishable fractional digit
- **GIVEN** a fractional digit whose colour is faded or close to the integer ink and is therefore not classified as red by the mask
- **WHEN** OCR does not detect that the digits include a fractional part and produces a suggestion
- **THEN** the suggestion may include that digit, remains editable, is not saved automatically and requires the owner's explicit confirmation

#### Scenario: Uncertain fractional boundary
- **WHEN** OCR cannot reliably separate the red fraction from integer digits
- **THEN** no value is suggested and the exact fallback message is displayed

### Requirement: Recover from uncertain or failed OCR
On OCR failure or insufficient confidence the system SHALL abstain without suggesting a value and display exactly “No pudimos identificar con seguridad la lectura del medidor. Intentá subir una fotografía más clara o ingresá manualmente el valor en kWh”. The owner SHALL remain able to enter and confirm a value manually, and there SHALL be no automatic retry. Trace: U13, M1.

#### Scenario: Ambiguous register or OCR failure
- **WHEN** OCR cannot reliably read an ambiguous register, no identification evaluation is available, or the OCR engine fails
- **THEN** no value is suggested, the exact message is shown, and manual entry and confirmation remain available

### Requirement: Versioned meter-scoped reading corrections
Every reading PATCH SHALL atomically check its version and increment it on success, even if fields are unchanged. A stale version SHALL return 409 `VERSION_CONFLICT` without mutation. OCR SHALL use a separate meter-scoped endpoint from saving. Trace: D11–D12.

#### Scenario: Unchanged and stale corrections
- **GIVEN** a reading at version 1
- **WHEN** its owner submits an unchanged PATCH with version 1 and then a PATCH with version 1
- **THEN** the first advances to version 2 and the second returns 409 `VERSION_CONFLICT` without changing the reading or photo

#### Scenario: Concurrent corrections
- **GIVEN** two requests with the same current reading version
- **WHEN** both PATCH concurrently
- **THEN** exactly one succeeds and the other returns 409 `VERSION_CONFLICT` without overwriting the winner

### Requirement: Bound OCR resources
The system SHALL reject image bytes over 5,000,000 and SHALL abstain from OCR on images over 20,000,000 decoded pixels, engine runtime over 5 seconds or engine memory over 256 MiB. At most one OCR job SHALL execute deployment-wide, with no automatic retry. Trace: technical review.

#### Scenario: Engine deadline
- **WHEN** OCR exceeds its deadline
- **THEN** the engine is stopped, no value is suggested and manual entry remains available with the exact fallback message

#### Scenario: Oversized OCR dimensions and valid attachment
- **GIVEN** a supported image no larger than 5,000,000 bytes and larger than 20,000,000 but no more than 40,000,000 decoded pixels
- **WHEN** its owner requests OCR and later confirms a valid manual reading with that attachment
- **THEN** OCR abstains with the exact fallback and the attachment remains eligible for saving

### Requirement: Use meter-scoped reading transport
The meter-scoped create, list, detail, PATCH, OCR and photo endpoints SHALL follow the request/response contract in `design.md`, enforce ownership and provide no reading-deletion endpoint. Trace: D11–D12 and technical review.

#### Scenario: Replace or remove the optional photo
- **WHEN** an owner submits a valid current-version PATCH with photo action `replace` or `remove`
- **THEN** the selected photo change commits with the incremented reading version, or leaves the prior reading and photo unchanged on definite rejection or rollback; an indeterminate commit is reconciled before retry

### Requirement: Idempotent reading creation
The system SHALL atomically associate the creation attempt's stable idempotency key with the authenticated account, meter, payload and original result in PostgreSQL. Retries with the same key and payload SHALL return the original result. Reuse with a different payload SHALL return 409 `IDEMPOTENCY_KEY_REUSED` without mutation. Trace: D15.

#### Scenario: Retry after uncertain commit
- **WHEN** the owner retries a create using the same key and payload after losing the response
- **THEN** the original creation result is returned without creating another reading

#### Scenario: Concurrent retry of one attempt
- **WHEN** two concurrent requests use the same key and identical payload for the same owned meter
- **THEN** exactly one reading is created and both requests receive the original successful result

#### Scenario: Key reused with changed payload
- **GIVEN** an owner has created a reading using an idempotency key
- **WHEN** that owner reuses the key for the same meter with a different payload
- **THEN** the system returns 409 `IDEMPOTENCY_KEY_REUSED` and does not mutate readings

### Requirement: Isolate visible history by selected meter
When the owner changes the selected meter in the CU04 management view, the frontend SHALL NOT display any reading history, photo or editable reading data belonging to the previously selected meter. It SHALL present only the selected meter's data and SHALL show the empty-history state when that meter has no readings. Trace: CU05, U13 and the reproduced `frontend/e2e/cu05-history.spec.ts` regression.

#### Scenario: Switch between meters with different histories
- **GIVEN** meter `m1` has a reading and meter `m2` has a different reading
- **WHEN** the owner selects `m2` after viewing `m1`
- **THEN** only `m2`'s reading is visible and no `m1` reading remains

#### Scenario: Switch to a meter without readings
- **GIVEN** meter `m1` has a visible reading and meter `m2` has none
- **WHEN** the owner selects `m2`
- **THEN** the empty-history state is shown and no `m1` reading or editable value remains visible

#### Scenario: Rapid meter switching
- **WHEN** the owner changes the selected meter several times in quick succession
- **THEN** the final visible history corresponds only to the meter selected last and contains no data from intermediate meters

### Requirement: Reject stale meter history responses
A response for a previously selected meter, including a delayed, out-of-order or failed response, SHALL NOT replace, resurrect or blend into the visible history of the currently selected meter. Trace: CU05, U13 and reproduced regression.

#### Scenario: Pending or late request for the previous meter
- **GIVEN** the history request for `m1` is pending or delayed and the owner selects `m2`
- **WHEN** `m2`'s history is loading and any delayed `m1` response is discarded or cancelled
- **THEN** no `m1` reading appears and the visible history remains `m2`'s

#### Scenario: HTTP error after switching meters
- **GIVEN** meter `m1` has a visible reading
- **WHEN** the owner selects `m2` and its history request fails
- **THEN** the error state is shown without the `m1` reading or its editable data

### Requirement: Preserve exact kWh in selected history
Reading values SHALL remain exact decimal strings while a meter is selected and after switching meters, without changing the existing CU05 decimal-string contract. The value `9007199254740993` SHALL be displayed exactly and SHALL NOT be converted to a JavaScript number. Trace: CU05 D14 and numeric-contract preservation.

#### Scenario: Exact kWh preservation
- **GIVEN** the selected meter has a reading recorded as `9007199254740993` kWh
- **WHEN** the history is displayed, including after switching meters and back
- **THEN** the value is displayed exactly as `9007199254740993`
