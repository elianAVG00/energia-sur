import { expect, test } from '@playwright/test';

const baseURL = process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5173';
const adminUser = process.env.QA_USERNAME_ADMIN ?? '';
const normalUser = process.env.QA_USERNAME_USER ?? '';
const password = process.env.QA_PASSWORD ?? '';

test.describe('CU10 real backend', () => {
  test.skip(!adminUser || !normalUser || !password, 'Needs synthetic QA admin and user');

  test('admin status, interval conflict, CSRF and non-admin denial', async ({ page, playwright }) => {
    const login = await page.request.post(`${baseURL}/api/login`, {
      data: { username: adminUser, password },
      headers: { Origin: baseURL },
    });
    expect(login.status()).toBe(200);
    const session = await login.json() as { csrf_token: string };

    await page.goto('/');
    await expect(page.getByRole('button', { name: 'Administración' })).toBeVisible();
    await page.getByRole('button', { name: 'Administración' }).click();
    await expect(page.getByRole('heading', { name: 'ENRE — Cortes actuales' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'ENRE — Trabajos programados' })).toBeVisible();

    const before = await page.request.get(`${baseURL}/api/admin/sources`);
    expect(before.status()).toBe(200);
    const sources = await before.json() as {
      sources: Array<{ key: string; interval_seconds: number; version: number }>;
    };
    const outages = sources.sources.find(source => source.key === 'outages');
    expect(outages).toBeTruthy();
    if (!outages) return;

    await page.locator('#interval-outages').selectOption('600');
    await page.getByRole('button', { name: /Guardar intervalo/ }).first().click();
    await expect(page.getByText(/Intervalo actualizado/)).toBeVisible();

    const stale = await page.request.patch(`${baseURL}/api/admin/sources/outages/interval`, {
      data: { interval_seconds: 900, version: outages.version },
      headers: { Origin: baseURL, 'X-CSRF-Token': session.csrf_token },
    });
    expect(stale.status()).toBe(409);
    expect((await stale.json() as { code?: string }).code).toBe('VERSION_CONFLICT');

    const noCsrf = await page.request.patch(`${baseURL}/api/admin/sources/outages/interval`, {
      data: { interval_seconds: 300, version: outages.version + 1 },
      headers: { Origin: baseURL },
    });
    expect(noCsrf.status()).toBe(403);

    const restore = await page.request.patch(`${baseURL}/api/admin/sources/outages/interval`, {
      data: { interval_seconds: outages.interval_seconds, version: outages.version + 1 },
      headers: { Origin: baseURL, 'X-CSRF-Token': session.csrf_token },
    });
    expect(restore.status()).toBe(200);

    const userContext = await playwright.request.newContext({ baseURL });
    try {
      const userLogin = await userContext.post('/api/login', {
        data: { username: normalUser, password },
        headers: { Origin: baseURL },
      });
      expect(userLogin.status()).toBe(200);
      const denied = await userContext.get('/api/admin/sources');
      expect(denied.status()).toBe(403);
    } finally {
      await userContext.dispose();
    }
  });
});
