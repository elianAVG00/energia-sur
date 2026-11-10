import assert from 'node:assert/strict';
import test from 'node:test';
import { ScheduledWorksClient } from '../src/features/scheduled-works/api.ts';
import { mockHttp } from './httpSupport.ts';

const signal = () => new AbortController().signal;

const areas = {
  coverage_version: '2026-11-10',
  coverage_retrieved_on: '2026-11-10',
  areas: [
    { partido: 'ALMIRANTE BROWN', localidades: [
      { localidad: 'GLEW', coverage: 'covered', reported: true },
      { localidad: null, coverage: 'coverage_unverified', reported: false },
    ] },
  ],
};

const works = {
  state: 'works_reported',
  source_status: 'ok',
  freshness: 'fresh',
  granularity: 'localidad',
  source: 'ENRE',
  source_url: 'https://www.enre.gov.ar/paginacorte/js/data_EDS.js',
  fetched_at: '2026-11-10T14:08:04Z',
  source_updated_at: '2026-11-10T14:06:50Z',
  source_reported_time: '11:05',
  coverage: { partido: 'ALMIRANTE BROWN', localidad: 'GLEW', status: 'covered' },
  limitations: ['dates_not_published', 'reason_not_published', 'proximity_not_available'],
  works: [{
    category: 'maintenance', partido: 'ALMIRANTE BROWN', localidad: 'GLEW',
    subestacion_alimentador: '277-GLEW', affected_users: 2742,
    restoration_estimate_text: 'Sin datos', reason_text: null,
    planned_start_at: null, planned_end_at: null,
  }],
};

test('areas uses the scheduled-works catalog endpoint', async () => {
  const { http } = mockHttp(areas, 200, 'application/json', config => {
    assert.equal(config.url, '/api/scheduled-works/areas');
    assert.equal(config.method, 'get');
  });
  const result = await new ScheduledWorksClient(http).areas(signal());
  assert.equal(result.coverage_version, '2026-11-10');
  assert.equal(result.areas[0]?.localidades[0]?.reported, true);
});

test('query builds an encoded request and validates nullable unpublished fields', async () => {
  const { http } = mockHttp(works, 200, 'application/json', config => {
    assert.equal(config.url, '/api/scheduled-works?partido=ALMIRANTE+BROWN&localidad=GLEW');
  });
  const result = await new ScheduledWorksClient(http).query('ALMIRANTE BROWN', 'GLEW', signal());
  assert.equal(result.state, 'works_reported');
  assert.equal(result.works?.[0]?.planned_start_at, null);
  assert.equal(result.works?.[0]?.reason_text, null);
  assert.equal(result.works?.[0]?.restoration_estimate_text, 'Sin datos');
});

test('query without localidad omits the parameter and accepts an empty list', async () => {
  const noWorks = { ...works, state: 'no_works', granularity: 'partido', works: [] };
  const { http } = mockHttp(noWorks, 200, 'application/json', config => {
    assert.equal(config.url, '/api/scheduled-works?partido=ALMIRANTE+BROWN');
  });
  const result = await new ScheduledWorksClient(http).query('ALMIRANTE BROWN', '', signal());
  assert.equal(result.state, 'no_works');
  assert.deepEqual(result.works, []);
});

test('query accepts omitted works for unverified coverage', async () => {
  const unverified = { ...works, state: 'coverage_unverified', works: undefined };
  const { http } = mockHttp(unverified, 200, 'application/json');
  const result = await new ScheduledWorksClient(http).query('CAPITAL', '', signal());
  assert.equal(result.state, 'coverage_unverified');
  assert.equal(result.works, undefined);
});

test('a fabricated category or a missing limitation is rejected', async () => {
  const badCategory = {
    ...works,
    works: [{ ...works.works[0], category: 'preventive' }],
  };
  const first = mockHttp(badCategory, 200, 'application/json');
  await assert.rejects(new ScheduledWorksClient(first.http).query('X', '', signal()));

  const badLimitations = { ...works, limitations: ['invented_limitation'] };
  const second = mockHttp(badLimitations, 200, 'application/json');
  await assert.rejects(new ScheduledWorksClient(second.http).query('X', '', signal()));
});

test('resolve reuses the public address endpoint with a body and no query string', async () => {
  const body = {
    status: 'resolved',
    zone: { partido: 'ALMIRANTE BROWN', localidad: 'GLEW', granularity: 'localidad', coverage: 'covered' },
  };
  const { http } = mockHttp(body, 200, 'application/json', config => {
    assert.equal(config.url, '/api/outages/resolve');
    assert.equal(config.method, 'post');
    assert.equal(config.url?.includes('?'), false);
    assert.deepEqual(JSON.parse(String(config.data)), { address: 'calchaqui 100', partido: 'Almirante Brown' });
  });
  const result = await new ScheduledWorksClient(http).resolve('calchaqui 100', { partido: 'Almirante Brown' }, signal());
  assert.equal(result.status, 'resolved');
});

test('resolveLocation reuses the public coordinates endpoint', async () => {
  const body = {
    status: 'resolved',
    zone: { partido: 'ALMIRANTE BROWN', localidad: null, granularity: 'partido', coverage: 'covered' },
  };
  const { http } = mockHttp(body, 200, 'application/json', config => {
    assert.equal(config.url, '/api/outages/resolve-location');
    assert.deepEqual(JSON.parse(String(config.data)), { lat: -34.7, lon: -58.4 });
  });
  const result = await new ScheduledWorksClient(http).resolveLocation(-34.7, -58.4, signal());
  assert.equal(result.status, 'resolved');
});
