import { expect, test } from '@playwright/test';
import type { Page, Route } from '@playwright/test';

const AREAS = {
  coverage_version: '2026-11-10',
  coverage_retrieved_on: '2026-11-10',
  areas: [
    { partido: 'LOMAS DE ZAMORA', localidades: [
      { localidad: 'BANFIELD', coverage: 'coverage_unverified', reported: true },
    ] },
    { partido: 'SAN VICENTE', localidades: [] },
    { partido: 'CAPITAL', localidades: [] },
  ],
};

const RESOLVED_LOMAS = {
  status: 'resolved',
  zone: { partido: 'LOMAS DE ZAMORA', localidad: null, granularity: 'partido', coverage: 'coverage_unverified' },
};

const CANDIDATES = {
  status: 'candidates',
  candidates: [
    { partido: 'LA MATANZA', localidad: 'LA MATANZA', granularity: 'partido', coverage: 'coverage_unverified' },
    { partido: 'QUILMES', localidad: 'QUILMES', granularity: 'localidad', coverage: 'covered' },
  ],
};

function result(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
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
    ...overrides,
  };
}

interface MockOptions {
  authenticated?: boolean;
  rateLimited?: boolean;
  resolve?: unknown;
  location?: unknown;
  byPartido?: Record<string, Record<string, unknown>>;
  onResolve?: (body: unknown, headers: Record<string, string>) => void;
}

async function openPublic(page: Page): Promise<void> {
  await page.goto('/');
  await page.getByRole('button', { name: 'Cortes' }).click();
}

async function mockApi(page: Page, options: MockOptions = {}): Promise<void> {
  await page.route('**/api/**', async (route: Route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.pathname === '/api/session') {
      if (options.authenticated) {
        await route.fulfill({ status: 200, json: {
          account: { id: 'synthetic', username: 'qa-synthetic' }, csrf_token: 'synthetic-csrf',
        } });
      } else {
        await route.fulfill({ status: 401, json: { detail: 'Sin sesión' } });
      }
      return;
    }
    if (url.pathname === '/api/health') {
      await route.fulfill({ status: 200, json: { status: 'ok' } });
      return;
    }
    if (url.pathname === '/api/domiciles') {
      await route.fulfill({ status: 200, json: [] });
      return;
    }
    if (url.pathname === '/api/outages/areas') {
      await route.fulfill({ status: 200, json: AREAS });
      return;
    }
    if (url.pathname === '/api/outages') {
      const partido = url.searchParams.get('partido') ?? '';
      await route.fulfill({ status: 200, json: options.byPartido?.[partido] ?? result() });
      return;
    }
    if (url.pathname === '/api/outages/resolve') {
      if (options.rateLimited) {
        await route.fulfill({ status: 429, headers: { 'retry-after': '30' },
          json: { detail: 'Demasiadas solicitudes.' } });
        return;
      }
      options.onResolve?.(
        request.postDataJSON() as unknown,
        request.headers() as Record<string, string>,
      );
      await route.fulfill({ status: 200, json: options.resolve ?? RESOLVED_LOMAS });
      return;
    }
    if (url.pathname === '/api/outages/resolve-location') {
      await route.fulfill({ status: 200, json: options.location ?? RESOLVED_LOMAS });
      return;
    }
    await route.fulfill({ status: 404, json: { detail: 'not mocked' } });
  });
}

