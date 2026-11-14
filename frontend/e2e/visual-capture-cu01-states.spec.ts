import path from 'node:path';
import { mkdir } from 'node:fs/promises';
import { expect, test } from '@playwright/test';
import type { Page, Route } from '@playwright/test';

// Evidence-only spec for the CU01 state presentation: never runs in the regular
// gate unless VISUAL_CAPTURE=1. Synthetic data only.
test.skip(process.env.VISUAL_CAPTURE !== '1', 'Set VISUAL_CAPTURE=1 to write evidence screenshots.');

const OUT_DIR = process.env.VISUAL_DIR;

const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'tablet', width: 820, height: 1180 },
  { name: 'mobile', width: 390, height: 844 },
] as const;

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

const BY_PARTIDO = {
  'LOMAS DE ZAMORA': result({
    state: 'stale',
    freshness: 'stale',
    granularity: 'partido',
    coverage: { partido: 'LOMAS DE ZAMORA', localidad: null, status: 'coverage_unverified' },
  }),
  'SAN VICENTE': result({
    state: 'coverage_unverified',
    granularity: 'partido',
    coverage: { partido: 'SAN VICENTE', localidad: null, status: 'coverage_unverified' },
    outages: undefined,
  }),
  'CAPITAL': result({
    state: 'unavailable',
    freshness: 'unavailable',
    granularity: 'partido',
    coverage: { partido: 'CAPITAL', localidad: null, status: 'coverage_unverified' },
    outages: undefined,
  }),
};

async function mockApi(page: Page): Promise<void> {
  await page.route('**/api/**', async (route: Route) => {
    const url = new URL(route.request().url());
    if (url.pathname === '/api/session') {
      await route.fulfill({ status: 401, json: { detail: 'Sin sesión' } });
      return;
    }
    if (url.pathname === '/api/outages/areas') {
      await route.fulfill({ status: 200, json: AREAS });
      return;
    }
    if (url.pathname === '/api/outages') {
      const partido = url.searchParams.get('partido') ?? '';
      await route.fulfill({
        status: 200,
        json: (BY_PARTIDO as Record<string, Record<string, unknown>>)[partido] ?? result(),
      });
      return;
    }
    if (url.pathname === '/api/outages/resolve') {
      await route.fulfill({ status: 200, json: CANDIDATES });
      return;
    }
    await route.fulfill({ status: 404, json: { detail: 'not mocked' } });
  });
}

async function capture(page: Page, name: string): Promise<void> {
  if (!OUT_DIR) throw new Error('VISUAL_DIR is required when VISUAL_CAPTURE=1.');
  await mkdir(OUT_DIR, { recursive: true });
  // Reset the scroll position so the sticky header is captured at the top.
  await page.evaluate(() => window.scrollTo(0, 0));
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow, `no horizontal overflow before ${name}`).toBe(0);
  await page.screenshot({ path: path.join(OUT_DIR, name), fullPage: true });
}

for (const viewport of VIEWPORTS) {
  test(`captures CU01 state evidence at ${viewport.name}`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await mockApi(page);
    await page.goto('/');
    await page.addStyleTag({ content: '*, *::before, *::after { transition: none !important; animation: none !important; }' });
    await page.getByRole('button', { name: 'Cortes' }).click();
    await expect(page.getByRole('heading', { name: 'Cortes eléctricos' })).toBeVisible();

    // Candidates are captured first so no previous result card is on screen.
    await page.getByLabel('Dirección (calle y altura)', { exact: true }).fill('calchaqui 100');
    await page.getByRole('button', { name: 'Buscar dirección' }).click();
    await expect(page.getByText('La dirección es ambigua. Elegí una de las zonas encontradas.')).toBeVisible();
    await expect(page.getByRole('button', { name: /QUILMES · QUILMES/ })).toBeVisible();
    await capture(page, `estado-candidatas-${viewport.name}.png`);

    for (const [partido, heading, file] of [
      ['LOMAS DE ZAMORA', 'Información desactualizada', 'estado-desactualizado'],
      ['SAN VICENTE', 'Cobertura no verificada', 'estado-cobertura-no-verificada'],
      ['CAPITAL', 'Fuente no disponible', 'estado-fuente-no-disponible'],
    ] as const) {
      await page.getByLabel('Partido', { exact: true }).selectOption(partido);
      await page.getByRole('button', { name: 'Consultar cortes' }).click();
      await expect(page.getByRole('heading', { name: heading })).toBeVisible();
      await capture(page, `${file}-${viewport.name}.png`);
    }
  });
}
