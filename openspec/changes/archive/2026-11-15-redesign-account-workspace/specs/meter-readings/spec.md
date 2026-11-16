# Spec Delta

## MODIFIED Requirements

### Requirement: Isolate visible history by selected meter

When the owner changes the selected meter in Mi cuenta, the frontend SHALL NOT display any reading history, photo or editable reading data belonging to the previously selected meter. It SHALL present only the selected meter's data and SHALL show the empty-history state when that meter has no readings. Trace: CU05, U13, U31 and the reproduced `frontend/e2e/cu05-history.spec.ts` regression.

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
