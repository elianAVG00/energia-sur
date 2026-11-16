import { expect, test } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import { isDomicile } from '../src/diaryApi.ts';

test('public registration returns to login, creates an isolated account, and keeps credentials out of browser storage', async ({ page, browser }) => {
  const username = process.env.QA_USERNAME_REGISTERED
    ?? `qa${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;
  const password = process.env.QA_PASSWORD ?? 'Synthetic-E2E-password-2026!';
  await page.goto('/');
  await page.getByRole('button', { name: 'Crear cuenta (cambiar formulario)', exact: true }).click();
  const form = page.getByRole('form', { name: 'Crear cuenta', exact: true });
  await form.getByLabel('Usuario', { exact: true }).fill(username);
  await form.getByLabel('Contraseña', { exact: true }).fill(password);
  await form.getByLabel('Confirmar contraseña', { exact: true }).fill(password);

  const registrationRequest = page.waitForRequest(request => request.url().endsWith('/api/register'));
  const registrationResponse = page.waitForResponse(response =>
    response.url().endsWith('/api/register') && response.request().method() === 'POST');
  await form.getByRole('button', { name: 'Crear cuenta', exact: true }).click();
  const request = await registrationRequest;
  const headers = await request.allHeaders();
  expect(headers['x-csrf-token']).toBeUndefined();
  expect(headers.origin).toBe(new URL(page.url()).origin);
  const response = await registrationResponse;
  expect(response.status()).toBe(201);
  const body: unknown = await response.json();
  expect(body).toEqual({ id: expect.any(String), username, role: 'user' });
  expect(await page.request.get('/api/session').then(result => result.status())).toBe(401);

  await expect(page.getByRole('status')).toContainText('La cuenta se creó correctamente');
  await expect(page.getByLabel('Usuario', { exact: true })).toHaveValue(username);
  await expect(page.getByLabel('Contraseña', { exact: true })).toHaveValue('');
  const storage = await page.evaluate(() => ({
    local: Object.keys(localStorage),
    session: Object.keys(sessionStorage),
  }));
  expect(storage.local).toEqual([]);
  expect(storage.session).toEqual([]);

  await page.getByLabel('Contraseña', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Ingresar', exact: true }).last().click();
  await expect(page.getByRole('heading', { name: 'Domicilios', exact: true })).toBeVisible();

  const address = `Domicilio de cuenta registrada ${username}`;
  await page.getByLabel('Domicilio nuevo').fill(address);
  const domicileResponse = page.waitForResponse(response =>
    response.url().endsWith('/api/domiciles') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Registrar domicilio', exact: true }).click();
  const createdDomicile: unknown = await (await domicileResponse).json();
  if (!isDomicile(createdDomicile)) throw new Error('Invalid domicile response');
  await mkdir('/tmp/cu09-artifacts', { recursive: true });
  await writeFile('/tmp/cu09-artifacts/registration-state.json', JSON.stringify({
    username,
    domicile: createdDomicile.id,
  }));
  const ownHomesResponse = await page.request.get('/api/domiciles');
  expect(ownHomesResponse.status()).toBe(200);
  const ownHomes: unknown = await ownHomesResponse.json();
  expect(Array.isArray(ownHomes) && ownHomes.some(
    (home: unknown) => isDomicile(home) && home.id === createdDomicile.id,
  )).toBe(true);

  const noCsrf = await page.request.post('/api/domiciles', {
    headers: { Origin: new URL(page.url()).origin },
    data: { display_address: `Debe rechazarse ${username}` },
  });
  expect(noCsrf.status()).toBe(403);

  const other = await browser.newContext({ baseURL: new URL(page.url()).origin });
  try {
    const otherPage = await other.newPage();
    await otherPage.goto('/');
    await otherPage.getByLabel('Usuario', { exact: true }).fill(process.env.QA_USERNAME_B ?? '');
    await otherPage.getByLabel('Contraseña', { exact: true }).fill(process.env.QA_PASSWORD ?? '');
    await otherPage.getByRole('button', { name: 'Ingresar', exact: true }).click();
    await expect(otherPage.getByRole('heading', { name: 'Domicilios', exact: true })).toBeVisible();
    await expect(otherPage.getByLabel('Domicilio seleccionado').locator('option').filter({
      hasText: address,
    })).toHaveCount(0);
    const foreignHomesResponse = await other.request.get('/api/domiciles');
    expect(foreignHomesResponse.status()).toBe(200);
    const foreignHomes: unknown = await foreignHomesResponse.json();
    expect(Array.isArray(foreignHomes) && foreignHomes.some(
      (home: unknown) => isDomicile(home) && home.id === createdDomicile.id,
    )).toBe(false);
  } finally {
    await other.close();
  }

  await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Ingresar', exact: true })).toBeEnabled();
  expect(await page.request.get('/api/session').then(result => result.status())).toBe(401);
});

test('registration presents duplicate and rate-limit errors and clears password fields', async ({ page }) => {
  let attempts = 0;
  await page.route('**/api/**', async route => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.pathname === '/api/session') {
      await route.fulfill({ status: 401, json: { detail: 'Sin sesión' } });
    } else if (url.pathname === '/api/register' && request.method() === 'POST') {
      attempts++;
      if (attempts === 1) {
        await route.fulfill({ status: 409, json: { detail: 'Nombre no disponible' } });
      } else {
        await route.fulfill({ status: 429, headers: { 'retry-after': '15' }, json: { detail: 'Límite alcanzado' } });
      }
    } else {
      await route.fulfill({ status: 404, json: { detail: 'No encontrado' } });
    }
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Crear cuenta (cambiar formulario)', exact: true }).click();
  const form = page.getByRole('form', { name: 'Crear cuenta', exact: true });
  await form.getByLabel('Usuario', { exact: true }).fill('duplicate_user');
  await form.getByLabel('Contraseña', { exact: true }).fill('synthetic password');
  await form.getByLabel('Confirmar contraseña', { exact: true }).fill('synthetic password');
  await form.getByRole('button', { name: 'Crear cuenta', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Ese usuario ya está registrado');
  await expect(form.getByLabel('Contraseña', { exact: true })).toHaveValue('');
  await expect(form.getByLabel('Confirmar contraseña', { exact: true })).toHaveValue('');
  await expect(form.getByLabel('Usuario', { exact: true })).toHaveValue('duplicate_user');

  await form.getByLabel('Contraseña', { exact: true }).fill('synthetic password');
  await form.getByLabel('Confirmar contraseña', { exact: true }).fill('synthetic password');
  await form.getByRole('button', { name: 'Crear cuenta', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Esperá 15 segundos');
  await expect(form.getByLabel('Contraseña', { exact: true })).toHaveValue('');
  await expect(form.getByLabel('Confirmar contraseña', { exact: true })).toHaveValue('');
  expect(attempts).toBe(2);
});
