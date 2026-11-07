# Interruption diary - proposed delta

## Purpose

Let account holders maintain their own domicile's interruption diary and export
a period-specific complaint-support report with overlap-safe duration totals.

## ADDED Requirements

### Requirement: Exclusive domicile-account authorization

Only the account with the registered domicile SHALL be allowed to save, consult,
correct, close and export its cuts. Other accounts SHALL NOT receive its private
records or PDF or modify its records through any of those actions.

#### Scenario: CU09-S09 All five operations enforce account ownership
- **GIVEN** domicile D is registered in A and B is another authenticated account
- **WHEN** A and B each attempt save, consult, correct, close and export for D
- **THEN** A is authorized subject to date validation and B is forbidden for all five actions without data exposure or mutation

### Requirement: Explicit login Origin and authenticated mutation CSRF boundary

The backend SHALL require an explicitly allowed trusted Origin for login. Missing,
`null`, malformed or foreign origins SHALL be rejected with 403 without issuing
a session cookie. Login SHALL NOT require a pre-authentication CSRF token.
Every authenticated operation that modifies state SHALL require both an allowed
Origin and a valid session-bound CSRF token; missing/invalid tokens SHALL yield
403 without modifying records or revoking the session. These rules reflect U09.

#### Scenario: Login rejects an untrusted or absent Origin
- **GIVEN** valid synthetic credentials and no authenticated session
- **WHEN** login is submitted with absent, null, malformed or foreign Origin
- **THEN** the backend returns 403, issues no session cookie and leaves the caller unauthenticated

#### Scenario: Trusted login establishes the authenticated CSRF boundary
- **GIVEN** valid synthetic credentials and an explicitly allowed Origin
- **WHEN** login is submitted without a CSRF token
- **THEN** login succeeds and returns the session-bound token for authenticated unsafe requests

#### Scenario: Every authenticated mutation rejects missing or invalid CSRF
- **GIVEN** an authenticated account and its domicile and ongoing cut
- **WHEN** logout, domicile creation, cut creation, correction or closure is submitted with missing or invalid CSRF
- **THEN** each request returns 403 and leaves the session, domiciles, cuts and versions unchanged

### Requirement: Store closed and ongoing interruption records

The system SHALL associate a saved cut with an authorized registered domicile,
its start, optional end, optional observations and optional complaint number.
An absent end SHALL denote an ongoing cut; a supplied valid end SHALL denote closure.

#### Scenario: CU09-S01 Valid closed record without complaint number
- **GIVEN** A's registered D, fixed validation time 2026-11-07 12:00 Buenos Aires, and cut 2026-11-01 10:00-12:00
- **WHEN** A saves the cut without a complaint number
- **THEN** D's closed cut is stored without requiring that optional number

#### Scenario: CU09-S02 Ongoing record keeps its end absent
- **GIVEN** an authorized registered domicile and a valid past start
- **WHEN** a cut is saved without an end and subsequently summarized
- **THEN** it is ongoing and summary generation does not populate its stored end

### Requirement: Buenos Aires minute-resolution temporal validation

Cut times SHALL use Buenos Aires local time and be recorded to the minute. Cut and
report-period times before 1970-01-01 00:00 Buenos Aires SHALL be rejected. Future
cut start/end dates SHALL be rejected. A supplied end SHALL be strictly after start.
These rules SHALL apply to creation, correction, closure and reporting; invalid
mutations SHALL leave existing records unchanged.

#### Scenario: CU09-S10 Reject future start or end and nonpositive interval
- **GIVEN** fixed validation time 2026-11-07 12:00 Buenos Aires and an own registered domicile
- **WHEN** a mutation uses start 12:01 that day, end 12:01, or end equal to/before a 10:00 start
- **THEN** each invalid mutation is rejected and any existing valid record remains unchanged

#### Scenario: Pre-1970 dates are rejected at the approved floor
- **GIVEN** an own registered domicile and a cut or report period starting 1969-12-31 23:59 Buenos Aires
- **WHEN** the owner saves, corrects, closes, summarizes or exports at that time
- **THEN** the request is rejected with a sanitized 422, no record changes, and 1970-01-01 00:00 remains accepted

### Requirement: Owner correction and explicit closure

The owner account SHALL be allowed to correct open and closed cuts under the same
temporal validation, and to close an ongoing cut with a valid end. Reporting
SHALL NOT perform an implicit stored closure.

