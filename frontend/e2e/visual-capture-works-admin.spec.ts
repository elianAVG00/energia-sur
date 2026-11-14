import path from 'node:path';
import { mkdir } from 'node:fs/promises';
import { expect, test } from '@playwright/test';
import type { Page, Route } from '@playwright/test';

// Evidence-only spec for the CU02/CU10 redesign. Never runs in the regular gate
// unless VISUAL_CAPTURE=1. Synthetic data only.
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
    { partido: 'ALMIRANTE BROWN', localidades: [
      { localidad: 'GLEW', coverage: 'covered', reported: true },
    ] },
    { partido: 'BERAZATEGUI', localidades: [
      { localidad: 'BERAZATEGUI', coverage: 'covered', reported: false },
    ] },
    { partido: 'CAPITAL', localidades: [] },
  ],
};

function works(overrides: Record<string, unknown> = {}): Record<string, unknown> {
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

const CU02_SCENES = {
  initial: null,
  reported: works(),
  'no-works': works({
    state: 'no_works', works: [],
    coverage: { partido: 'BERAZATEGUI', localidad: 'BERAZATEGUI', status: 'covered' },
    limitations: ['dates_not_published', 'reason_not_published', 'proximity_not_available'],
  }),
  'stale-degraded': works({
    state: 'stale', freshness: 'stale', source_status: 'degraded',
  }),
  'coverage-unverified': works({
    state: 'coverage_unverified',
    coverage: { partido: 'CAPITAL', localidad: null, status: 'coverage_unverified' },
    works: undefined,
    limitations: ['dates_not_published', 'reason_not_published', 'proximity_not_available'],
  }),
  error: 'error',
} as const;

type Cu02Scene = keyof typeof CU02_SCENES;

function source(
  key: 'outages' | 'scheduled_works', overrides: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    key, scheduler_enabled: key === 'outages', interval_seconds: 300, version: 1,
    last_attempt_at: '2026-11-13T12:00:00Z', last_attempt_outcome: 'ok',
    last_attempt_error: null, last_success_at: '2026-11-13T12:00:00Z',
    last_skipped_locked_at: null, ...overrides,
  };
}

const CU10_SCENES = {
  normal: { sources: [source('outages'), source('scheduled_works')] },
  failure: { sources: [
    source('outages', {
      last_attempt_at: '2026-11-13T12:20:00Z',
      last_attempt_outcome: 'timeout',
      last_attempt_error: 'EnreTimeout',
      last_success_at: '2026-11-13T11:55:00Z',
      last_skipped_locked_at: '2026-11-13T12:10:00Z',
    }),
    source('scheduled_works'),
  ] },
} as const;

type Cu10Scene = keyof typeof CU10_SCENES;

async function mockApi(
  page: Page,
  getScenario: () => Cu02Scene | Cu10Scene,
  role: 'admin' | 'none',
): Promise<void> {
  await page.route('**/api/**', async (route: Route) => {
    const url = new URL(route.request().url());
    if (url.pathname === '/api/session') {
      if (role === 'admin') {
        await route.fulfill({ status: 200, json: {
          account: { id: 'synthetic', username: 'qa-synthetic', role: 'admin' },
          csrf_token: 'synthetic-csrf',
        } });
      } else {
        await route.fulfill({ status: 401, json: { detail: 'Sin sesión' } });
      }
      return;
    }
    if (url.pathname === '/api/domiciles' || url.pathname === '/api/health') {
      await route.fulfill({ status: 200, json: [] });
      return;
    }
    if (url.pathname === '/api/scheduled-works/areas') {
      await route.fulfill({ status: 200, json: AREAS });
      return;
    }
    if (url.pathname === '/api/scheduled-works') {
      const scene = getScenario() as Cu02Scene;
      if (scene === 'error') {
        await route.fulfill({ status: 503, json: { detail: 'snapshot store unavailable' } });
        return;
      }
      await route.fulfill({ status: 200, json: CU02_SCENES[scene] });
      return;
    }
    if (url.pathname === '/api/admin/sources') {
      await route.fulfill({ status: 200, json: CU10_SCENES[getScenario() as Cu10Scene] });
      return;
    }
    await route.fulfill({ status: 404, json: { detail: 'not mocked' } });
  });
}

