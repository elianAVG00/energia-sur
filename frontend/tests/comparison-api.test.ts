import assert from 'node:assert/strict';
import test from 'node:test';
import { ComparisonsClient } from '../src/features/bills/comparison.ts';
import { DiaryError } from '../src/lib/httpError.ts';
import { mockHttp } from './httpSupport.ts';

const signal = () => new AbortController().signal;
const start = { reading_id: 'reading-a', recorded_at: '2026-11-01T15:00:00Z', local_date: '2026-11-01', value_kwh: '1000', version: 1 };
const end = { reading_id: 'reading-b', recorded_at: '2026-11-07T15:00:00Z', local_date: '2026-11-07', value_kwh: '1120', version: 1 };
const sets = { bill_id: 'bill', meter_id: 'meter', period_start: '2026-11-01', period_end: '2026-11-07', billed_kwh: '100', start_candidates: [start], end_candidates: [end] };
const result = { bill_id: 'bill', meter_id: 'meter', period_start: '2026-11-01', period_end: '2026-11-07', billed_kwh: '100', status: 'comparable', reason: null, exact: true, start_reading: start, end_reading: end, recorded_kwh: '120', difference_kwh: '20', outcome: 'recorded_higher' };

test('candidates validate ownership and window payload', async () => {
  const { http } = mockHttp(sets, 200, 'application/json', config => {
    assert.equal(config.url, '/api/meters/meter/bills/bill/comparison-candidates');
  });
  assert.deepEqual(await new ComparisonsClient(http).candidates('meter', 'bill', signal()), sets);
  await assert.rejects(new ComparisonsClient(mockHttp({ ...sets, meter_id: 'other' }).http).candidates('meter', 'bill', signal()), DiaryError);
  await assert.rejects(new ComparisonsClient(mockHttp({ ...sets, start_candidates: [{ ...start, value_kwh: '-1' }] }).http).candidates('meter', 'bill', signal()), DiaryError);
});

test('exact comparison omits the confirmation flag', async () => {
  const { http } = mockHttp(result, 200, 'application/json', config => {
    assert.equal(config.url, '/api/meters/meter/bills/bill/comparison?start_reading_id=reading-a&end_reading_id=reading-b');
  });
  assert.deepEqual(await new ComparisonsClient(http).compare('meter', 'bill', 'reading-a', 'reading-b', false, signal()), result);
});

test('approximate comparison sends the confirmation flag', async () => {
  const approximate = { ...result, exact: false };
  const { http } = mockHttp(approximate, 200, 'application/json', config => {
    assert.equal(config.url, '/api/meters/meter/bills/bill/comparison?start_reading_id=reading-a&end_reading_id=reading-b&confirm_approximate=true');
  });
  assert.equal((await new ComparisonsClient(http).compare('meter', 'bill', 'reading-a', 'reading-b', true, signal())).exact, false);
});

test('confirmation conflict exposes structured real dates and candidates', async () => {
  const body = {
    detail: 'Confirmá la comparación aproximada.', code: 'CONFIRMATION_REQUIRED',
    period_start: '2026-11-01', period_end: '2026-11-07',
    start_local_date: '2026-10-25', end_local_date: '2026-11-14',
    start_candidates: [start], end_candidates: [end],
  };
  await assert.rejects(
    new ComparisonsClient(mockHttp(body, 409).http).compare('meter', 'bill', 'reading-a', 'reading-b', false, signal()),
    error => error instanceof DiaryError && error.code === 'CONFIRMATION_REQUIRED' &&
      error.comparisonWarning?.start_local_date === '2026-10-25' &&
      error.comparisonWarning?.end_candidates[0]?.value_kwh === '1120',
  );
  await assert.rejects(
    new ComparisonsClient(mockHttp({ ...body, start_candidates: [{ reading_id: 'x' }] }, 409).http).compare('meter', 'bill', 'reading-a', 'reading-b', false, signal()),
    error => error instanceof DiaryError && error.code === 'CONFIRMATION_REQUIRED' && error.comparisonWarning === null,
  );
});

test('decreasing and malformed results are distinguished', async () => {
  const decreasing = { ...result, status: 'no_comparison', reason: 'decreasing_reading', recorded_kwh: null, difference_kwh: null, outcome: null };
  assert.equal((await new ComparisonsClient(mockHttp(decreasing).http).compare('meter', 'bill', 'reading-a', 'reading-b', false, signal())).reason, 'decreasing_reading');
  await assert.rejects(new ComparisonsClient(mockHttp({ ...result, outcome: 'hacked' }).http).compare('meter', 'bill', 'reading-a', 'reading-b', false, signal()), DiaryError);
  await assert.rejects(new ComparisonsClient(mockHttp({ ...result, meter_id: 'other' }).http).compare('meter', 'bill', 'reading-a', 'reading-b', false, signal()), DiaryError);
});
