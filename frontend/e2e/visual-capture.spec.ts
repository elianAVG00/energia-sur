import path from 'node:path';
import { mkdir } from 'node:fs/promises';
import { expect, test } from '@playwright/test';
import type { Page, Route } from '@playwright/test';

// Evidence-only spec: never runs in the regular gate unless VISUAL_CAPTURE=1.
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
    { partido: 'ALMIRANTE BROWN', localidades: [
      { localidad: 'GLEW', coverage: 'covered', reported: true },
    ] },
  ],
};

const OUTAGES = {
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

const WORKS = {
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

async function mockApi(page: Page): Promise<void> {
  await page.route('**/api/**', async (route: Route) => {
    const url = new URL(route.request().url());
    if (url.pathname === '/api/session') {
      await route.fulfill({ status: 401, json: { detail: 'Sin sesión' } });
      return;
    }
    if (url.pathname === '/api/domiciles') {
      await route.fulfill({ status: 200, json: [] });
      return;
    }
    if (url.pathname === '/api/outages/areas' || url.pathname === '/api/scheduled-works/areas') {
      await route.fulfill({ status: 200, json: AREAS });
      return;
    }
    if (url.pathname === '/api/outages') {
      await route.fulfill({ status: 200, json: OUTAGES });
      return;
    }
    if (url.pathname === '/api/scheduled-works') {
      await route.fulfill({ status: 200, json: WORKS });
      return;
    }
    await route.fulfill({ status: 404, json: { detail: 'not mocked' } });
  });
}

async function capture(page: Page, name: string): Promise<void> {
  if (!OUT_DIR) throw new Error('VISUAL_DIR is required when VISUAL_CAPTURE=1.');
  await mkdir(OUT_DIR, { recursive: true });
  await page.screenshot({ path: path.join(OUT_DIR, name), fullPage: true });
}

for (const viewport of VIEWPORTS) {
  test(`captures shell evidence at ${viewport.name}`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await mockApi(page);
    await page.goto('/');
    // Freeze CSS transitions so captures show the settled state of the active nav.
    await page.addStyleTag({ content: '*, *::before, *::after { transition: none !important; animation: none !important; }' });

    await expect(page.getByRole('heading', { name: 'Ingresar' })).toBeVisible();
    await capture(page, `login-${viewport.name}.png`);

    await page.getByRole('button', { name: 'Cortes' }).click();
    await expect(page.getByRole('heading', { name: 'Cortes eléctricos' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cortes', exact: true })).toHaveAttribute('aria-current', 'page');
    await expect(page.getByLabel('Partido', { exact: true })).toContainText('LOMAS DE ZAMORA');
    await capture(page, `cortes-inicial-${viewport.name}.png`);

    await page.getByLabel('Partido', { exact: true }).selectOption('LOMAS DE ZAMORA');
    await page.getByLabel('Localidad (opcional)', { exact: true }).selectOption('BANFIELD');
    await page.getByRole('button', { name: 'Consultar cortes' }).click();
    await expect(page.getByRole('heading', { name: 'Cortes reportados' })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'Media tensión' })).toBeVisible();
    await capture(page, `cortes-resultado-${viewport.name}.png`);

    await page.getByRole('button', { name: 'Trabajos' }).click();
    await expect(page.getByRole('heading', { name: 'Trabajos programados' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Trabajos', exact: true })).toHaveAttribute('aria-current', 'page');
    await page.getByLabel('Partido', { exact: true }).selectOption('ALMIRANTE BROWN');
    await page.getByLabel('Localidad (opcional)', { exact: true }).selectOption('GLEW');
    await page.getByRole('button', { name: 'Consultar trabajos' }).click();
    await expect(page.getByRole('heading', { name: 'Trabajos informados' })).toBeVisible();
    await capture(page, `trabajos-resultado-${viewport.name}.png`);
  });
}
