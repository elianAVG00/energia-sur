import assert from 'node:assert/strict';
import test from 'node:test';
import { BillsClient, validDate, validDecimal } from '../src/features/bills/api.ts';
import { DiaryError } from '../src/lib/httpError.ts';
import { mockHttp } from './httpSupport.ts';

const signal = () => new AbortController().signal;
const key = '12345678-1234-4234-8234-123456789abc';
const bill = { id: 'bill', meter_id: 'meter', period_start: '2026-11-07', period_end: '2026-11-07', value_kwh: '9007199254740993.125', amount_ars: '0.01', file_type: 'application/pdf', version: 1 };
const input = { period_start: bill.period_start, period_end: bill.period_end, value_kwh: bill.value_kwh, amount_ars: bill.amount_ars, file_base64: 'cGRm', overlap_token: null };

test('create preserves decimal strings, file and idempotency key', async () => {
  const { http } = mockHttp(bill, 201, 'application/json', config => {
    assert.equal(config.url, '/api/meters/meter/bills');
    assert.equal(config.headers.get('Idempotency-Key'), key);
    assert.deepEqual(JSON.parse(String(config.data)), input);
  });
  assert.deepEqual(await new BillsClient(http).create('meter', input, key, signal()), bill);
});

test('edit retains file explicitly and validates version and ownership', async () => {
  const body = { ...input, file_base64: null, file_action: 'keep' as const, version: 1 };
  const good = mockHttp({ ...bill, version: 2 }, 200, 'application/json', config => assert.deepEqual(JSON.parse(String(config.data)), body));
  assert.equal((await new BillsClient(good.http).edit('meter', 'bill', body, signal())).version, 2);
  for (const row of [bill, { ...bill, version: 2, meter_id: 'other' }]) {
    await assert.rejects(new BillsClient(mockHttp(row).http).edit('meter', 'bill', body, signal()), DiaryError);
  }
});

test('overlap conflict exposes structured warning, including stale replacement', async () => {
  const response = { detail: 'Superposición', code: 'OVERLAP_CONFIRMATION_REQUIRED', overlap_token: 'fresh', overlaps: [{ id: 'other', period_start: '2026-11-07', period_end: '2026-11-10', version: 2 }] };
  const client = new BillsClient(mockHttp(response, 409).http);
  await assert.rejects(client.create('meter', input, key, signal()), error => error instanceof DiaryError && error.billWarning?.overlap_token === 'fresh' && error.billWarning.overlaps[0]?.period_start === '2026-11-07');
  const empty = new BillsClient(mockHttp({ ...response, overlaps: [] }, 409).http);
  await assert.rejects(empty.create('meter', input, key, signal()), error => error instanceof DiaryError && error.billWarning?.overlaps.length === 0);
  const bad = new BillsClient(mockHttp({ ...response, overlaps: [{ id: 'other' }] }, 409).http);
  await assert.rejects(bad.create('meter', input, key, signal()), error => error instanceof DiaryError && error.billWarning === null);
});

test('duplicates and private file errors are surfaced without treating them as attachments', async () => {
  const duplicate = new BillsClient(mockHttp({ detail: 'Duplicada', code: 'DUPLICATE_BILL' }, 409).http);
  await assert.rejects(duplicate.create('meter', input, key, signal()), error => error instanceof DiaryError && error.code === 'DUPLICATE_BILL');
  await assert.rejects(new BillsClient(mockHttp(new Blob(['not a bill']), 200, 'text/html').http).file('meter', 'bill', signal()), DiaryError);
  await assert.rejects(new BillsClient(mockHttp([{ ...bill, meter_id: 'other' }]).http).list('meter', signal()), DiaryError);
});

test('calendar and decimal input checks preserve exact values without rounding', () => {
  assert.equal(validDate('2026-02-29'), false);
  assert.equal(validDate('2024-02-29'), true);
  assert.equal(validDecimal('9007199254740993.125', 3), true);
  for (const value of ['-1', '1e2', '1.0001', '1234567890123456789']) assert.equal(validDecimal(value, 3), false);
  assert.equal(validDecimal('0.001', 2), false);
});
