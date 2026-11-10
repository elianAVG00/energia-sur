# consumption-trends Specification

## Purpose
Enable account holders to view their own meter's consumption evolution between CU05 readings and obtain a deterministic, non-factured estimate for a chosen number of days.

## Requirements

### Requirement: Show per-interval consumption evolution
The system SHALL show the selected meter's reading history as consecutive intervals between readings, each with its consumption in kWh and daily average in kWh/day, not only a merged total. Trace: CU08-R1, D03, D07, Q16.

#### Scenario: Two intervals from three readings
- **GIVEN** valid meter M readings of 1000, 1020 and 1080 kWh on 2026-11-01, 2026-11-03 and 2026-11-07, with elapsed intervals of exactly 2 and 4 days
- **WHEN** evolution is viewed
- **THEN** it includes the separate intervals 2026-11-01→2026-11-03 as 20 kWh and 10 kWh/day, and 2026-11-03→2026-11-07 as 60 kWh and 15 kWh/day

### Requirement: Use real elapsed time for daily average
The daily average of an interval SHALL use the real elapsed time between the two readings (including same-day readings measured as a fraction of a day), not calendar months or assumed period lengths. Trace: D03, D05, Q16.

#### Scenario: Irregular and same-day intervals
- **GIVEN** readings 1000 kWh on 2026-11-01 00:00 and 1030 kWh on 2026-11-06 00:00, then 1038 kWh on 2026-11-06 12:00
- **WHEN** evolution is viewed
- **THEN** the first interval is 30 kWh over 5 days (6 kWh/day) and the second is 8 kWh over 0.5 day (16 kWh/day), each using elapsed time rather than a whole-month assumption

### Requirement: Deterministic estimate from the last interval
The system SHALL compute the estimate deterministically as the daily average of the meter's last chronological interval (the two most recent readings by `recorded_at`) multiplied by the chosen number of days. A decreasing last interval SHALL yield no estimate and SHALL NOT fall back to older intervals. It SHALL NOT use AI, historical averages or other intervals. Trace: D01, CU08-R2, Q15, R02.

#### Scenario: Estimate uses the two latest readings
- **GIVEN** meter M readings of 1000, 1020 and 1080 kWh on 2026-11-01, 2026-11-03 and 2026-11-07, and another meter's later reading
- **WHEN** an estimate is requested for M for 7 days
- **THEN** it is based on M's 1020 kWh (11-03) and 1080 kWh (11-07) interval with daily average 15 kWh/day, yielding a 105 kWh estimate, ignoring the other meter

#### Scenario: Decreasing latest interval yields no estimate
- **GIVEN** meter M readings of 1000, 1080 and 1020 kWh in chronological order
- **WHEN** an estimate is requested
- **THEN** no estimate is returned because the last interval 1080→1020 is decreasing, and the earlier 1000→1080 interval is not used as a fallback base

### Requirement: Manual 1 to 90 day estimation horizon
The estimation horizon SHALL be a manual selector accepting a whole number of days from 1 to 90 inclusive; values outside that range SHALL be rejected without an estimate. Trace: D02, Q16.

#### Scenario: Reject out-of-range horizons
- **GIVEN** an owned meter with at least two valid readings
- **WHEN** an owner requests an estimate for 0 or 91 days
- **THEN** the request is rejected and no estimate is returned

#### Scenario: Accept boundary horizons
- **GIVEN** an owned meter with at least two valid readings
- **WHEN** an owner requests an estimate for 1 day and then 90 days
- **THEN** the system returns an estimate for each using the same deterministic formula

### Requirement: Mark decreasing intervals as not calculable
A decreasing interval (end reading lower than start reading) SHALL be shown as not calculable, SHALL NOT produce negative consumption and SHALL NOT serve as the estimation base; other intervals in the same meter's history SHALL still be shown. Trace: D04, CU05-S03, Q10, R02.

#### Scenario: Decreasing interval does not block the history
- **GIVEN** meter M readings of 1000, 1080 and 1020 kWh in chronological order
- **WHEN** evolution and estimation are viewed
- **THEN** the 1000→1080 interval is calculable, the 1080→1020 interval is shown as not calculable with no negative consumption, and no estimate is produced because the last interval is decreasing

### Requirement: Compute in UTC and display Buenos Aires time
The system SHALL compute elapsed time internally using real UTC instants and SHALL display reading times in `America/Argentina/Buenos_Aires`. Trace: D05.

#### Scenario: UTC reading displayed in local time
- **GIVEN** a stored reading recorded at 2026-11-07 15:00:00 UTC
- **WHEN** it is displayed
- **THEN** its displayed Buenos Aires time is 2026-11-07 12:00:00

### Requirement: Accept zero intervals and zero estimates
The system SHALL accept a 0 kWh interval with a 0 kWh/day daily average, and SHALL return a 0 kWh estimate when the last valid interval has a zero daily average. Trace: D06.

