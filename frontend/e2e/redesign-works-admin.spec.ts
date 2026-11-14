import { expect, test } from '@playwright/test';
import type { Page, Route } from '@playwright/test';

const AREAS = {
  coverage_version: '2026-11-10',
  coverage_retrieved_on: '2026-11-10',
  areas: [
    { partido: 'ALMIRANTE BROWN', localidades: [
      { localidad: 'GLEW', coverage: 'covered', reported: true },
    ] },
  ],
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

const ADMIN_SOURCES = {
  sources: [
    {
      key: 'outages', scheduler_enabled: true, interval_seconds: 300, version: 1,
      last_attempt_at: '2026-11-13T12:00:00Z', last_attempt_outcome: 'ok',
      last_attempt_error: null, last_success_at: '2026-11-13T12:00:00Z',
      last_skipped_locked_at: null,
    },
    {
      key: 'scheduled_works', scheduler_enabled: false, interval_seconds: 300, version: 1,
      last_attempt_at: '2026-11-13T12:00:00Z', last_attempt_outcome: 'ok',
      last_attempt_error: null, last_success_at: '2026-11-13T12:00:00Z',
      last_skipped_locked_at: null,
    },
  ],
};

async function mockAdminApi(page: Page): Promise<string[]> {
  const requests: string[] = [];
  await page.route('**/api/**', async (route: Route) => {
    const url = new URL(route.request().url());
    requests.push(url.pathname);
    if (url.pathname === '/api/session') {
      await route.fulfill({ status: 200, json: {
        account: { id: 'synthetic', username: 'qa-synthetic', role: 'admin' },
        csrf_token: 'synthetic-csrf',
      } });
      return;
    }
    if (url.pathname === '/api/domiciles') {
      await route.fulfill({ status: 200, json: [] });
      return;
    }
    if (url.pathname === '/api/admin/sources') {
      await route.fulfill({ status: 200, json: ADMIN_SOURCES });
      return;
    }
    await route.fulfill({ status: 404, json: { detail: 'not mocked' } });
  });
  return requests;
}

async function mockApi(page: Page): Promise<string[]> {
  const requests: string[] = [];
  await page.route('**/api/**', async (route: Route) => {
    const url = new URL(route.request().url());
    requests.push(url.pathname);
    if (url.pathname === '/api/session') {
      await route.fulfill({ status: 401, json: { detail: 'Sin sesión' } });
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
      await route.fulfill({ status: 200, json: WORKS });
      return;
    }
    await route.fulfill({ status: 404, json: { detail: 'not mocked' } });
  });
  return requests;
}

async function openWorks(page: Page): Promise<void> {
  await page.goto('/');
  await page.getByRole('button', { name: 'Trabajos' }).click();
  await expect(page.getByRole('heading', { name: 'Trabajos programados', exact: true })).toBeVisible();
}

async function queryWorks(page: Page): Promise<void> {
  await page.getByLabel('Partido', { exact: true }).selectOption('ALMIRANTE BROWN');
  await page.getByLabel('Localidad (opcional)', { exact: true }).selectOption('GLEW');
  await page.getByRole('button', { name: 'Consultar trabajos' }).click();
  await expect(page.getByRole('heading', { name: 'Trabajos informados', exact: true })).toBeVisible();
}

test('CU02 uses the approved shell, palette and one heading', async ({ page }) => {
  await mockApi(page);
  await openWorks(page);

  await expect(page.getByRole('banner')).toHaveCount(1);
  await expect(page.getByRole('main')).toHaveCount(1);
  await expect(page.getByRole('contentinfo')).toHaveCount(1);
  await expect(page.locator('h1')).toHaveCount(1);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Trabajos programados');
  await expect(page.getByRole('button', { name: 'Trabajos', exact: true }))
    .toHaveAttribute('aria-current', 'page');
  await expect(page.locator('[aria-current="page"]')).toHaveCount(1);
  await expect(page.getByRole('button', { name: 'Administración', exact: true })).toHaveCount(0);

  const colors = await page.evaluate(() => ({
    background: getComputedStyle(document.body).backgroundColor,
    foreground: getComputedStyle(document.body).color,
    primary: getComputedStyle(document.querySelector('main button[type="button"]') as HTMLElement).backgroundColor,
  }));
  expect(colors).toEqual({
    background: 'rgb(248, 250, 252)',
    foreground: 'rgb(15, 23, 42)',
    primary: 'rgb(13, 97, 119)',
  });
});

test('CU02 controls share the same token-defined visual language', async ({ page }) => {
  await mockApi(page);
  await openWorks(page);

  const styles = await page.evaluate(() => {
    const input = document.querySelector('#scheduled-filter') as HTMLElement;
    const select = document.querySelector('#scheduled-partido') as HTMLElement;
    const card = document.querySelector('[data-slot="card"]') as HTMLElement;
    const button = document.querySelector('main button[type="button"]') as HTMLElement;
    const read = (element: HTMLElement) => {
      const style = getComputedStyle(element);
      return { radius: style.borderRadius, height: element.getBoundingClientRect().height };
    };
    return { input: read(input), select: read(select), cardRadius: getComputedStyle(card).borderRadius,
      buttonHeight: button.getBoundingClientRect().height };
  });
  expect(styles.input.radius).toBe(styles.select.radius);
  expect(styles.input.height).toBeGreaterThanOrEqual(40);
  expect(styles.select.height).toBeGreaterThanOrEqual(40);
  expect(styles.cardRadius).toBe('12px');
  expect(styles.buttonHeight).toBeGreaterThanOrEqual(44);
});

test('CU02 stays inside the centred container and avoids overflow at three widths', async ({ page }) => {
  await mockApi(page);
  await openWorks(page);
  await queryWorks(page);

  for (const width of [390, 820, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    const metrics = await page.evaluate(() => {
      const main = document.querySelector('main') as HTMLElement;
      return {
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        mainWidth: main.getBoundingClientRect().width,
      };
    });
    expect(metrics.overflow, `no horizontal overflow at ${width}px`).toBe(0);
    expect(metrics.mainWidth, `main stays within the container at ${width}px`).toBeLessThanOrEqual(1200);
    await expect(page.getByRole('button', { name: 'Trabajos', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Mi cuenta', exact: true })).toBeVisible();
  }
});

test('CU02 keeps one chat mount and never requests the health endpoint', async ({ page }) => {
  const requests = await mockApi(page);
  await openWorks(page);
  await queryWorks(page);

  await expect(page.locator('[data-chat-mount="cu03"]')).toHaveCount(1);
  expect(requests.filter(path => path === '/api/health')).toEqual([]);
});

test('CU02 result keeps the table region keyboard reachable', async ({ page }) => {
  await mockApi(page);
  await openWorks(page);
  await queryWorks(page);

  const region = page.locator('[data-slot="table-container"]');
  await region.focus();
  await expect(region).toBeFocused();
  await expect(page.getByRole('columnheader', { name: 'Zona' })).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'Motivo' })).toBeVisible();
});

test('CU10 uses the approved shell and palette at three widths', async ({ page }) => {
  const requests = await mockAdminApi(page);
  await page.goto('/');
  await page.addStyleTag({ content: '*, *::before, *::after { transition: none !important; animation: none !important; }' });
  await page.getByRole('button', { name: 'Administración' }).click();
  await expect(page.getByRole('heading', { name: 'Administración de fuentes', exact: true })).toBeVisible();
  // Leave the clicked button so its hover tint does not replace the active color.
  await page.getByRole('heading', { name: 'Administración de fuentes', exact: true }).hover();

  await expect(page.getByRole('banner')).toHaveCount(1);
  await expect(page.getByRole('main')).toHaveCount(1);
  await expect(page.getByRole('contentinfo')).toHaveCount(1);
  await expect(page.locator('h1')).toHaveCount(1);
  await expect(page.getByRole('button', { name: 'Administración', exact: true }))
    .toHaveAttribute('aria-current', 'page');
  await expect(page.locator('[aria-current="page"]')).toHaveCount(1);

  const colors = await page.evaluate(() => ({
    background: getComputedStyle(document.body).backgroundColor,
    foreground: getComputedStyle(document.body).color,
    active: getComputedStyle(document.querySelector('header [aria-current="page"]') as HTMLElement).backgroundColor,
  }));
  expect(colors).toEqual({
    background: 'rgb(248, 250, 252)',
    foreground: 'rgb(15, 23, 42)',
    active: 'rgb(13, 97, 119)',
  });
  expect(requests.filter(path => path === '/api/health')).toEqual([]);

  for (const width of [390, 820, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    const metrics = await page.evaluate(() => {
      const main = document.querySelector('main') as HTMLElement;
      return {
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        mainWidth: main.getBoundingClientRect().width,
      };
    });
    expect(metrics.overflow, `no horizontal overflow at ${width}px`).toBe(0);
    expect(metrics.mainWidth, `main stays within the container at ${width}px`).toBeLessThanOrEqual(1200);
    await expect(page.locator('h1')).toHaveCount(1);
  }
});
