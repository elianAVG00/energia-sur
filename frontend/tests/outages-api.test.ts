import assert from 'node:assert/strict';
import test from 'node:test';
import { OutagesClient } from '../src/features/outages/api.ts';
import { DiaryError } from '../src/lib/httpError.ts';
import { mockHttp } from './httpSupport.ts';

const signal = () => new AbortController().signal;

const areas = {
  coverage_version: '2026-11-10',
  coverage_retrieved_on: '2026-11-10',
  areas: [
    { partido: 'LOMAS DE ZAMORA', localidades: [
      { localidad: 'BANFIELD', coverage: 'coverage_unverified', reported: true },
      { localidad: null, coverage: 'coverage_unverified', reported: false },
    ] },
  ],
};

const outages = {
  state: 'reported',
  source_status: 'ok',
  freshness: 'fresh',
  granularity: 'localidad',
  source: 'ENRE',
  source_url: 'https://www.enre.gov.ar/paginacorte/js/data_EDS.js',
  fetched_at: '2026-11-10T04:53:49Z',
  source_updated_at: '2026-11-10T04:53:00Z',
  source_reported_time: '1:50',
  coverage: { partido: 'LOMAS DE ZAMORA', localidad: 'BANFIELD', status: 'coverage_unverified' },
  totals_scope: 'edesur',
  total_users_without: 7198,
  total_users_with: 2819686,
  users_affected_yesterday: 1580,
  outages: [{
    category: 'medium_voltage', partido: 'LOMAS DE ZAMORA', localidad: 'BANFIELD',
    subestacion_alimentador: '87-ESCALADA', affected_users: 120, normalizacion: '11:00',
  }],
};

test('areas uses the public catalog endpoint and validates coverage', async () => {
  const { http } = mockHttp(areas, 200, 'application/json', config => {
    assert.equal(config.url, '/api/outages/areas');
    assert.equal(config.method, 'get');
  });
  const result = await new OutagesClient(http).areas(signal());
  assert.equal(result.coverage_version, '2026-11-10');
  assert.equal(result.areas[0]?.localidades[0]?.coverage, 'coverage_unverified');
});

test('query builds an encoded partido/localidad request and validates rows', async () => {
  const { http } = mockHttp(outages, 200, 'application/json', config => {
    assert.equal(config.url, '/api/outages?partido=LOMAS+DE+ZAMORA&localidad=BANFIELD');
  });
  const result = await new OutagesClient(http).query('LOMAS DE ZAMORA', 'BANFIELD', signal());
  assert.equal(result.state, 'reported');
  assert.equal(result.outages?.[0]?.category, 'medium_voltage');
});

test('query without localidad omits the parameter and accepts a no-reports payload', async () => {
  const noReports = { ...outages, state: 'no_reports', granularity: 'partido', outages: [] };
  const { http } = mockHttp(noReports, 200, 'application/json', config => {
    assert.equal(config.url, '/api/outages?partido=LOMAS+DE+ZAMORA');
  });
  const result = await new OutagesClient(http).query('LOMAS DE ZAMORA', '', signal());
  assert.equal(result.state, 'no_reports');
  assert.deepEqual(result.outages, []);
});

test('resolve posts address and hints in the body with no query string', async () => {
  const body = { status: 'resolved', zone: { partido: 'QUILMES', localidad: 'QUILMES', granularity: 'localidad', coverage: 'covered' } };
  const { http } = mockHttp(body, 200, 'application/json', config => {
    assert.equal(config.url, '/api/outages/resolve');
    assert.equal(config.method, 'post');
    assert.equal(config.url?.includes('?'), false);
    assert.deepEqual(JSON.parse(String(config.data)), { address: 'calchaqui 100', partido: 'Quilmes' });
  });
  const result = await new OutagesClient(http).resolve('calchaqui 100', { partido: 'Quilmes' }, signal());
  assert.equal(result.status, 'resolved');
});

test('resolve accepts candidates and resolve-location sends coordinates in the body', async () => {
  const candidates = {
    status: 'candidates',
    candidates: [
      { partido: 'LA MATANZA', localidad: 'LA MATANZA', granularity: 'partido', coverage: 'coverage_unverified' },
      { partido: 'QUILMES', localidad: 'QUILMES', granularity: 'localidad', coverage: 'covered' },
    ],
  };
  const first = mockHttp(candidates, 200, 'application/json');
  const result = await new OutagesClient(first.http).resolve('calchaqui 100', {}, signal());
  assert.equal(result.status, 'candidates');

  const resolved = { status: 'resolved', zone: { partido: 'LOMAS DE ZAMORA', localidad: null, granularity: 'partido', coverage: 'coverage_unverified' } };
  const { http } = mockHttp(resolved, 200, 'application/json', config => {
    assert.equal(config.url, '/api/outages/resolve-location');
    assert.deepEqual(JSON.parse(String(config.data)), { lat: -34.76, lon: -58.4 });
  });
  const zone = await new OutagesClient(http).resolveLocation(-34.76, -58.4, signal());
  assert.equal(zone.status, 'resolved');
});

test('accepts the real exclude_none shape with omitted nested nullable fields', async () => {
  const compact = {
    ...outages,
    coverage: { partido: 'ALMIRANTE BROWN', status: 'coverage_unverified' },
    outages: [{ category: 'low_voltage', partido: 'ALMIRANTE BROWN', localidad: 'SAN JOSE' }],
  };
  const { http } = mockHttp(compact);
  const result = await new OutagesClient(http).query('ALMIRANTE BROWN', '', signal());
  assert.equal(result.state, 'reported');
  assert.equal(result.coverage.localidad, undefined);
  assert.equal(result.outages?.[0]?.subestacion_alimentador, undefined);
  assert.equal(result.outages?.[0]?.affected_users, undefined);

  const resolvedPayload = {
    status: 'resolved',
    zone: { partido: 'LOMAS DE ZAMORA', granularity: 'partido', coverage: 'coverage_unverified' },
  };
  const resolved = await new OutagesClient(mockHttp(resolvedPayload).http).resolve('calle 1', {}, signal());
  assert.equal(resolved.status, 'resolved');
});

test('malformed payloads and non-JSON responses are rejected', async () => {  const invalid = { ...outages, state: 'invented_state' };
  await assert.rejects(new OutagesClient(mockHttp(invalid).http).query('A', '', signal()), DiaryError);
  const emptyCandidates = { status: 'candidates', candidates: [] };
  await assert.rejects(new OutagesClient(mockHttp(emptyCandidates).http).resolve('x', {}, signal()), DiaryError);
  const badCoverage = { ...outages, coverage: { ...outages.coverage, status: 'unknown' } };
  await assert.rejects(new OutagesClient(mockHttp(badCoverage).http).query('A', '', signal()), DiaryError);
  await assert.rejects(new OutagesClient(mockHttp(outages, 200, 'text/html').http).query('A', '', signal()), DiaryError);
});
