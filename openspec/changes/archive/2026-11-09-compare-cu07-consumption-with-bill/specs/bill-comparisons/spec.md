# CU07 bill comparisons

## Purpose

Enable account holders to compare the consumption derived from their own CU05 meter
readings with the kWh recorded in a CU06 bill for the same meter, read-only and
without interpolation, proration or estimation.

## ADDED Requirements

### Requirement: Compare an owned bill with same-meter readings

The system SHALL compare a CU06 bill only with CU05 readings of the same meter and
owning account. It SHALL compute recorded consumption as the selected end reading
minus the selected start reading in kWh and SHALL NOT modify or delete those
records. Trace: CU07-R1, U14, SR02.

#### Scenario: Same meter and account

- **GIVEN** an owned meter M with a bill and readings, and an unrelated account B
- **WHEN** the owner requests a comparison for M's bill
- **THEN** only M's readings are considered and B's data is never exposed

#### Scenario: Foreign or missing resources

- **GIVEN** a bill or reading that belongs to another account, or does not exist
- **WHEN** the owner requests candidates or a comparison using it
- **THEN** the request returns the same 404 without disclosing data or mutating records

### Requirement: Bound candidates to the local +/-7-day window

The system SHALL treat a reading's comparison date as its
`America/Argentina/Buenos_Aires` local calendar date and SHALL accept a reading for a
billed boundary only when that date is within +/-7 days inclusive of the boundary.
An 8-day difference SHALL be rejected. Trace: CU07-R1, U14.

#### Scenario: Exact boundary dates

- **GIVEN** a bill for 2026-11-01 to 2026-11-07 and readings on those exact local dates
- **WHEN** comparison is requested
- **THEN** the pair is treated as exact and compared directly

#### Scenario: Seven-day tolerance accepted

- **GIVEN** a bill for 2026-11-01 to 2026-11-07, a start reading on 2026-10-25 and an
  end reading on 2026-11-14
- **WHEN** comparison is requested and explicitly confirmed
- **THEN** the pair is accepted as approximate and the comparison is calculated

#### Scenario: Eight-day difference rejected

- **GIVEN** a bill for 2026-11-01 to 2026-11-07 and only a reading on 2026-10-24
  (8 days before the start)
- **WHEN** candidates are requested
- **THEN** that reading is not a start candidate and, without another compatible
  reading, no comparison is calculated

### Requirement: Confirm approximate comparisons in the backend

The system SHALL require explicit confirmation for any comparison whose selected
boundary dates differ from the billed boundary dates, and SHALL validate that
confirmation on the server, not only in the interface. Without it the system SHALL
return a confirmation-required conflict and no comparison result. Trace: CU07-R1,
U14.

#### Scenario: Missing confirmation

- **GIVEN** a bill and an in-window reading pair whose local dates differ from the
  billed boundaries
- **WHEN** the comparison is requested without confirmation
- **THEN** the request returns 409 `CONFIRMATION_REQUIRED` including the real dates
  and candidates, and no consumption or difference is returned

#### Scenario: Confirmed approximate comparison

- **GIVEN** the same in-window pair
- **WHEN** the comparison is requested with explicit confirmation
- **THEN** it returns the recorded consumption, billed kWh and exact difference, and
  marks the result as not exact so the real dates and a warning can be shown

### Requirement: Select among multiple candidates

When more than one candidate reading exists for a boundary, the system SHALL require
manual selection of the start and end readings and SHALL validate that the submitted
reading IDs belong to the bill's meter and fall inside their windows. Trace: U14.

#### Scenario: Multiple start candidates

- **GIVEN** two readings within the start window and one within the end window
- **WHEN** the owner selects one start reading and submits the comparison
- **THEN** the selected reading is used and the other candidate is not merged,
  interpolated or averaged

#### Scenario: Invalid selection

- **WHEN** a submitted reading ID is duplicated, belongs to another meter, lies
  outside its boundary window, or the start reading's local date is after the end
  reading's
- **THEN** the request is rejected without a comparison result

### Requirement: Calculate an exact kWh difference without estimation

The system SHALL show recorded consumption, billed kWh and the exact absolute
difference in kWh, identifying whether recorded or billed consumption is higher or
that there is no difference. It SHALL NOT interpolate, prorate, estimate, round away
exact decimals or compute a percentage. Trace: CU07-R2, Q14, U14.

#### Scenario: Recorded consumption higher

- **GIVEN** a bill for 100 kWh and exact readings of 1000 and 1120 kWh
- **WHEN** comparison is requested
- **THEN** recorded consumption is 120 kWh, the difference is 20 kWh and recorded
  consumption is identified as higher

#### Scenario: Billed consumption higher

- **GIVEN** a bill for 100 kWh and exact readings of 1000 and 1080 kWh
- **WHEN** comparison is requested
- **THEN** recorded consumption is 80 kWh, the difference is 20 kWh and billed
  consumption is identified as higher

#### Scenario: Equal consumption

- **GIVEN** a bill for 100 kWh and exact readings of 1000 and 1100 kWh
- **WHEN** comparison is requested
- **THEN** the difference is 0 kWh and the result states that there is no difference

#### Scenario: Zero recorded consumption

- **GIVEN** a bill and two distinct readings with the same value inside their windows
- **WHEN** comparison is requested
- **THEN** recorded consumption is 0 kWh and the difference equals the billed kWh
  without division or percentage

### Requirement: Refuse to calculate incompatible comparisons

The system SHALL NOT calculate a comparison when a boundary has no compatible reading
or when the selected end reading is lower than the start reading, and SHALL report a
neutral no-comparison outcome without asserting a billing error. Trace: CU07-R1,
U14.

#### Scenario: Decreasing reading

- **GIVEN** a start reading of 1200 kWh and an end reading of 1100 kWh inside their
  windows
- **WHEN** comparison is requested
- **THEN** no consumption or difference is calculated and a neutral
  `decreasing_reading` outcome is returned

#### Scenario: No candidates

- **GIVEN** a bill whose start window contains no reading
- **WHEN** candidates are requested
- **THEN** the start candidate list is empty and no comparison is available

### Requirement: Show real dates for approximate periods

The system SHALL include the selected readings' real local dates and an exactness
flag in the comparison result so the interface can warn when the periods differ from
the billed period. Trace: U14.

#### Scenario: Approximate result displays real dates

- **GIVEN** a confirmed approximate comparison
- **WHEN** the result is rendered
- **THEN** it shows both billed boundaries, both real reading dates and a visible
  warning that the periods differ
