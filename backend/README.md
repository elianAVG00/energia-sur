# CU04 backend contract

CU04 adds owner-only `GET /domiciles/{d}/management`,
`PATCH /domiciles/{d}`, `GET` and `POST /domiciles/{d}/meters`, and
`GET` and `PATCH /domiciles/{d}/meters/{m}`. The original domicile list and
creation responses remain unchanged. All requests require the existing session;
writes additionally require a trusted Origin and session-bound CSRF token.
Missing, foreign and mismatched resources return the same 404 response.

The domicile management response contains `id`, `display_address`, and `version`;
its PATCH requires `display_address` and a strict positive integer `version`.
Meter responses contain `id`, `domicile_id`, `meter_number`, `alias`, and `version`.
Meter creation accepts `meter_number` and optional `alias`; correction requires
all three of `meter_number`, `alias` (nullable), and `version`. Unknown fields
are rejected. Every successful correction increments its version once, including
an unchanged correction. Stale corrections return 409 with `detail` and
`code: VERSION_CONFLICT`.

Numbers must consist exclusively of printable ASCII before end-space trimming;
after trimming ASCII spaces they must contain 1–120 characters. Case, internal
spaces, punctuation and leading zeros are retained. Duplicate detection is
account-wide, using ASCII-only case folding and ASCII-space trimming. Duplicate
meter writes return 409 with `detail` and `code: DUPLICATE_METER`. Alias accepts
null or Unicode text, rejects control characters before whitespace trimming,
converts blank text to null, and permits at most 120 characters after trimming.

Revision `0002_cu04` is additive to `0001_cu09`; it does not delete data, require
meters, or change interruption associations. Destructive downgrade is not supported.
The optional populated-upgrade test requires `TEST_CU04_MIGRATION=1` and an
isolated synthetic `TEST_DATABASE_URL` with schema-creation permission. It retains
a uniquely named synthetic schema; do not run it on a real-data database. See the
root README for the existing verification-image and synthetic acceptance workflow.