#### Scenario: CU09-S11 Correct both open and closed cuts
- **GIVEN** A's open and closed records and fixed validation time 2026-11-07 12:00
- **WHEN** A corrects the open start to 2026-11-01 09:45 with end absent and the closed interval to 2026-11-01 10:15-11:45
- **THEN** both corrections persist; a future or nonpositive replacement is instead rejected without overwriting either record

#### Scenario: CU09-S12 Close an ongoing cut with a valid end
- **GIVEN** A's ongoing cut starting 2026-11-07 10:00 and fixed validation time that day 12:00
- **WHEN** A supplies end 10:30
- **THEN** the cut is stored closed at 10:30 and contributes 0 h 30 min to that day's period

### Requirement: Count only positive duration inside the queried period

The system SHALL count only each cut's intersection with the queried period and
SHALL exclude cuts with no positive duration there from summary and PDF results.
Exclusion from a query SHALL NOT delete the stored record.

#### Scenario: CU09-S05 Closed cut crosses the November start
- **GIVEN** a cut 2026-10-31 23:00 to 2026-11-01 02:00 in Buenos Aires
- **WHEN** the period 2026-11-01 00:00 to 2026-12-01 00:00 is summarized after that cut
- **THEN** it contributes 2 h 0 min, not its complete three-hour duration

#### Scenario: CU09-S13 Boundary-only or outside records are excluded
- **GIVEN** period 2026-11-01 00:00 to 2026-11-02 00:00 and valid cuts ending at its start, starting at its end, or wholly outside
- **WHEN** the period is summarized after those cuts
- **THEN** none is included in summary/PDF, they contribute 0 h 0 min, and their stored records remain

### Requirement: Cap ongoing duration without closing stored records

For an ongoing cut, the summary effective end SHALL be the earlier of generation
time and period end. Only positive period intersections SHALL count; the stored
end SHALL remain absent after summary or PDF generation.

#### Scenario: CU09-S07 Fixed generation time is the earlier bound
- **GIVEN** ongoing start 2026-11-01 10:00, period that day 00:00 to next day 00:00 and fixed generation 15:00
- **WHEN** summary/PDF is generated
- **THEN** effective end is 15:00, contribution is 5 h 0 min, status remains ongoing and PDF end reads “En curso”

#### Scenario: CU09-S08 Period end precedes generation
- **GIVEN** ongoing start 2026-11-01 22:00, period 2026-11-01 00:00 to 2026-11-02 00:00 and fixed generation 03:00 that next day
- **WHEN** the period is summarized
- **THEN** effective end is 00:00 and contribution is 2 h 0 min rather than 5 hours, without stored closure

### Requirement: Retain overlaps and show union totals in hours and minutes

The system SHALL retain overlapping records and count common time once within a
single domicile's positive period-clipped intervals. Total duration SHALL be
shown in hours and minutes.

#### Scenario: CU09-S04 Retained whole-hour overlaps total three hours
- **GIVEN** D's cuts 2026-11-01 10:00-12:00 and 11:00-13:00 inside the queried day
- **WHEN** summarized after 13:00
- **THEN** both records remain and total is 3 h 0 min, not 4 hours

#### Scenario: CU09-S14 Minute-resolution overlaps total sixty-five minutes
- **GIVEN** D's Buenos Aires cuts 2026-11-01 10:05-10:50 and 10:35-11:10
- **WHEN** summarized for that day after 11:10
- **THEN** those recorded minutes are preserved and union total is 1 h 5 min

### Requirement: Download the approved PDF content and table

Owner export SHALL include domicile, period, each included cut's dates/times/status,
total hours/minutes and supplied observations/complaint number. Rows SHALL form a
table ordered by start descending. Missing end SHALL read exactly “En curso”.

#### Scenario: CU09-S06 Required content preserves both overlapping rows
- **GIVEN** D's CU09-S04 cuts and that day as period, first cut note “Synthetic note” and complaint “TEST-001”, neither on the second
- **WHEN** the owner downloads the PDF
- **THEN** domicile, period, both dates/times/closed statuses, supplied text and 3 h 0 min total appear, with 11:00 before 10:00 and neither row omitted for overlap or absent optional text

#### Scenario: CU09-S15 Mixed table uses descending start and ongoing end text
- **GIVEN** D's 2026-11-01 closed cut 10:00-11:00 and open cut from 12:00, that day as period and fixed generation 13:30
- **WHEN** the owner downloads the PDF
- **THEN** 12:00 row precedes 10:00, their end cells are “En curso” and 11:00, both statuses appear and total is 2 h 30 min
