import assert from 'node:assert/strict';
import test from 'node:test';
import { AxiosError, AxiosHeaders } from 'axios';
import type { AxiosAdapter, AxiosResponse } from 'axios';
import { createHttpClient } from '../src/lib/http.ts';
import { DiaryClient, DiaryError } from '../src/diaryApi.ts';
import { createSessionStore } from '../src/stores/session.ts';
import { mockHttp, session } from './httpSupport.ts';

const signal = () => new AbortController().signal;

test('session factories are isolated and reset selected domicile on account lifecycle', () => {
  const first = createSessionStore();
  const second = createSessionStore();
  first.getState().setSession(session);
  first.getState().selectDomicile('home-a');
  assert.equal(first.getState().selectedDomicileId, 'home-a');
  assert.equal(second.getState().session, null);
  const generation = first.getState().generation;
  first.getState().setSession({ ...session, account: { id: 'b', username: 'second' } });
  assert.equal(first.getState().selectedDomicileId, '');
  assert.equal(first.getState().clearSession(generation, true), false);
  assert.equal(first.getState().setSession(session, generation), false);
  assert.equal(first.getState().session?.account.id, 'b');
  first.getState().clearSession();
  assert.equal(first.getState().session, null);
  first.getState().selectDomicile('cannot-select-without-session');
  assert.equal(first.getState().selectedDomicileId, '');
  assert.equal('password' in first.getState(), false);
  assert.equal('persist' in first, false);
});

test('interceptors send cookie credentials, current CSRF on writes, none on login/GET and no forged Origin', async () => {
  const seen: string[] = [];
  const { http, store } = mockHttp({}, 200, 'application/json', config => {
    assert.equal(config.withCredentials, true);
    assert.equal(config.withXSRFToken, false);
    assert.equal(config.headers.has('Origin'), false);
    assert.equal(config.headers.has('Authorization'), false);
    const needsToken = config.method !== 'get' && config.url !== '/api/login';
    assert.equal(config.headers.get('X-CSRF-Token') ?? undefined, needsToken ? 'rotated' : undefined);
    seen.push(config.url ?? '');
  });
  store.getState().setSession({ ...session, csrf_token: 'rotated' });
  await http.request('/session', signal());
  await http.request('/login', signal(), { method: 'POST', data: { username: 'synthetic', password: 'not-logged' } });
  for (const [path, method] of [['/domiciles', 'POST'], ['/domiciles/d/interruptions', 'POST'], ['/interruptions/i', 'PATCH'], ['/interruptions/i/close', 'POST'], ['/logout', 'POST']] as const) {
    await http.request(path, signal(), { method });
  }
  assert.equal(seen.length, 7);
});

test('external and normalized traversal destinations never dispatch or receive tokens', async () => {
  let calls = 0;
  const { http } = mockHttp({}, 200, 'application/json', () => { calls++; });
  for (const path of ['https://evil.invalid/a', '//evil.invalid/a', '/\\evil.invalid/a', '/../login', '/a/../../login', '/%2e%2e/login', '/a/%2E%2E/login', '/%252e%252e/login', '/%2f%2fevil.invalid', '/a#fragment', '/a\n']) {
    await assert.rejects(http.request(path, signal(), { method: 'POST' }), DiaryError);
  }
  assert.equal(calls, 0);
  await http.request('/domiciles/d/summary?period_start=2026-11-01T00%3A00', signal());
  assert.equal(calls, 1);
});

test('missing session CSRF fails locally, while captured logout token works after local clear', async () => {
  let calls = 0;
  const { http, store } = mockHttp(null, 204, 'application/json', config => {
    calls++;
    assert.equal(config.headers.get('X-CSRF-Token'), 'current-csrf');
  });
  const csrf = store.getState().session?.csrf_token;
  assert.ok(csrf);
  store.getState().clearSession();
  await assert.rejects(http.request('/domiciles', signal(), { method: 'POST' }), error => error instanceof DiaryError && error.status === 403);
  assert.equal(calls, 0);
  await new DiaryClient(http).logout(csrf, signal());
  assert.equal(calls, 1);
});

test('status-aware errors never replay mutations and expire only current authenticated sessions', async () => {
  for (const status of [401, 403, 404, 409, 422, 503]) {
    let calls = 0;
    const { http, store } = mockHttp({ detail: 'Safe server detail' }, status, 'application/json', () => { calls++; });
    await assert.rejects(http.request('/domiciles', signal(), { method: 'POST' }), error => {
      assert.ok(error instanceof DiaryError);
      assert.equal(error.status, status);
      assert.ok(error.message.includes('Safe server detail'));
      if (status === 409) assert.doesNotMatch(error.message, /Descartar borrador/);
      return true;
    });
    assert.equal(calls, 1);
    assert.equal(store.getState().session === null, status === 401);
    assert.equal(store.getState().expired, status === 401);
  }
});

for (const status of [200, 401]) {
  test(`late old-session ${status} cannot install data or clear newer session`, async () => {
    const store = createSessionStore();
    store.getState().setSession(session);
    let begin: () => void = () => { throw new Error('not initialized'); };
    const started = new Promise<void>(resolve => { begin = resolve; });
    let finish: () => void = () => { throw new Error('not initialized'); };
    const wait = new Promise<void>(resolve => { finish = resolve; });
    const adapter: AxiosAdapter = async config => {
      begin(); await wait;
      return { data: {}, status, statusText: String(status), headers: new AxiosHeaders(), config };
    };
    const http = createHttpClient({ store, adapter });
    const pending = http.request('/session', signal());
    await started;
    store.getState().setSession({ ...session, account: { id: 'new', username: 'new' } });
    finish();
    await assert.rejects(pending, error => error instanceof DiaryError && error.kind === 'aborted');
    assert.equal(store.getState().session?.account.id, 'new');
  });
}

