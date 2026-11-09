import assert from 'node:assert/strict';
import test from 'node:test';
import { ReadingsClient } from '../src/features/readings/api.ts';
import { lowerReadingWarning } from '../src/features/readings/warning.ts';
import { mockHttp } from './httpSupport.ts';

test('loaded history selects the most recent earlier reading without losing precision', async () => {
  const row = (id: string, recorded_at: string, value_kwh: string) => ({
    id, meter_id: 'meter', recorded_at, value_kwh, has_photo: false, version: 1,
  });
  const rows = [
    row('older', '2026-01-01T00:00:00Z', '1'),
    row('later', '2026-01-03T00:00:00Z', '2'),
    row('previous', '2026-01-02T00:00:00Z', '9007199254740993'),
  ];
  const { http } = mockHttp(rows);
  const loaded = await new ReadingsClient(http).list('meter', new AbortController().signal);
  assert.equal(lowerReadingWarning(loaded, 'meter', '2026-01-02T20:00:00-03:00', '9007199254740992'), true);
  assert.equal(lowerReadingWarning(loaded, 'meter', '2026-01-02T20:00:00-03:00', '9007199254740993'), false);
  assert.equal(lowerReadingWarning(loaded, 'meter', '2026-01-02T20:00:00-03:00', 'bad'), null);
  assert.equal(lowerReadingWarning(loaded, 'meter', '2026-01-02T22:00:00-03:00', '3'), false);
});

test('editing excludes itself and equal instants and never compares another meter', async () => {
  const rows = [
    { id: 'edit', meter_id: 'meter', recorded_at: '2026-01-02T00:00:00Z', value_kwh: '100', has_photo: false, version: 1 },
    { id: 'earlier', meter_id: 'meter', recorded_at: '2026-01-01T00:00:00Z', value_kwh: '10', has_photo: false, version: 1 },
  ];
  const { http } = mockHttp(rows);
  const loaded = await new ReadingsClient(http).list('meter', new AbortController().signal);
  assert.equal(lowerReadingWarning(loaded, 'meter', '2026-01-03T00:00:00Z', '20', 'edit'), false);
  assert.equal(lowerReadingWarning(loaded, 'meter', '2026-01-01T00:00:00Z', '1'), null);
  assert.equal(lowerReadingWarning(loaded, 'other', '2026-01-03T00:00:00Z', '1'), null);
  assert.equal(lowerReadingWarning(loaded, 'meter', 'invalid', '1'), null);
});