async function capture(page: Page, name: string): Promise<void> {
  if (!OUT_DIR) throw new Error('VISUAL_DIR is required when VISUAL_CAPTURE=1.');
  await mkdir(OUT_DIR, { recursive: true });
  // Added after navigation so the sticky nav settles before the screenshot.
  await page.addStyleTag({ content: '*, *::before, *::after { transition: none !important; animation: none !important; }' });
  await page.evaluate(() => window.scrollTo(0, 0));
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow, `no horizontal overflow before ${name}`).toBe(0);
  await page.screenshot({ path: path.join(OUT_DIR, name), fullPage: true });
}

async function openWorks(page: Page): Promise<void> {
  await page.goto('/');
  await page.getByRole('button', { name: 'Trabajos' }).click();
  await expect(page.getByRole('heading', { name: 'Trabajos programados' })).toBeVisible();
}

async function openAdmin(page: Page): Promise<void> {
  await page.goto('/');
  await page.getByRole('button', { name: 'Administración' }).click();
  await expect(page.getByRole('heading', { name: 'Administración de fuentes' })).toBeVisible();
}

for (const viewport of VIEWPORTS) {
  test(`captures CU02 evidence at ${viewport.name}`, async ({ page }) => {
    let scene: Cu02Scene = 'initial';
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await mockApi(page, () => scene, 'none');
    await openWorks(page);
    await page.addStyleTag({ content: '*, *::before, *::after { transition: none !important; animation: none !important; }' });
    await capture(page, `cu02-inicial-${viewport.name}.png`);

    for (const [name, partido, localidad] of [
      ['resultado', 'ALMIRANTE BROWN', 'GLEW'],
      ['sin-trabajos', 'BERAZATEGUI', 'BERAZATEGUI'],
      ['desactualizado', 'ALMIRANTE BROWN', 'GLEW'],
      ['cobertura-no-verificada', 'CAPITAL', ''],
    ] as const) {
      scene = name === 'resultado' ? 'reported'
        : name === 'sin-trabajos' ? 'no-works'
          : name === 'desactualizado' ? 'stale-degraded' : 'coverage-unverified';
      await openWorks(page);
      await page.getByLabel('Partido', { exact: true }).selectOption(partido);
      if (localidad) {
        await page.getByLabel('Localidad (opcional)', { exact: true }).selectOption(localidad);
      }
      await page.getByRole('button', { name: 'Consultar trabajos' }).click();
      const heading = name === 'resultado' ? 'Trabajos informados'
        : name === 'sin-trabajos' ? 'Sin trabajos informados'
          : name === 'desactualizado' ? 'Información desactualizada' : 'Cobertura no verificada';
      await expect(page.getByRole('heading', { name: heading, exact: true })).toBeVisible();
      await capture(page, `cu02-${name}-${viewport.name}.png`);
    }

    scene = 'error';
    await openWorks(page);
    await page.getByLabel('Partido', { exact: true }).selectOption('ALMIRANTE BROWN');
    await page.getByRole('button', { name: 'Consultar trabajos' }).click();
    await expect(page.getByRole('alert')).toBeVisible();
    await capture(page, `cu02-error-consulta-${viewport.name}.png`);
  });

  test(`captures CU10 evidence at ${viewport.name}`, async ({ page }) => {
    let scene: Cu10Scene = 'normal';
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await mockApi(page, () => scene, 'admin');
    await page.addStyleTag({ content: '*, *::before, *::after { transition: none !important; animation: none !important; }' });

    await openAdmin(page);
    await expect(page.getByRole('heading', { name: 'ENRE — Cortes actuales' })).toBeVisible();
    await capture(page, `cu10-normal-${viewport.name}.png`);

    scene = 'failure';
    await openAdmin(page);
    await expect(page.getByRole('heading', { name: 'ENRE — Trabajos programados' })).toBeVisible();
    await expect(page.getByText('EnreTimeout')).toBeVisible();
    await capture(page, `cu10-error-${viewport.name}.png`);
  });
}
