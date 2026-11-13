import assert from 'node:assert/strict';
import test from 'node:test';
import { DiaryClient, DiaryError, isCut, isSession, isSummary } from '../src/diaryApi.ts';
import { RequestScope, buenosAiresMinute, defaultPeriod, minuteInput } from '../src/diaryState.ts';
import { mockHttp } from './httpSupport.ts';

const cut = { id: 'cut', domicile_id: 'home', start_at: '2026-11-01T10:00:00-03:00', end_at: null, observations: null, complaint_number: null, version: 1, status: 'ongoing' };

test('validates private DTOs without unchecked casts', () => {
  assert.equal(isCut(cut), true);
  assert.equal(isCut({ ...cut, version: 0 }), false);
  assert.equal(isCut({ ...cut, status: 'closed' }), false);
  assert.equal(isCut({ ...cut, start_at: 'bad' }), false);
  assert.equal(isSession({ account: { id: 'a', username: 'name' }, csrf_token: 'token' }), true);
  assert.equal(isSession({ account: { id: 'a', username: 'name', role: 'admin' }, csrf_token: 'token' }), true);
  assert.equal(isSession({ account: { id: 'a', username: 'name', role: 'user' }, csrf_token: 'token' }), true);
  assert.equal(isSession({ account: { id: 'a', username: 'name', role: 'root' }, csrf_token: 'token' }), false);
  assert.equal(isSession({ account: { id: 'a' }, csrf_token: 'token' }), false);
  assert.equal(isSummary({}), false);
});

test('calendar inputs use Buenos Aires rather than host time', () => {
  assert.equal(buenosAiresMinute(new Date('2026-11-02T02:30:00Z')), '2026-11-01T23:30');
  assert.deepEqual(defaultPeriod(new Date('2026-11-02T02:30:00Z')), { period_start: '2026-11-01T00:00', period_end: '2026-11-02T00:00' });
  assert.equal(minuteInput('2026-11-01T10:05:00-03:00'), '2026-11-01T10:05');
});

test('request scope invalidates stale lanes and all account data requests', () => {
  const scope = new RequestScope();
  const first = scope.begin('cuts');
  const second = scope.begin('cuts');
  assert.equal(first.isCurrent(), false);
  assert.equal(second.isCurrent(), true);
  scope.invalidate();
  assert.equal(second.isCurrent(), false);
});

test('client sends session cookies and CSRF but never trusts caller ownership', async () => {
  const { http } = mockHttp({ id: 'home', display_address: 'Synthetic address' }, 201, 'application/json', config => {
    assert.equal(config.url, '/api/domiciles');
    assert.equal(config.withCredentials, true);
    assert.equal(config.headers.get('X-CSRF-Token'), 'current-csrf');
    assert.equal(config.data, JSON.stringify({ display_address: 'Synthetic address' }));
  });
  const client = new DiaryClient(http);
  assert.equal((await client.createDomicile('Synthetic address', 'stale-caller-token', new AbortController().signal)).id, 'home');
});

test('client rejects a mismatched domicile response', async () => {
  const client = new DiaryClient(mockHttp([cut]).http);
  await assert.rejects(client.cuts('another-home', new AbortController().signal), DiaryError);
});

test('client validates typed session responses through the shared transport', async () => {
  const client = new DiaryClient(mockHttp({ account: { id: 'a', username: 'synthetic' }, csrf_token: 'csrf' }).http);
  assert.equal((await client.session(new AbortController().signal)).account.id, 'a');
  await assert.rejects(new DiaryClient(mockHttp({ account: {} }).http).session(new AbortController().signal), DiaryError);
});

test('conflict error preserves retry guidance and network failures are safe', async () => {
  const conflict = new DiaryClient(mockHttp({ detail: 'Conflicto' }, 409).http);
  await assert.rejects(conflict.domiciles(new AbortController().signal), /Descartar borrador y recargar/);
  const failed = new DiaryClient(mockHttp({ detail: 'Temporalmente no disponible' }, 503).http);
  await assert.rejects(failed.domiciles(new AbortController().signal), /Temporalmente no disponible/);
});
