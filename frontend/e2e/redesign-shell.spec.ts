import { expect, test } from '@playwright/test';
import type { Page, Route } from '@playwright/test';

interface MockOptions {
  role?: 'admin' | 'user';
  logoutStatus?: number;
}

async function mockApi(page: Page, options: MockOptions = {}): Promise<string[]> {
  const requests: string[] = [];
  await page.route('**/api/**', async (route: Route) => {
    const request = route.request();
    const url = new URL(request.url());
    requests.push(url.pathname);
    if (url.pathname === '/api/session') {
      if (options.role) {
        await route.fulfill({ status: 200, json: {
          account: {
            id: `synthetic-${options.role}`,
            username: 'qa-synthetic',
            ...(options.role === 'admin' ? { role: 'admin' } : {}),
          },
          csrf_token: 'synthetic-csrf',
        } });
      } else {
        await route.fulfill({ status: 401, json: { detail: 'Sin sesión' } });
      }
      return;
    }
    if (url.pathname === '/api/logout') {
      await route.fulfill({ status: options.logoutStatus ?? 204 });
      return;
    }
    if (url.pathname === '/api/domiciles') {
      await route.fulfill({ status: 200, json: [] });
      return;
    }
    await route.fulfill({ status: 404, json: { detail: 'not mocked' } });
  });
  return requests;
}

async function openCortes(page: Page): Promise<void> {
  await page.goto('/');
  await page.getByRole('button', { name: 'Cortes' }).click();
  await expect(page.getByRole('heading', { name: 'Cortes eléctricos', exact: true })).toBeVisible();
}

test('shared shell exposes header, main and footer landmarks with one heading', async ({ page }) => {
  await mockApi(page);
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Diario de interrupciones', exact: true })).toBeVisible();

  await expect(page.getByRole('banner')).toHaveCount(1);
  await expect(page.getByRole('banner')).toContainText('Energía Sur');
  await expect(page.getByRole('main')).toHaveCount(1);
  await expect(page.getByRole('contentinfo')).toHaveCount(1);
  await expect(page.locator('h1')).toHaveCount(1);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Diario de interrupciones');
  await expect(page.getByRole('button', { name: 'Cerrar sesión', exact: true })).toHaveCount(0);

  const footer = page.getByRole('contentinfo');
  await expect(footer).toContainText('Portal ciudadano para usuarios de Edesur en Zona Sur');
  await expect(footer).toContainText('datos públicos del ENRE');
  await expect(footer).not.toContainText('API');
  await expect(footer).not.toContainText('Entorno de desarrollo');
  await expect(footer.getByRole('button')).toHaveCount(0);

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
});

test('active navigation section is announced and administration stays admin-only', async ({ page }) => {
  await mockApi(page, { role: 'user' });
  await openCortes(page);

  await expect(page.getByRole('navigation', { name: 'Secciones' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Cortes', exact: true })).toHaveAttribute('aria-current', 'page');
  await expect(page.locator('[aria-current="page"]')).toHaveCount(1);
  await expect(page.getByRole('button', { name: 'Administración', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Cerrar sesión', exact: true })).toHaveCount(1);
  await expect(page.locator('h1')).toHaveCount(1);

  await page.getByRole('button', { name: 'Trabajos', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Trabajos', exact: true })).toHaveAttribute('aria-current', 'page');
  await expect(page.locator('[aria-current="page"]')).toHaveCount(1);
  await expect(page.getByRole('heading', { name: 'Trabajos programados', exact: true })).toBeVisible();
  await expect(page.locator('h1')).toHaveCount(1);
});

test('administrator sees the administration section and the nav stays reachable on mobile', async ({ page }) => {
  await mockApi(page, { role: 'admin' });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');

  const admin = page.getByRole('button', { name: 'Administración', exact: true });
  await expect(admin).toHaveCount(1);
  await expect(admin).toBeVisible();
  await admin.click();
  await expect(admin).toHaveAttribute('aria-current', 'page');
  await expect(page.getByRole('heading', { name: 'Administración de fuentes', exact: true })).toBeVisible();
  await expect(page.locator('h1')).toHaveCount(1);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow, 'no horizontal overflow at 390px').toBe(0);
});

test('signed-in users have exactly one logout control that posts the revocation', async ({ page }) => {
  const requests = await mockApi(page, { role: 'user' });
  await page.goto('/');
  await expect(page.getByText('Cuenta: qa-synthetic')).toBeVisible();

  const logout = page.getByRole('button', { name: 'Cerrar sesión', exact: true });
  await expect(logout).toHaveCount(1);
  const revocation = page.waitForRequest(request =>
    new URL(request.url()).pathname === '/api/logout' && request.method() === 'POST');
  await logout.click();
  await revocation;
  await expect(page.getByRole('heading', { name: 'Ingresar', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Cerrar sesión', exact: true })).toHaveCount(0);
  await expect.poll(() => requests.filter(path => path === '/api/logout')).toHaveLength(1);
});

test('failed logout keeps its feedback visible outside the account view', async ({ page }) => {
  await mockApi(page, { role: 'user', logoutStatus: 500 });
  await openCortes(page);

  await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'No se confirmó el cierre de sesión' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Cortes eléctricos', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Cerrar sesión', exact: true })).toHaveCount(0);

  await page.getByRole('button', { name: 'Trabajos', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Trabajos programados', exact: true })).toBeVisible();
  await expect(page.getByRole('alert').filter({ hasText: 'No se confirmó el cierre de sesión' })).toHaveCount(0);
});

test('keyboard users can skip repeated navigation and operate the nav', async ({ page }) => {
  await mockApi(page);
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Diario de interrupciones', exact: true })).toBeVisible();

  await page.keyboard.press('Tab');
  const skip = page.getByRole('link', { name: 'Saltar al contenido' });
  await expect(skip).toBeFocused();
  await expect(skip).toBeVisible();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/#contenido$/);
  await expect(page.getByRole('main')).toBeFocused();

  await page.goto('/');
  await page.keyboard.press('Tab');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('button', { name: 'Cortes', exact: true })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'Cortes eléctricos', exact: true })).toBeVisible();
});

test('shell keeps one chat mount, no health request and no horizontal overflow', async ({ page }) => {
  const requests = await mockApi(page);
  await openCortes(page);

  await expect(page.locator('[data-chat-mount="cu03"]')).toHaveCount(1);
  expect(requests.filter(path => path === '/api/health')).toEqual([]);

  for (const width of [390, 820, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, `no horizontal overflow at ${width}px`).toBe(0);
    await expect(page.getByRole('button', { name: 'Cortes', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Mi cuenta', exact: true })).toBeVisible();
  }
});
