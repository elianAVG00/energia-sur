# Proposal: CU05 meter readings

## Why

Account holders need a private history of confirmed accumulated kWh readings for their own meters. CU05 is planned, not implemented; the user subsequently authorized Apply and D14/D15.

## What Changes

- Record, view and correct readings linked to stable CU04 meter IDs; do not offer deletion. Require confirmation, a nonnegative integer kWh value and a nonfuture date; warn but allow decreases and reject exact duplicate date/times.
- Allow at most one optional JPG, PNG or WebP photo up to 5 MB. Store photo bytes in a persistent Docker volume managed by FastAPI, with only metadata in PostgreSQL and owner-only access; no cloud image storage.
- Offer opt-in local Docker Tesseract OCR on a manually cropped attached photo, excluding clearly separable red fractional digits and producing only an editable suggestion after reliable identification of the kWh register. M1 permits abstention on uncertainty but does not replace the OCR attempt. Manual entry always remains available; no independent blur detector or automatic retry.
- Preserve CU04/CU09 security and existing functionality. Exclude CU06-CU08 implementation, physical meter replacement and any inference of consumption, billing or rollover rules.

## Capabilities

### New Capabilities

- `meter-readings`: owner-scoped CU05 reading history, optional private photo and user-confirmed OCR assistance.

### Modified Capabilities

- None; CU04 meter identity and CU09 session rules are reused without changing their requirements.

## Impact

Future work affects the FastAPI API, React UI, PostgreSQL metadata and Docker persistent storage. The user approved D01–D15 and BUILD; dependencies are not yet installed. See [design](design.md) and [decision register](../../../docs/use-cases/decisions.md). Synthetic image testing is permitted; a real image remains pending and no representative accuracy is implied.
