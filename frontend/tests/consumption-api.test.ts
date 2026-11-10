import assert from 'node:assert/strict';
import test from 'node:test';
import { ConsumptionClient } from '../src/features/consumption/api.ts';
import { DiaryError } from '../src/lib/httpError.ts';
import { mockHttp } from './httpSupport.ts';

const signal = () => new AbortController().signal;
const interval = {
  start_reading_id: 'a', end_reading_id: 'b',
  start_at: '2026-11-01T15:00:00Z', end_at: '2026-11-03T15:00:00Z',
  start_local_date: '2026-11-01', end_local_date: '2026-11-03',
  start_value_kwh: '1000', end_value_kwh: '1020',
  consumption_kwh: '20', daily_average_kwh_day: '10',
  calculable: true, sub_day: false, below_minimum: false,
};
const evolution = { meter_id: 'meter', intervals: [interval] };
const estimate = {
  meter_id: 'meter', status: 'available', days: 7, daily_average_kwh_day: '15', estimate_kwh: '105',
  orientative: true, below_minimum: false, daily_average_below_minimum: false, sub_day: false,
  base_start_reading_id: 'b', base_end_reading_id: 'c',
  base_start_at: '2026-11-03T15:00:00Z', base_end_at: '2026-11-07T15:00:00Z',
};

test('evolution builds the endpoint and validates the payload', async () => {
  const { http } = mockHttp(evolution, 200, 'application/json', config => {
    assert.equal(config.url, '/api/meters/meter/consumption-evolution');
  });
  assert.deepEqual(await new ConsumptionClient(http).evolution('meter', '', '', signal()), evolution);
  await assert.rejects(new ConsumptionClient(mockHttp({ ...evolution, meter_id: 'other' }).http).evolution('meter', '', '', signal()), DiaryError);
  await assert.rejects(new ConsumptionClient(mockHttp({ ...evolution, intervals: [{ ...interval, calculable: true, consumption_kwh: null }] }).http).evolution('meter', '', '', signal()), DiaryError);
});

test('evolution appends inclusive from/to date filters', async () => {
  const { http } = mockHttp(evolution, 200, 'application/json', config => {
    assert.equal(config.url, '/api/meters/meter/consumption-evolution?from=2026-11-01&to=2026-11-07');
  });
  await new ConsumptionClient(http).evolution('meter', '2026-11-01', '2026-11-07', signal());
});

test('evolution accepts a decreasing (not calculable) interval', async () => {
  const decreasing = {
    meter_id: 'meter', intervals: [{ ...interval, calculable: false, consumption_kwh: null, daily_average_kwh_day: null }],
  };
  const { http } = mockHttp(decreasing, 200, 'application/json');
  const value = await new ConsumptionClient(http).evolution('meter', '', '', signal());
  assert.equal(value.intervals[0]?.calculable, false);
  assert.equal(value.intervals[0]?.consumption_kwh, null);
});

test('estimate builds the endpoint and validates the payload', async () => {
  const { http } = mockHttp(estimate, 200, 'application/json', config => {
    assert.equal(config.url, '/api/meters/meter/consumption-estimate?days=7');
  });
  assert.deepEqual(await new ConsumptionClient(http).estimate('meter', 7, signal()), estimate);
  await assert.rejects(new ConsumptionClient(mockHttp({ ...estimate, estimate_kwh: '-1' }).http).estimate('meter', 7, signal()), DiaryError);
  await assert.rejects(new ConsumptionClient(mockHttp({ ...estimate, meter_id: 'other' }).http).estimate('meter', 7, signal()), DiaryError);
});

test('estimate accepts an unavailable base outcome', async () => {
  const unavailable = { meter_id: 'meter', status: 'base_unavailable', reason: 'decreasing_latest' };
  const { http } = mockHttp(unavailable, 200, 'application/json');
  const value = await new ConsumptionClient(http).estimate('meter', 7, signal());
  assert.equal(value.status, 'base_unavailable');
  await assert.rejects(
    new ConsumptionClient(mockHttp({ ...unavailable, reason: 'hacked' }).http).estimate('meter', 7, signal()),
    DiaryError,
  );
});