#### Scenario: Equal consecutive readings
- **GIVEN** two distinct same-meter readings with the same value
- **WHEN** evolution and estimation are viewed
- **THEN** the interval is 0 kWh and 0 kWh/day, and a chosen-horizon estimate is 0 kWh

### Requirement: Separate real and daily-average views
The system SHALL present real consumption (kWh) and daily average (kWh/day) as two distinct views, keeping units explicit, and SHALL visually distinguish historical intervals from the estimated projection. Trace: D07, CU08-R1.

#### Scenario: Historical and estimated are distinguishable
- **GIVEN** a meter with calculable intervals and a valid estimation base
- **WHEN** evolution and an estimate are rendered together
- **THEN** real consumption and daily average appear in separate views and the estimated portion is visually distinct from the historical intervals

#### Scenario: Units stay distinct
- **GIVEN** a meter with calculable intervals and an estimate
- **WHEN** evolution and an estimate are displayed
- **THEN** consumption and estimate values are labeled kWh and daily-average values are labeled kWh/day, never merged

### Requirement: Use only CU05 readings as the source
The estimate and evolution SHALL be derived exclusively from the meter's CU05 readings. CU06 bills and CU07 comparison rules SHALL NOT be consulted or combined. Trace: D08.

#### Scenario: Bills and comparisons are not consulted
- **GIVEN** a meter with CU05 readings, CU06 bills and a possible CU07 comparison
- **WHEN** evolution or an estimate is requested
- **THEN** the result uses only the readings and never the bill kWh or the comparison outcome

### Requirement: Two-decimal display with orientative warning
The system SHALL present estimated and daily-average values to two decimal places and SHALL show the warning "orientativa, no facturada" on the estimate so it is not mistaken for a billed value. Trace: D09.

#### Scenario: Estimate is clearly orientative
- **GIVEN** an owned meter with a valid estimation base and a chosen horizon
- **WHEN** an estimate is displayed
- **THEN** its value is shown to two decimal places together with the warning "orientativa, no facturada"

### Requirement: Render tiny positive values without mislabeling them as zero
The system SHALL render a computed value that is positive but rounds to "0.00" at two decimals as a distinct less-than indicator rather than "0.00", so it is not confused with the real zeros permitted for zero intervals. Trace: R06.

#### Scenario: Tiny positive value shown distinctly
- **GIVEN** a computed daily-average or estimate value that is positive but rounds to "0.00" at two decimals
- **WHEN** the value is displayed
- **THEN** the UI shows a less-than indicator (for example "< 0.01") instead of "0.00"

### Requirement: Flag sub-day intervals as not representative
The system SHALL still compute an interval shorter than 24 hours but SHALL flag it in the UI as not representative of a full day. Trace: R04.

#### Scenario: Same-day interval flagged
- **GIVEN** two readings of the same meter less than 24 hours apart
- **WHEN** evolution or an estimate based on that interval is viewed
- **THEN** the calculation is still produced and the UI shows a "poco representativo" (not representative) warning

### Requirement: Filter by owned meter and inclusive date range
The system SHALL allow filtering evolution by the owner's own meter and by an inclusive date range, including whole intervals that overlap or touch the range with their real endpoint dates visible, and SHALL enforce account ownership so another account cannot read the meter's data. Trace: D10, SR02, Q03, R05.

#### Scenario: Crossing interval included whole
- **GIVEN** a meter with an interval whose endpoints lie outside the selected date range but the interval overlaps or touches it
- **WHEN** the owner filters by that range
- **THEN** the interval is included in full with its real endpoint dates visible, without clipping, interpolation or proration

#### Scenario: Cross-account isolation
- **GIVEN** account A owns meter M and account B does not
- **WHEN** B requests evolution or an estimate for M
- **THEN** the request returns the same 404 as a missing resource and discloses no reading data

### Requirement: No estimate without a valid interval base
The system SHALL NOT return an estimate when the selected meter has zero or one reading, or when its last chronological interval is decreasing, and SHALL signal that the base prerequisite is unmet. Trace: CU08-S03, Q15, R02, R07.

#### Scenario: Insufficient readings show an empty state
- **GIVEN** a meter with zero or one reading
- **WHEN** an estimate is requested
- **THEN** no estimate is returned and the UI shows an empty state indicating the base prerequisite is not satisfied

### Requirement: Use current values in UTC chronological order
The system SHALL treat a reading as valid by the same rules CU05 applies to confirmed stored readings, SHALL order readings by `recorded_at` UTC using their current stored values (including edits), and SHALL NOT model physical meter replacement. Trace: R01, R03, Q10.

#### Scenario: Corrected reading is ordered by its recorded time
- **GIVEN** a reading whose value or time was edited
- **WHEN** evolution is computed
- **THEN** it is placed by its current `recorded_at` UTC and current value, not by edit time, and no meter replacement is assumed
