# CU05 reading history isolation

## ADDED Requirements

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