test('visitor queries reported outages without a session and without direct ENRE access', async ({ page }) => {
  const external: string[] = [];
  page.on('request', request => {
    if (/enre\.gov\.ar|datos\.gob\.ar/.test(request.url())) external.push(request.url());
  });
  await mockApi(page);
  await openPublic(page);
  await expect(page.getByRole('heading', { name: 'Cortes eléctricos' })).toBeVisible();
  await page.getByLabel('Partido', { exact: true }).selectOption('LOMAS DE ZAMORA');
  await page.getByLabel('Localidad (opcional)', { exact: true }).selectOption('BANFIELD');
  await page.getByRole('button', { name: 'Consultar cortes' }).click();
  await expect(page.getByRole('heading', { name: 'Cortes reportados' })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Media tensión' })).toBeVisible();
  await expect(page.getByText('Total Edesur (todos los partidos, no la zona consultada)')).toBeVisible();
  await expect(page.getByText('10/11/2026 01:53').first()).toBeVisible();
  await expect(page.getByRole('link', { name: 'ENRE' }))
    .toHaveAttribute('href', 'https://www.enre.gov.ar/paginacorte/js/data_EDS.js');
  expect(external).toEqual([]);
});

test('ambiguous address shows candidates and posts the address without CSRF', async ({ page }) => {
  let body: unknown;
  let csrf: string | undefined;
  await mockApi(page, {
    resolve: CANDIDATES,
    onResolve: (value, headers) => { body = value; csrf = headers['x-csrf-token']; },
  });
  await openPublic(page);
  await page.getByLabel('Dirección (calle y altura)', { exact: true }).fill('calchaqui 100');
  await page.getByRole('button', { name: 'Buscar dirección' }).click();
  await expect(page.getByText('La dirección es ambigua. Elegí una de las zonas encontradas.')).toBeVisible();
  await page.getByRole('button', { name: /QUILMES · QUILMES/ }).click();
  await expect(page.getByRole('heading', { name: 'Cortes reportados' })).toBeVisible();
  expect(body).toEqual({ address: 'calchaqui 100' });
  expect(csrf).toBeUndefined();
});

test('consented browser location resolves a partido and degrades the search', async ({ page, context }) => {
  await context.grantPermissions(['geolocation']);
  await context.setGeolocation({ latitude: -34.76, longitude: -58.4 });
  await mockApi(page, { location: RESOLVED_LOMAS });
  await openPublic(page);
  await page.getByRole('button', { name: 'Usar mi ubicación' }).click();
  await expect(page.getByText('Búsqueda limitada al partido LOMAS DE ZAMORA: no se pudo determinar una localidad confiable.')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Cortes reportados' })).toBeVisible();
});

test('stale, unverified coverage and unavailable source are distinct states', async ({ page }) => {
  const unverified = result({
    state: 'coverage_unverified',
    coverage: { partido: 'SAN VICENTE', localidad: null, status: 'coverage_unverified' },
    outages: undefined,
  });
  const unavailable = result({
    state: 'unavailable',
    freshness: 'unavailable',
    coverage: { partido: 'CAPITAL', localidad: null, status: 'coverage_unverified' },
    outages: undefined,
  });
  await mockApi(page, { byPartido: {
    'LOMAS DE ZAMORA': result({ state: 'stale', freshness: 'stale' }),
    'SAN VICENTE': unverified,
    'CAPITAL': unavailable,
  } });
  await openPublic(page);

  await page.getByLabel('Partido', { exact: true }).selectOption('LOMAS DE ZAMORA');
  await page.getByRole('button', { name: 'Consultar cortes' }).click();
  await expect(page.getByRole('heading', { name: 'Información desactualizada' })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Media tensión' })).toBeVisible();

  await page.getByLabel('Partido', { exact: true }).selectOption('SAN VICENTE');
  await page.getByRole('button', { name: 'Consultar cortes' }).click();
  await expect(page.getByRole('heading', { name: 'Cobertura no verificada' })).toBeVisible();
  await expect(page.getByText('No podemos confirmar si hay cortes ni afirmar que no los hay.')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Sin cortes reportados' })).toHaveCount(0);

  await page.getByLabel('Partido', { exact: true }).selectOption('CAPITAL');
  await page.getByRole('button', { name: 'Consultar cortes' }).click();
  await expect(page.getByRole('heading', { name: 'Fuente no disponible' })).toBeVisible();
  await expect(page.getByText('No podemos confirmar cortes ni ausencia de cortes.').first()).toBeVisible();
});

test('rate limiting is explained with Retry-After', async ({ page }) => {
  await mockApi(page, { rateLimited: true });
  await openPublic(page);
  await page.getByLabel('Dirección (calle y altura)', { exact: true }).fill('calchaqui 100');
  await page.getByRole('button', { name: 'Buscar dirección' }).click();
  await expect(page.getByText('Demasiadas solicitudes. Reintentá en 30 segundos.')).toBeVisible();
});

test('degraded source is not presented as updated', async ({ page }) => {
  const degraded = result({
    state: 'unavailable',
    freshness: 'fresh',
    source_status: 'degraded',
    coverage: { partido: 'SAN VICENTE', localidad: null, status: 'covered' },
    outages: undefined,
  });
  await mockApi(page, { byPartido: { 'SAN VICENTE': degraded } });
  await openPublic(page);
  await page.getByLabel('Partido', { exact: true }).selectOption('SAN VICENTE');
  await page.getByRole('button', { name: 'Consultar cortes' }).click();
  await expect(page.getByRole('heading', { name: 'Fuente no disponible' })).toBeVisible();
  await expect(page.getByText('Fuente degradada')).toBeVisible();
  await expect(page.getByText('Información actualizada')).toHaveCount(0);
  await expect(page.getByText('El ENRE informó que no está actualizando la información. No podemos confirmar cortes ni ausencia de cortes.')).toBeVisible();
});

test('denied geolocation explains the fallback without querying', async ({ page }) => {
  await mockApi(page);
  await openPublic(page);
  await page.getByRole('button', { name: 'Usar mi ubicación' }).click();
  await expect(page.getByText(/No autorizaste la ubicación|No pudimos obtener tu ubicación/)).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Cortes reportados' })).toHaveCount(0);
});

test('unresolved address shows the geographic error without an outage list', async ({ page }) => {
  await mockApi(page);
  await page.route('**/api/outages/resolve', route => route.fulfill({
    status: 422,
    json: { detail: 'No pudimos ubicar la dirección. Probá con partido y localidad.' },
  }));
  await openPublic(page);
  await page.getByLabel('Dirección (calle y altura)', { exact: true }).fill('calle inexistente 99999');
  await page.getByRole('button', { name: 'Buscar dirección' }).click();
  await expect(page.getByText('No pudimos ubicar la dirección. Probá con partido y localidad.')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Cortes reportados' })).toHaveCount(0);
});

test('authenticated shell still renders the private diary after the public view', async ({ page }) => {
  await mockApi(page, { authenticated: true });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Domicilios' })).toBeVisible();
  await page.getByRole('button', { name: 'Cortes' }).click();
  await expect(page.getByRole('heading', { name: 'Cortes eléctricos' })).toBeVisible();
  await page.getByRole('button', { name: 'Mi cuenta' }).click();
  await expect(page.getByRole('heading', { name: 'Domicilios' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Cerrar sesión' })).toBeVisible();
});

async function expectNoHealthPanel(page: Page): Promise<void> {
  await expect(page.getByRole('heading', { name: 'Conexión con la API' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Volver a comprobar' })).toHaveCount(0);
  await expect(page.getByText('Conexión con la API')).toHaveCount(0);
  await expect(page.getByText('Esta pantalla comprueba únicamente que el servicio HTTP responde.')).toHaveCount(0);
}

test('public shell renders every section without the technical API panel', async ({ page }) => {
  const healthRequests: string[] = [];
  page.on('request', request => {
    if (new URL(request.url()).pathname === '/api/health') healthRequests.push(request.url());
  });
  await mockApi(page);
  await page.goto('/');
  await expectNoHealthPanel(page);
  for (const [section, heading] of [
    ['Cortes', 'Cortes eléctricos'],
    ['Trabajos', 'Trabajos programados'],
    ['Mi cuenta', 'Diario de interrupciones'],
  ] as const) {
    await page.getByRole('button', { name: section }).click();
    await expect(page.getByRole('heading', { name: heading, exact: true })).toBeVisible();
    await expectNoHealthPanel(page);
  }
  expect(healthRequests).toEqual([]);
});

test('authenticated shell renders the diary without the technical API panel', async ({ page }) => {
  const healthRequests: string[] = [];
  page.on('request', request => {
    if (new URL(request.url()).pathname === '/api/health') healthRequests.push(request.url());
  });
  await mockApi(page, { authenticated: true });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Domicilios' })).toBeVisible();
  await expectNoHealthPanel(page);
  await page.getByRole('button', { name: 'Cortes' }).click();
  await expectNoHealthPanel(page);
  await page.getByRole('button', { name: 'Mi cuenta' }).click();
  await expect(page.getByRole('heading', { name: 'Domicilios' })).toBeVisible();
  await expectNoHealthPanel(page);
  expect(healthRequests).toEqual([]);
});
