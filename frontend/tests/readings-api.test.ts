import assert from 'node:assert/strict';
import test from 'node:test';
import { ReadingsClient, OCR_FALLBACK } from '../src/features/readings/api.ts';
import { DiaryError } from '../src/lib/httpError.ts';
import { mockHttp } from './httpSupport.ts';

const signal = () => new AbortController().signal;
const key = '12345678-1234-4234-8234-123456789abc';
const reading = { id: 'reading', meter_id: 'meter', recorded_at: '2026-01-01T00:00:00Z', value_kwh: '9007199254740993', has_photo: false, version: 1 };
const input = { recorded_at: '2026-01-01T00:00:00Z', value_kwh: '9007199254740993', confirmed: true as const, photo_base64: null };

test('creation retains the exact value and sends the caller-owned retry key', async () => {
  const { http } = mockHttp(reading, 201, 'application/json', config => {
    assert.equal(config.url, '/api/meters/meter/readings');
    assert.equal(config.headers.get('Idempotency-Key'), key);
    assert.match(String(config.data), /9007199254740993/);
  });
  const result = await new ReadingsClient(http).create('meter', input, key, signal());
  assert.equal(result.value_kwh, '9007199254740993');
});

test('rejects wrong ownership, non-string numeric values and wrong revisions', async () => {
  for (const data of [{ ...reading, meter_id: 'foreign' }, { ...reading, value_kwh: 10 }]) {
    const { http } = mockHttp(data, 201);
    await assert.rejects(new ReadingsClient(http).create('meter', input, key, signal()), DiaryError);
  }
  const { http } = mockHttp(reading);
  await assert.rejects(new ReadingsClient(http).edit('meter', 'reading',
    { ...input, version: 1, photo_action: 'keep' }, signal()), DiaryError);
});

test('OCR accepts exact fallback and rejects a numeric suggestion', async () => {
  const crop = { x: 0, y: 0, width: 10, height: 10 };
  const good = mockHttp({ status: 'abstained', value_kwh: null, message: OCR_FALLBACK }, 200, 'application/json', config => {
    assert.ok(config.headers.get('X-CSRF-Token'));
  });
  assert.equal((await new ReadingsClient(good.http).ocr('meter', 'synthetic', crop, signal())).status, 'abstained');
  const invalid = mockHttp({ status: 'suggested', value_kwh: 1 });
  await assert.rejects(new ReadingsClient(invalid.http).ocr('meter', 'synthetic', crop, signal()), DiaryError);
});

test('list and detail reject records for another meter or reading', async () => {
  const list = mockHttp([{ ...reading, meter_id: 'foreign' }]);
  await assert.rejects(new ReadingsClient(list.http).list('meter', signal()), DiaryError);
  const detail = mockHttp({ ...reading, id: 'different' });
  await assert.rejects(new ReadingsClient(detail.http).detail('meter', 'reading', signal()), DiaryError);
});

test('history rejects an unparseable timestamp instead of rendering it', async () => {
  const { http } = mockHttp([{ ...reading, recorded_at: '2026-99-99T99:99:99Z' }]);
  await assert.rejects(new ReadingsClient(http).list('meter', signal()), DiaryError);
});

test('create retries retain the exact key and payload supplied by the caller', async () => {
  const bodies: string[] = [];
  const { http } = mockHttp(reading, 201, 'application/json', config => {
    assert.equal(config.headers.get('Idempotency-Key'), key);
    bodies.push(String(config.data));
  });
  const client = new ReadingsClient(http);
  await client.create('meter', input, key, signal());
  await client.create('meter', input, key, signal());
  assert.equal(bodies.length, 2);
  assert.equal(bodies[0], bodies[1]);
});

test('photo rejects a non-image response', async () => {
  const { http } = mockHttp(new Blob(['synthetic']), 200, 'text/plain');
  await assert.rejects(new ReadingsClient(http).photo('meter', 'reading', signal()), DiaryError);
});

test('create surfaces idempotency conflict without retrying automatically', async () => {
  let calls = 0;
  const { http } = mockHttp({ detail: 'Conflicto', code: 'IDEMPOTENCY_KEY_REUSED' }, 409,
    'application/json', () => { calls++; });
  await assert.rejects(new ReadingsClient(http).create('meter', input, key, signal()),
    error => error instanceof DiaryError && error.status === 409 && error.code === 'IDEMPOTENCY_KEY_REUSED');
  assert.equal(calls, 1);
});
