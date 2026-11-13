import { expect, test } from '@playwright/test';
import type { Page, Route } from '@playwright/test';

interface MockSource {
  key: 'outages' | 'scheduled_works';
  scheduler_enabled: boolean;
  interval_seconds: number;
  version: number;
  last_attempt_at: string | null;
  last_attempt_outcome: string | null;
  last_attempt_error: string | null;
  last_success_at: string | null;
  last_skipped_locked_at: string | null;
}
interface MockSources { sources: MockSource[] }

function source(
  key: MockSource['key'], overrides: Partial<MockSource> = {},
): MockSource {
  return {
    key, scheduler_enabled: key === 'outages', interval_seconds: 300, version: 1,
    last_attempt_at: '2026-11-13T12:00:00Z', last_attempt_outcome: 'ok',
    last_attempt_error: null, last_success_at: '2026-11-13T12:00:00Z',
    last_skipped_locked_at: null, ...overrides,
  };
}

function sources(overrides: {
  outages?: Partial<MockSource>; scheduled?: Partial<MockSource>;
} = {}): MockSources {
  return {
    sources: [
      source('outages', overrides.outages),
      source('scheduled_works', overrides.scheduled),
    ],
  };
}

interface MockOptions {
  role?: 'user' | 'admin' | 'none';
  initial?: MockSources;
  getStatus?: number;
  conflictOnce?: boolean;
  busyOnce?: boolean;
  outcome?: string;
  delayMs?: number;
  onPatch?: (body: Record<string, unknown>, headers: Record<string, string>) => void;
  onPost?: (headers: Record<string, string>) => void;
}

async function mockApi(page: Page, options: MockOptions = {}) {
  const role = options.role ?? 'admin';
  const current = options.initial ?? sources();
  let patchCalls = 0;
  let postCalls = 0;
  let getCalls = 0;

  await page.route('**/api/**', async (route: Route) => {
    const request = route.request();
    const url = new URL(request.url());
    const headers = request.headers() as Record<string, string>;
    if (url.pathname === '/api/session') {
      if (role === 'none') {
        await route.fulfill({ status: 401, json: { detail: 'Sin sesión' } });
      } else {
        await route.fulfill({ status: 200, json: {
          account: { id: 'synthetic', username: 'qa-synthetic', role },
          csrf_token: 'synthetic-csrf',
        } });
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
    if (url.pathname === '/api/admin/sources' && request.method() === 'GET') {
      getCalls += 1;
      if (options.getStatus && options.getStatus !== 200) {
        await route.fulfill({ status: options.getStatus, json: { detail: 'No autorizado' } });
      } else {
        await route.fulfill({ status: 200, json: current });
      }
      return;
    }
    const interval = url.pathname.match(/^\/api\/admin\/sources\/([^/]+)\/interval$/);
    if (interval && request.method() === 'PATCH') {
      patchCalls += 1;
      const raw = request.postDataJSON();
      const body = typeof raw === 'object' && raw !== null
        ? raw as Record<string, unknown> : {};
      options.onPatch?.(body, headers);
      const key = interval[1] as MockSource['key'];
      if (options.conflictOnce && patchCalls === 1) {
        await route.fulfill({ status: 409, json: { detail: 'conflict', code: 'VERSION_CONFLICT' } });
        return;
      }
      const target = current.sources.find(item => item.key === key);
      if (!target) { await route.fulfill({ status: 404, json: { detail: 'missing' } }); return; }
      target.interval_seconds = typeof body.interval_seconds === 'number'
        ? body.interval_seconds : target.interval_seconds;
      target.version += 1;
      await route.fulfill({ status: 200, json: {
        key, interval_seconds: target.interval_seconds, version: target.version,
      } });
      return;
    }
    const refresh = url.pathname.match(/^\/api\/admin\/sources\/([^/]+)\/refresh$/);
    if (refresh && request.method() === 'POST') {
      postCalls += 1;
      options.onPost?.(headers);
      const key = refresh[1] as MockSource['key'];
      if (options.busyOnce && postCalls === 1) {
        await route.fulfill({ status: 409, json: { detail: 'busy', code: 'SOURCE_BUSY' } });
        return;
      }
      if (options.delayMs) {
        await new Promise(resolve => setTimeout(resolve, options.delayMs));
      }
      const outcome = options.outcome ?? 'ok';
      const target = current.sources.find(item => item.key === key);
      if (target) {
        target.last_attempt_at = '2026-11-13T12:00:00Z';
        target.last_attempt_outcome = outcome;
        target.last_attempt_error =
          outcome === 'ok' || outcome === 'not_modified' ? null : 'EnreTimeout';
        if (outcome === 'ok' || outcome === 'not_modified') {
          target.last_success_at = '2026-11-13T12:00:00Z';
        }
      }
      try {
        await route.fulfill({ status: 200, json: {
          key, outcome, http_status: 200,
          detail_code: outcome === 'timeout' ? 'EnreTimeout' : null,
          started_at: '2026-11-13T12:00:00Z', finished_at: '2026-11-13T12:00:01Z',
        } });
      } catch {
        // The browser may have already aborted the synchronous retry at its deadline.
      }
      return;
    }
    await route.fulfill({ status: 404, json: { detail: 'not mocked' } });
  });
  return { patchCalls: () => patchCalls, postCalls: () => postCalls, getCalls: () => getCalls };
}

async function openAdmin(page: Page): Promise<void> {
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Administración' })).toBeVisible();
  await page.getByRole('button', { name: 'Administración' }).click();
  await expect(page.getByRole('heading', { name: 'Administración de fuentes' })).toBeVisible();
}

test('admin sees both ENRE cards with real status fields', async ({ page }) => {
  await mockApi(page);
  await openAdmin(page);
  await expect(page.getByRole('heading', { name: 'ENRE — Cortes actuales' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'ENRE — Trabajos programados' })).toBeVisible();
  await expect(page.getByText('Último intento').first()).toBeVisible();
  await expect(page.getByText('Última actualización exitosa').first()).toBeVisible();
  await expect(page.getByText('Intervalo actual').first()).toBeVisible();
  await expect(page.getByText('13/11/2026 09:00').first()).toBeVisible();
  await expect(page.locator('#interval-outages')).toHaveValue('300');
  await expect(page.locator('#interval-scheduled_works')).toHaveValue('300');
  await expect(page.getByText(/configuración, no garantiza/).first()).toBeVisible();
});

test('non-admin and unauthenticated visitors cannot see the admin navigation', async ({ page }) => {
  await mockApi(page, { role: 'user' });
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Administración' })).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Domicilios' })).toBeVisible();

  await page.unroute('**/api/**');
  await mockApi(page, { role: 'none' });
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Administración' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Ingresar' })).toBeVisible();
});

