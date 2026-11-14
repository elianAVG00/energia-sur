import { expect, test } from '@playwright/test';
import type { Page, Route } from '@playwright/test';

const AREAS = {
  coverage_version: '2026-11-10',
  coverage_retrieved_on: '2026-11-10',
  areas: [
    { partido: 'ALMIRANTE BROWN', localidades: [
      { localidad: 'GLEW', coverage: 'covered', reported: true },
    ] },
    { partido: 'BERAZATEGUI', localidades: [
      { localidad: 'BERAZATEGUI', coverage: 'covered', reported: false },
    ] },
    { partido: 'CAPITAL', localidades: [] },
  ],
};

const RESOLVED = {
  status: 'resolved',
  zone: { partido: 'ALMIRANTE BROWN', localidad: null, granularity: 'partido', coverage: 'covered' },
};

const CANDIDATES = {
  status: 'candidates',
  candidates: [
    { partido: 'ALMIRANTE BROWN', localidad: 'GLEW', granularity: 'localidad', coverage: 'covered' },
    { partido: 'SAN VICENTE', localidad: 'ALEJANDRO KORN', granularity: 'localidad', coverage: 'covered' },
  ],
};

function result(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
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
    ...overrides,
  };
}

interface MockOptions {
  authenticated?: boolean;
  resolve?: unknown;
  location?: unknown;
  byPartido?: Record<string, Record<string, unknown>>;
  queryStatus?: number;
  resolveStatus?: number;
  delayMs?: number;
  onResolve?: (body: unknown, headers: Record<string, string>) => void;
}

async function openWorks(page: Page): Promise<void> {
  await page.goto('/');
  await page.getByRole('button', { name: 'Trabajos' }).click();
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
    if (url.pathname === '/api/scheduled-works/areas') {
      await route.fulfill({ status: 200, json: AREAS });
      return;
    }
    if (url.pathname === '/api/scheduled-works') {
      if (options.delayMs) await new Promise(resolve => setTimeout(resolve, options.delayMs));
      if (options.queryStatus && options.queryStatus !== 200) {
        await route.fulfill({ status: options.queryStatus, json: { detail: 'No se pudo consultar la fuente.' } });
        return;
      }
      const partido = url.searchParams.get('partido') ?? '';
      await route.fulfill({ status: 200, json: options.byPartido?.[partido] ?? result() });
      return;
    }
    if (url.pathname === '/api/outages/resolve') {
      options.onResolve?.(
        request.postDataJSON() as unknown,
        request.headers() as Record<string, string>,
      );
      if (options.resolveStatus && options.resolveStatus !== 200) {
        await route.fulfill({ status: options.resolveStatus, json: { detail: 'No se pudo resolver la dirección.' } });
        return;
      }
      await route.fulfill({ status: 200, json: options.resolve ?? RESOLVED });
      return;
    }
    if (url.pathname === '/api/outages/resolve-location') {
      await route.fulfill({ status: 200, json: options.location ?? RESOLVED });
      return;
    }
    await route.fulfill({ status: 404, json: { detail: 'not mocked' } });
  });
}

test('visitor sees reported works without dates, motives or direct ENRE access', async ({ page }) => {
  const external: string[] = [];
  page.on('request', request => {
    if (/enre\.gov\.ar|datos\.gob\.ar/.test(request.url())) external.push(request.url());
  });
  await mockApi(page);
  await openWorks(page);
  await expect(page.getByRole('heading', { name: 'Trabajos programados' })).toBeVisible();
  await page.getByLabel('Partido', { exact: true }).selectOption('ALMIRANTE BROWN');
  await page.getByLabel('Localidad (opcional)', { exact: true }).selectOption('GLEW');
  await page.getByRole('button', { name: 'Consultar trabajos' }).click();
  await expect(page.getByRole('heading', { name: 'Trabajos informados' })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'ALMIRANTE BROWN · GLEW' })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'No publicado por la fuente' })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Sin datos' })).toBeVisible();
  await expect(page.getByText(/no publica fecha de inicio ni de fin/i)).toBeVisible();
  await expect(page.getByText(/No son una agenda de trabajos futuros/i)).toBeVisible();
  await expect(page.getByText(/No es una fecha de fin/)).toBeVisible();
  await expect(page.locator('input[type="date"]')).toHaveCount(0);
  await expect(page.getByLabel('Desde', { exact: true })).toHaveCount(0);
  await expect(page.getByLabel('Hasta', { exact: true })).toHaveCount(0);
  expect(external).toEqual([]);
});

