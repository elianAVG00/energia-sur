import assert from 'node:assert/strict';
import { test } from 'node:test';
import { loginSchema, domicileSchema, cutSchema, closedCutSchema, closeSchema, periodSchema } from '../src/features/diary/schemas.ts';
import { duplicateAddress, meterSchema } from '../src/features/domiciles/schemas.ts';

const draft = { start_at: '2026-11-01T10:00', end_at: '', observations: '', complaint_number: '' };

test('meter form preserves identifiers and passes server-owned validation to the backend', () => {
  assert.deepEqual(meterSchema.parse({ meter_number: '  001-Ab  ', alias: '' }), { meter_number: '  001-Ab  ', alias: null });
  assert.deepEqual(meterSchema.parse({ meter_number: '001', alias: ' Medidor eléctrico ' }), { meter_number: '001', alias: ' Medidor eléctrico ' });
  assert.equal(meterSchema.safeParse({ meter_number: ' ', alias: '' }).success, false);
});

test('duplicate address warning compares trimmed own rows and excludes the edited row', () => {
  const rows = [{ id: 'one', display_address: 'Example 1' }, { id: 'two', display_address: 'Example 2' }];
  assert.equal(duplicateAddress(' Example 1 ', rows), true);
  assert.equal(duplicateAddress('Example 1', rows, 'one'), false);
  assert.equal(duplicateAddress('example 1', rows), false);
  assert.equal(duplicateAddress(' ', rows), false);
});

test('login requires transient credentials and preserves exact password text', () => {
  assert.equal(loginSchema.safeParse({ username: '', password: 'synthetic' }).success, false);
  assert.equal(loginSchema.safeParse({ username: 'synthetic', password: '' }).success, false);
  assert.equal(loginSchema.safeParse({ username: 'u'.repeat(80), password: 'p'.repeat(1024) }).success, true);
  assert.equal(loginSchema.safeParse({ username: 'u'.repeat(81), password: 'synthetic' }).success, false);
  assert.equal(loginSchema.safeParse({ username: 'synthetic', password: 'p'.repeat(1025) }).success, false);
  assert.equal(loginSchema.parse({ username: 'synthetic', password: ' synthetic ' }).password, ' synthetic ');
});

test('domicile schema trims the accepted display address and enforces its limit', () => {
  assert.deepEqual(domicileSchema.parse({ display_address: '  Synthetic QA  ' }), { display_address: 'Synthetic QA' });
  assert.equal(domicileSchema.safeParse({ display_address: '   ' }).success, false);
  assert.equal(domicileSchema.safeParse({ display_address: 'a'.repeat(300) }).success, true);
  assert.equal(domicileSchema.safeParse({ display_address: 'a'.repeat(301) }).success, false);
});

test('empty optional cut values become explicit API nulls without changing field names', () => {
  assert.deepEqual(cutSchema.parse(draft), { start_at: draft.start_at, end_at: null, observations: null, complaint_number: null });
  const completed = { ...draft, end_at: '2026-11-01T12:00', observations: 'Energía sintética Álvarez', complaint_number: 'QA-001' };
  assert.deepEqual(cutSchema.parse(completed), completed);
  assert.equal(cutSchema.parse({ ...draft, observations: ' ' }).observations, ' ');
});

test('cut schemas enforce approved text boundaries and associate closed-end errors', () => {
  assert.equal(cutSchema.safeParse({ ...draft, observations: 'a'.repeat(4000), complaint_number: 'b'.repeat(120) }).success, true);
  assert.equal(cutSchema.safeParse({ ...draft, observations: 'a'.repeat(4001) }).success, false);
  assert.equal(cutSchema.safeParse({ ...draft, complaint_number: 'b'.repeat(121) }).success, false);
  const closed = closedCutSchema.safeParse(draft);
  assert.equal(closed.success, false);
  if (!closed.success) assert.deepEqual(closed.error.issues[0]?.path, ['end_at']);
  assert.equal(closedCutSchema.safeParse({ ...draft, end_at: '2026-11-01T12:00' }).success, true);
});

test('required minute fields reject empty or wrong-shape form input', () => {
  assert.equal(cutSchema.safeParse({ ...draft, start_at: '' }).success, false);
  assert.equal(cutSchema.safeParse({ ...draft, start_at: '2026-11-01T10:00:30' }).success, false);
  assert.equal(closeSchema.safeParse({ end_at: '' }).success, false);
  assert.equal(closeSchema.safeParse({ end_at: '2026-11-01T12:00' }).success, true);
  assert.equal(periodSchema.safeParse({ period_start: draft.start_at, period_end: '' }).success, false);
});

test('form schemas leave server clock, historical floor and interval ordering to the backend', () => {
  assert.equal(cutSchema.safeParse({ ...draft, start_at: '2999-11-01T10:00' }).success, true);
  assert.equal(cutSchema.safeParse({ ...draft, start_at: '1969-12-31T10:00' }).success, true);
  assert.equal(cutSchema.safeParse({ ...draft, end_at: '2026-11-01T09:00' }).success, true);
  assert.equal(periodSchema.safeParse({ period_start: '2999-11-01T10:00', period_end: '2026-11-01T09:00' }).success, true);
});
