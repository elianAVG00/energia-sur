import assert from 'node:assert/strict';
import test from 'node:test';
import { AdminClient } from '../src/features/admin/api.ts';
import { DiaryError } from '../src/lib/httpError.ts';
import { mockHttp } from './httpSupport.ts';

const signal = () => new AbortController().signal;

const sources = {
  sources: [
    {
      key: 'outages', scheduler_enabled: true, interval_seconds: 300, version: 1,
      last_attempt_at: '2026-11-13T12:00:00Z', last_attempt_outcome: 'ok',
      last_attempt_error: null, last_success_at: '2026-11-13T12:00:00Z',
      last_skipped_locked_at: null,
    },
    {
      key: 'scheduled_works', scheduler_enabled: false, interval_seconds: 600, version: 2,
      last_attempt_at: '2026-11-13T11:45:00.123456Z', last_attempt_outcome: 'timeout',
      last_attempt_error: 'EnreTimeout', last_success_at: null,
      last_skipped_locked_at: '2026-11-13T11:40:00Z',
    },
  ],
};

test('sources uses the admin endpoint, needs no CSRF and validates both sources', async () => {
  const { http } = mockHttp(sources, 200, 'application/json', config => {
    assert.equal(config.url, '/api/admin/sources');
    assert.equal(config.method, 'get');
    assert.equal(config.headers.get('X-CSRF-Token'), undefined);
  });
  const result = await new AdminClient(http, http).sources(signal());
  assert.equal(result.sources.length, 2);
  assert.equal(result.sources[1]?.last_attempt_outcome, 'timeout');
  assert.equal(result.sources[1]?.last_success_at, null);
});

test('setInterval patches the current version with CSRF and validates the response', async () => {
  const response = { key: 'outages', interval_seconds: 900, version: 2 };
  const { http } = mockHttp(response, 200, 'application/json', config => {
    assert.equal(config.url, '/api/admin/sources/outages/interval');
    assert.equal(config.method, 'patch');
    assert.deepEqual(JSON.parse(String(config.data)), { interval_seconds: 900, version: 1 });
    assert.equal(config.headers.get('X-CSRF-Token'), 'current-csrf');
  });
  const result = await new AdminClient(http, http).setInterval('outages', 900, 1, signal());
  assert.deepEqual(result, response);
});

test('refresh posts with CSRF and returns the real failure outcome', async () => {
  const response = {
    key: 'scheduled_works', outcome: 'timeout', http_status: null,
    detail_code: 'EnreTimeout', started_at: '2026-11-13T12:00:00Z',
    finished_at: '2026-11-13T12:00:20Z',
  };
  const { http } = mockHttp(response, 200, 'application/json', config => {
    assert.equal(config.url, '/api/admin/sources/scheduled_works/refresh');
    assert.equal(config.method, 'post');
    assert.equal(config.headers.get('X-CSRF-Token'), 'current-csrf');
  });
  const result = await new AdminClient(http, http).refresh('scheduled_works', signal());
  assert.equal(result.outcome, 'timeout');
  assert.equal(result.detail_code, 'EnreTimeout');
});

test('409 SOURCE_BUSY and VERSION_CONFLICT keep their codes', async () => {
  const busy = mockHttp({ detail: 'busy', code: 'SOURCE_BUSY' }, 409);
  await assert.rejects(
    new AdminClient(busy.http, busy.http).refresh('outages', signal()),
    (error: unknown) => error instanceof DiaryError && error.status === 409 &&
      error.code === 'SOURCE_BUSY',
  );
  const conflict = mockHttp({ detail: 'conflict', code: 'VERSION_CONFLICT' }, 409);
  await assert.rejects(
    new AdminClient(conflict.http, conflict.http).setInterval('outages', 900, 1, signal()),
    (error: unknown) => error instanceof DiaryError && error.status === 409 &&
      error.code === 'VERSION_CONFLICT',
  );
});

test('422 and malformed payloads are rejected', async () => {
  const invalid = mockHttp({ detail: 'invalid' }, 422);
  await assert.rejects(
    new AdminClient(invalid.http, invalid.http).setInterval('outages', 900, 1, signal()),
    (error: unknown) => error instanceof DiaryError && error.status === 422,
  );
  const incomplete = { sources: [sources.sources[0]] };
  await assert.rejects(
    new AdminClient(mockHttp(incomplete).http, mockHttp(incomplete).http).sources(signal()),
    DiaryError,
  );
  const badInterval = {
    ...sources,
    sources: [{ ...sources.sources[0], interval_seconds: 301 }, sources.sources[1]],
  };
  await assert.rejects(
    new AdminClient(mockHttp(badInterval).http, mockHttp(badInterval).http).sources(signal()),
    DiaryError,
  );
  await assert.rejects(
    new AdminClient(mockHttp(sources, 200, 'text/html').http, mockHttp(sources).http)
      .sources(signal()),
    DiaryError,
  );
});