test('cancellation, timeout and network failures are typed and omit raw credential-bearing configs', async () => {
  const store = createSessionStore();
  for (const code of ['ECONNABORTED', 'ETIMEDOUT', 'ERR_NETWORK']) {
    const adapter: AxiosAdapter = async config => { throw new AxiosError('PRIVATE-PASSWORD', code, config); };
    const http = createHttpClient({ store, adapter });
    await assert.rejects(http.request('/login', signal(), { method: 'POST', data: { password: 'PRIVATE-PASSWORD' } }), error => {
      assert.ok(error instanceof DiaryError);
      assert.equal(error.kind, code === 'ERR_NETWORK' ? 'network' : 'timeout');
      assert.doesNotMatch(JSON.stringify(error), /PRIVATE-PASSWORD/);
      assert.equal('config' in error, false);
      assert.equal('cause' in error, false);
      return true;
    });
  }
  const canceled = new AbortController();
  canceled.abort();
  await assert.rejects(mockHttp({}).http.request('/session', canceled.signal), error => error instanceof DiaryError && error.kind === 'aborted');
});

test('PDF success, JSON blob errors, empty or non-PDF responses are validated', async () => {
  const period = { period_start: '2026-11-01T00:00', period_end: '2026-11-02T00:00' };
  const pdf = new Blob(['%PDF-synthetic'], { type: 'application/pdf' });
  assert.equal((await new DiaryClient(mockHttp(pdf, 200, 'application/pdf').http).pdf('d', period, signal())).size, pdf.size);
  for (const [data, type] of [[new Blob(), 'application/pdf'], [new Blob(['{}']), 'application/json'], [{}, 'application/pdf']] as const) {
    await assert.rejects(new DiaryClient(mockHttp(data, 200, type).http).pdf('d', period, signal()), error => error instanceof DiaryError && error.kind === 'invalid-response');
  }
  const errorBlob = new Blob([JSON.stringify({ detail: 'Safe PDF failure' })], { type: 'application/json' });
  await assert.rejects(new DiaryClient(mockHttp(errorBlob, 503, 'application/json').http).pdf('d', period, signal()), /Safe PDF failure/);
  await assert.rejects(new DiaryClient(mockHttp(new Blob(['{'.repeat(9000)]), 503, 'application/json').http).pdf('d', period, signal()), /temporalmente/);
});

test('failed or canceled PDF never produces a successful blob', async () => {
  const store = createSessionStore();
  const controller = new AbortController();
  const adapter: AxiosAdapter = async config => {
    controller.abort();
    const response: AxiosResponse<unknown> = { data: new Blob(['%PDF']), status: 200, statusText: 'OK', headers: new AxiosHeaders({ 'content-type': 'application/pdf' }), config };
    return response;
  };
  await assert.rejects(new DiaryClient(createHttpClient({ store, adapter })).pdf('d', { period_start: 'a', period_end: 'b' }, controller.signal), error => error instanceof DiaryError && error.kind === 'aborted');
});

test('deadline bounds deferred PDF JSON error decoding and remains a timeout', async () => {
  const deadline = new AbortController();
  let started: () => void = () => { throw new Error('not initialized'); };
  const reading = new Promise<void>(resolve => { started = resolve; });
  class DeferredErrorBlob extends Blob {
    override text(): Promise<string> {
      started();
      return new Promise(() => { /* Deadline must settle the request, not this body. */ });
    }
  }
  const adapter: AxiosAdapter = async config => ({
    data: new DeferredErrorBlob(['{}']), status: 503, statusText: 'Unavailable',
    headers: new AxiosHeaders({ 'content-type': 'application/json' }), config,
  });
  const http = createHttpClient({ store: createSessionStore(), adapter, deadlineSignal: () => deadline.signal });
  const pending = http.request('/domiciles/d/report.pdf', signal(), { responseType: 'blob' });
  await reading;
  deadline.abort();
  await assert.rejects(pending, error => error instanceof DiaryError && error.kind === 'timeout');
});

test('generation change during PDF JSON decoding cannot expire a new login', async () => {
  const store = createSessionStore(); store.getState().setSession(session);
  let begin: () => void = () => { throw new Error('not initialized'); };
  const started = new Promise<void>(resolve => { begin = resolve; });
  let finish: (text: string) => void = () => { throw new Error('not initialized'); };
  class DeferredErrorBlob extends Blob {
    override text(): Promise<string> { begin(); return new Promise(resolve => { finish = resolve; }); }
  }
  const adapter: AxiosAdapter = async config => ({
    data: new DeferredErrorBlob(['{}']), status: 401, statusText: 'Unauthorized',
    headers: new AxiosHeaders({ 'content-type': 'application/json' }), config,
  });
  const pending = createHttpClient({ store, adapter }).request('/domiciles/d/report.pdf', signal(), { responseType: 'blob' });
  await started;
  store.getState().setSession({ ...session, account: { id: 'new', username: 'new' } });
  finish('{"detail":"Expired old session"}');
  await assert.rejects(pending, error => error instanceof DiaryError && error.kind === 'aborted');
  assert.equal(store.getState().session?.account.id, 'new');
});