test('empty agenda and unverified coverage are distinct states', async ({ page }) => {
  await mockApi(page, { byPartido: {
    BERAZATEGUI: result({
      state: 'no_works', granularity: 'localidad',
      coverage: { partido: 'BERAZATEGUI', localidad: 'BERAZATEGUI', status: 'covered' },
      works: [],
    }),
    CAPITAL: result({
      state: 'coverage_unverified',
      coverage: { partido: 'CAPITAL', localidad: null, status: 'coverage_unverified' },
      works: undefined,
    }),
  } });
  await openWorks(page);

  await page.getByLabel('Partido', { exact: true }).selectOption('BERAZATEGUI');
  await page.getByLabel('Localidad (opcional)', { exact: true }).selectOption('BERAZATEGUI');
  await page.getByRole('button', { name: 'Consultar trabajos' }).click();
  await expect(page.getByRole('heading', { name: 'Sin trabajos informados' })).toBeVisible();
  await expect(page.getByText(/no publica una agenda de fechas futuras/i)).toBeVisible();

  await page.getByLabel('Partido', { exact: true }).selectOption('CAPITAL');
  await page.getByRole('button', { name: 'Consultar trabajos' }).click();
  await expect(page.getByRole('heading', { name: 'Cobertura no verificada' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Sin trabajos informados' })).toHaveCount(0);
});

test('ambiguous address shows candidates and posts without CSRF', async ({ page }) => {
  let body: unknown;
  let csrf: string | undefined;
  await mockApi(page, {
    resolve: CANDIDATES,
    onResolve: (value, headers) => { body = value; csrf = headers['x-csrf-token']; },
  });
  await openWorks(page);
  await page.getByLabel('Dirección (calle y altura)', { exact: true }).fill('calchaqui 100');
  await page.getByRole('button', { name: 'Buscar dirección' }).click();
  await expect(page.getByText('La dirección es ambigua. Elegí una de las zonas encontradas.')).toBeVisible();
  await page.getByRole('button', { name: /ALMIRANTE BROWN · GLEW/ }).click();
  await expect(page.getByRole('heading', { name: 'Trabajos informados' })).toBeVisible();
  expect(body).toEqual({ address: 'calchaqui 100' });
  expect(csrf).toBeUndefined();
});

test('consented browser location resolves a partido and degrades the search', async ({ page, context }) => {
  await context.grantPermissions(['geolocation']);
  await context.setGeolocation({ latitude: -34.76, longitude: -58.4 });
  await mockApi(page, { location: RESOLVED });
  await openWorks(page);
  await page.getByRole('button', { name: 'Usar mi ubicación' }).click();
  await expect(page.getByText('Búsqueda limitada al partido ALMIRANTE BROWN: no se pudo determinar una localidad confiable.')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Trabajos informados' })).toBeVisible();
});

test('authenticated shell still renders the private diary after the public works view', async ({ page }) => {
  await mockApi(page, { authenticated: true });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Domicilios' })).toBeVisible();
  await page.getByRole('button', { name: 'Trabajos' }).click();
  await expect(page.getByRole('heading', { name: 'Trabajos programados' })).toBeVisible();
  await page.getByRole('button', { name: 'Mi cuenta' }).click();
  await expect(page.getByRole('heading', { name: 'Domicilios' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Cerrar sesión' })).toBeVisible();
});

test('result card presents scope, unpublished dates and provenance', async ({ page }) => {
  await mockApi(page);
  await openWorks(page);
  await page.getByLabel('Partido', { exact: true }).selectOption('ALMIRANTE BROWN');
  await page.getByLabel('Localidad (opcional)', { exact: true }).selectOption('GLEW');
  await page.getByRole('button', { name: 'Consultar trabajos' }).click();

  await expect(page.getByRole('heading', { name: 'Trabajos informados' })).toBeVisible();
  await expect(page.getByText('Resultado por localidad')).toBeVisible();
  await expect(page.getByText('Cobertura verificada')).toBeVisible();
  await expect(page.getByText('Información actualizada')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Zona y alcance de los datos' })).toBeVisible();
  await expect(page.getByText('Inicio planificado')).toBeVisible();
  await expect(page.getByText('Fin planificado')).toBeVisible();
  await expect(page.getByText('No publicado', { exact: true })).toHaveCount(2);
  await expect(page.getByRole('cell', { name: 'No publicado por la fuente' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'ENRE' })).toHaveAttribute('href', /^https:\/\//);
  await expect(page.locator('input[type="date"]')).toHaveCount(0);
  await expect(page.getByLabel('Desde', { exact: true })).toHaveCount(0);
  await expect(page.getByLabel('Hasta', { exact: true })).toHaveCount(0);
});

test('stale and degraded results keep the works and mark the source', async ({ page }) => {
  await mockApi(page, { byPartido: {
    'ALMIRANTE BROWN': result({
      state: 'stale',
      freshness: 'stale',
      source_status: 'degraded',
    }),
  } });
  await openWorks(page);
  await page.getByLabel('Partido', { exact: true }).selectOption('ALMIRANTE BROWN');
  await page.getByRole('button', { name: 'Consultar trabajos' }).click();

  await expect(page.getByRole('heading', { name: 'Información desactualizada' })).toBeVisible();
  await expect(page.getByText('Fuente degradada')).toBeVisible();
  await expect(page.getByText(/La última sincronización de trabajos no fue exitosa/)).toBeVisible();
  await expect(page.getByText(/La última actualización tiene más de 15 minutos/).first()).toBeVisible();
  await expect(page.getByRole('cell', { name: 'ALMIRANTE BROWN · GLEW' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Sin trabajos informados' })).toHaveCount(0);
});

test('unverified coverage does not claim that there are no works', async ({ page }) => {
  await mockApi(page, { byPartido: {
    CAPITAL: result({
      state: 'coverage_unverified',
      coverage: { partido: 'CAPITAL', localidad: null, status: 'coverage_unverified' },
      works: undefined,
    }),
  } });
  await openWorks(page);
  await page.getByLabel('Partido', { exact: true }).selectOption('CAPITAL');
  await page.getByRole('button', { name: 'Consultar trabajos' }).click();

  await expect(page.getByRole('heading', { name: 'Cobertura no verificada' })).toBeVisible();
  await expect(page.getByText(/no podemos confirmar/i)).toBeVisible();
  await expect(page.getByRole('table')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Sin trabajos informados' })).toHaveCount(0);
});

test('loading and query errors are announced in the search card', async ({ page }) => {
  await mockApi(page, { delayMs: 600 });
  await openWorks(page);
  await page.getByLabel('Partido', { exact: true }).selectOption('ALMIRANTE BROWN');
  await page.getByRole('button', { name: 'Consultar trabajos' }).click();
  await expect(page.getByText(/Consultando trabajos/)).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Trabajos informados' })).toBeVisible();

  await page.unroute('**/api/**');
  await mockApi(page, { queryStatus: 503 });
  await openWorks(page);
  await page.getByLabel('Partido', { exact: true }).selectOption('ALMIRANTE BROWN');
  await page.getByRole('button', { name: 'Consultar trabajos' }).click();
  await expect(page.getByRole('alert')).toHaveText(/No se pudo consultar la fuente/);
  await expect(page.getByRole('heading', { name: 'Trabajos informados' })).toHaveCount(0);
});

test('empty address and address errors stay in the address card', async ({ page }) => {
  await mockApi(page, { resolveStatus: 503 });
  await openWorks(page);
  await page.getByRole('button', { name: 'Buscar dirección' }).click();
  await expect(page.getByText('Ingresá una dirección con calle y altura.')).toBeVisible();

  await page.getByLabel('Dirección (calle y altura)', { exact: true }).fill('calchaqui 100');
  await page.getByRole('button', { name: 'Buscar dirección' }).click();
  await expect(page.getByRole('alert')).toHaveText(/No se pudo resolver la dirección/);
  const addressCard = page.locator('section').filter({
    has: page.getByRole('heading', { name: 'Buscar por dirección' }),
  });
  await expect(addressCard.getByRole('alert')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Trabajos informados' })).toHaveCount(0);
});

test('no works and unverified coverage do not present planned date fields', async ({ page }) => {
  await mockApi(page, { byPartido: {
    BERAZATEGUI: result({
      state: 'no_works', works: [],
      coverage: { partido: 'BERAZATEGUI', localidad: 'BERAZATEGUI', status: 'covered' },
    }),
    CAPITAL: result({
      state: 'coverage_unverified',
      coverage: { partido: 'CAPITAL', localidad: null, status: 'coverage_unverified' },
      works: undefined,
    }),
  } });
  await openWorks(page);

  await page.getByLabel('Partido', { exact: true }).selectOption('BERAZATEGUI');
  await page.getByLabel('Localidad (opcional)', { exact: true }).selectOption('BERAZATEGUI');
  await page.getByRole('button', { name: 'Consultar trabajos' }).click();
  await expect(page.getByRole('heading', { name: 'Sin trabajos informados' })).toBeVisible();
  await expect(page.getByText('Inicio planificado')).toHaveCount(0);
  await expect(page.getByText('Fin planificado')).toHaveCount(0);

  await page.getByLabel('Partido', { exact: true }).selectOption('CAPITAL');
  await page.getByRole('button', { name: 'Consultar trabajos' }).click();
  await expect(page.getByRole('heading', { name: 'Cobertura no verificada' })).toBeVisible();
  await expect(page.getByText('Inicio planificado')).toHaveCount(0);
  await expect(page.getByText('Fin planificado')).toHaveCount(0);
});

test('denied geolocation explains the fallback without querying', async ({ page }) => {
  await mockApi(page);
  await openWorks(page);
  await page.getByRole('button', { name: 'Usar mi ubicación' }).click();
  await expect(page.getByText(/No autorizaste la ubicación|No pudimos obtener tu ubicación/)).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Trabajos informados' })).toHaveCount(0);
});

test('address resolution reports the resolved zone in the address card', async ({ page }) => {
  await mockApi(page);
  await openWorks(page);
  await page.getByLabel('Dirección (calle y altura)', { exact: true }).fill('calchaqui 100');
  await page.getByRole('button', { name: 'Buscar dirección' }).click();
  const addressCard = page.locator('section').filter({
    has: page.getByRole('heading', { name: 'Buscar por dirección' }),
  });
  await expect(addressCard.getByText(/Búsqueda limitada al partido ALMIRANTE BROWN/)).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Trabajos informados' })).toBeVisible();
});

test('narrow viewport keeps the works table in its own scroll region', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockApi(page);
  await openWorks(page);
  await page.getByLabel('Partido', { exact: true }).selectOption('ALMIRANTE BROWN');
  await page.getByLabel('Localidad (opcional)', { exact: true }).selectOption('GLEW');
  await page.getByRole('button', { name: 'Consultar trabajos' }).click();
  await expect(page.getByRole('heading', { name: 'Trabajos informados' })).toBeVisible();

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBe(0);

  const region = page.locator('[data-slot="table-container"]');
  await region.focus();
  await expect(region).toBeFocused();
  const widths = await region.evaluate(element => ({
    scrollWidth: element.scrollWidth,
    clientWidth: element.clientWidth,
  }));
  expect(widths.scrollWidth).toBeGreaterThan(widths.clientWidth);
  for (const header of ['Zona', 'Alimentador', 'Usuarios afectados',
    'Normalización estimada', 'Motivo']) {
    await expect(page.getByRole('columnheader', { name: header })).toBeVisible();
  }
  const button = await page.getByRole('button', { name: 'Consultar trabajos' }).boundingBox();
  expect(button?.width ?? 0).toBeGreaterThan(300);
});