test('interval change succeeds, reports the result and survives a reload', async ({ page }) => {
  const patchBodies: Record<string, unknown>[] = [];
  const patchHeaders: Record<string, string>[] = [];
  await mockApi(page, {
    onPatch: (body, headers) => { patchBodies.push(body); patchHeaders.push(headers); },
  });
  await openAdmin(page);
  await page.locator('#interval-outages').selectOption('600');
  await page.getByRole('button', { name: /Guardar intervalo/ }).first().click();
  await expect(page.getByText('Intervalo actualizado a 10 minutos.')).toBeVisible();
  await expect(page.locator('#interval-outages')).toHaveValue('600');
  expect(patchBodies).toEqual([{ interval_seconds: 600, version: 1 }]);
  expect(patchHeaders[0]?.['x-csrf-token']).toBe('synthetic-csrf');

  await page.reload();
  await openAdmin(page);
  await expect(page.locator('#interval-outages')).toHaveValue('600');
  await expect(page.getByText('10 minutos').first()).toBeVisible();
});

test('a stale version reports the conflict, reloads and does not auto-overwrite', async ({ page }) => {
  const calls = await mockApi(page, { conflictOnce: true });
  await openAdmin(page);
  await page.locator('#interval-outages').selectOption('900');
  await page.getByRole('button', { name: /Guardar intervalo/ }).first().click();
  await expect(page.getByText(/La configuración fue modificada por otro administrador/)).toBeVisible();
  await expect(page.locator('#interval-outages')).toHaveValue('300');
  expect(calls.patchCalls()).toBe(1);
  expect(calls.getCalls()).toBeGreaterThan(1);
});

test('a busy source reports 409, reloads the status and does not fake success', async ({ page }) => {
  let csrf = '';
  const calls = await mockApi(page, { busyOnce: true, onPost: headers => { csrf = headers['x-csrf-token'] ?? ''; } });
  await openAdmin(page);
  await page.getByRole('button', { name: /Actualizar ahora/ }).first().click();
  await expect(page.getByText(/La fuente ya se está actualizando/)).toBeVisible();
  expect(calls.postCalls()).toBe(1);
  expect(calls.getCalls()).toBeGreaterThan(1);
  expect(csrf).toBe('synthetic-csrf');
});

test('a successful retry shows the real outcome and refreshes the state', async ({ page }) => {
  const calls = await mockApi(page, { outcome: 'ok' });
  await openAdmin(page);
  await page.getByRole('button', { name: /Actualizar ahora/ }).first().click();
  await expect(page.getByText('Actualización completada: Actualización exitosa.')).toBeVisible();
  expect(calls.getCalls()).toBeGreaterThan(1);
  await expect(page.getByText('Actualización exitosa').first()).toBeVisible();
});

test('a failed retry outcome is shown as a failure, never as success', async ({ page }) => {
  await mockApi(page, { outcome: 'timeout' });
  await openAdmin(page);
  await page.getByRole('button', { name: /Actualizar ahora/ }).first().click();
  await expect(page.getByText(/La actualización no fue exitosa: Tiempo de espera agotado/)).toBeVisible();
  await expect(page.getByText('Actualización completada: Actualización exitosa.')).toHaveCount(0);
});

test('an unconfirmed retry timeout is reported and the real state is reloaded', async ({ page }) => {
  test.setTimeout(60000);
  const calls = await mockApi(page, { delayMs: 30000, outcome: 'ok' });
  await openAdmin(page);
  const retry = page.getByRole('button', { name: /Actualizar ahora/ }).first();
  await retry.click();
  await expect(retry).toBeDisabled();
  await expect(page.getByText(/No se pudo confirmar el resultado de la actualización/))
    .toBeVisible({ timeout: 40000 });
  await expect(page.getByText('Actualización completada: Actualización exitosa.')).toHaveCount(0);
  expect(calls.getCalls()).toBeGreaterThan(1);
  expect(calls.postCalls()).toBe(1);
});

test('backend denial is reported even when the frontend role is admin', async ({ page }) => {
  await mockApi(page, { getStatus: 403 });
  await openAdmin(page);
  await expect(page.getByText('No tenés autorización para administrar las fuentes.')).toBeVisible();
});
