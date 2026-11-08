import assert from 'node:assert/strict';
import test from 'node:test';
import { DomicilesClient } from '../src/features/domiciles/api.ts';
import { DiaryError } from '../src/lib/httpError.ts';
import { mockHttp } from './httpSupport.ts';
import { RequestScope } from '../src/diaryState.ts';

const signal = () => new AbortController().signal;
const meter = { id: 'm', domicile_id: 'd', meter_number: '001-A', alias: null, version: 1 };

test('CU04 adapter sends the six specified routes and correction versions', async () => {
  const cases = [
    { data: { id: 'd', display_address: 'Example', version: 1 }, status: 200, method: 'get', url: '/api/domiciles/d/management', run: (client: DomicilesClient) => client.management('d', signal()) },
    { data: { id: 'd', display_address: 'New', version: 2 }, status: 200, method: 'patch', url: '/api/domiciles/d', run: (client: DomicilesClient) => client.correctDomicile({ id: 'd', display_address: 'Example', version: 1 }, 'New', signal()) },
    { data: [meter], status: 200, method: 'get', url: '/api/domiciles/d/meters', run: (client: DomicilesClient) => client.meters('d', signal()) },
    { data: meter, status: 201, method: 'post', url: '/api/domiciles/d/meters', run: (client: DomicilesClient) => client.createMeter('d', { meter_number: '001-A', alias: null }, signal()) },
    { data: meter, status: 200, method: 'get', url: '/api/domiciles/d/meters/m', run: (client: DomicilesClient) => client.meter('d', 'm', signal()) },
    { data: { ...meter, version: 2 }, status: 200, method: 'patch', url: '/api/domiciles/d/meters/m', run: (client: DomicilesClient) => client.correctMeter(meter, { meter_number: '001-A', alias: null }, signal()) },
  ];
  for (const item of cases) {
    const { http } = mockHttp(item.data, item.status, 'application/json', config => {
      assert.equal(config.url, item.url); assert.equal(config.method, item.method);
      if (item.method === 'patch') assert.equal(JSON.parse(config.data).version, 1);
    });
    await item.run(new DomicilesClient(http));
  }
});

test('CU04 rejects invalid DTOs, wrong identities, version and MIME', async () => {
  for (const data of [{ ...meter, domicile_id: 'other' }, { ...meter, id: 'other' }, { ...meter, version: 0 }, { ...meter, alias: 2 }]) {
    await assert.rejects(new DomicilesClient(mockHttp(data).http).meter('d', 'm', signal()), error => error instanceof DiaryError && error.kind === 'invalid-response');
  }
  await assert.rejects(new DomicilesClient(mockHttp([meter, { ...meter, domicile_id: 'other' }]).http).meters('d', signal()), DiaryError);
  await assert.rejects(new DomicilesClient(mockHttp(meter, 200, 'text/plain').http).meter('d', 'm', signal()), DiaryError);
  await assert.rejects(new DomicilesClient(mockHttp(meter).http).correctMeter(meter, { meter_number: '001-A', alias: null }, signal()), DiaryError);
});

test('conflict code is validated without diary-specific transport advice', async () => {
  for (const code of ['DUPLICATE_METER', 'VERSION_CONFLICT', 'unexpected']) {
    const { http } = mockHttp({ detail: 'Conflict', code }, 409);
    await assert.rejects(new DomicilesClient(http).createMeter('d', { meter_number: '001', alias: null }, signal()), error => {
      assert.ok(error instanceof DiaryError);
      assert.equal(error.code, code === 'unexpected' ? null : code);
      assert.doesNotMatch(error.message, /Descartar borrador/);
      return true;
    });
  }
});

test('selection scope invalidation prevents an older domicile response from being accepted', async () => {
  const scope = new RequestScope();
  const old = scope.begin('management');
  let finish: (value: string) => void = () => { throw new Error('not initialized'); };
  const pending = new Promise<string>(resolve => { finish = resolve; });
  const accepted: string[] = [];
  const oldResult = pending.then(value => { if (old.isCurrent()) accepted.push(value); });
  const current = scope.begin('management');
  assert.equal(old.signal.aborted, true);
  if (current.isCurrent()) accepted.push('new selection');
  finish('old selection');
  await oldResult;
  assert.deepEqual(accepted, ['new selection']);
  scope.invalidate();
  assert.equal(current.isCurrent(), false);
});
