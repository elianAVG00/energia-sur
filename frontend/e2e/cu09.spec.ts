import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';
import { writeFile } from 'node:fs/promises';
import { isCut, isDomicile, isSession } from '../src/diaryApi.ts';

function setting(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing synthetic QA setting ${name}`);
  return value;
}

async function login(page: Page, username: string) {
  await page.goto('/');
  await expect(page.locator('[data-chat-mount]')).toHaveCount(1);
  await expect(page.locator('[data-chat-mount]').getByRole('button')).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Ingresar', exact: true })).toBeEnabled();
  await page.getByLabel('Usuario', { exact: true }).fill(username);
  await page.getByLabel('Contraseña', { exact: true }).fill(setting('QA_PASSWORD'));
  await page.getByRole('button', { name: 'Ingresar', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Domicilios', exact: true })).toBeVisible();
  await expect(page.locator('[data-chat-mount]')).toHaveCount(1);
}

async function createCut(page: Page, start: string, end: string, note = '') {
  const form = page.getByRole('form', { name: 'Registrar corte', exact: true });
  await form.getByLabel('Inicio', { exact: true }).fill(start);
  await form.getByLabel('Fin (opcional si está en curso)', { exact: true }).fill(end);
  await form.getByRole('textbox', { name: 'Observaciones', exact: true }).fill(note);
  await form.getByLabel('Número de reclamo', { exact: true }).fill(note ? 'TEST-001' : '');
  await form.getByRole('button', { name: 'Guardar corte', exact: true }).click();
  await expect(page.getByText('Operación guardada.', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Guardar corte', exact: true })).toBeEnabled();
}

async function query(page: Page, expected: string, start = '2026-11-01T00:00', end = '2026-11-02T00:00') {
  await page.getByLabel('Desde', { exact: true }).fill(start);
  await page.getByLabel('Hasta', { exact: true }).fill(end);
  await page.getByRole('button', { name: 'Consultar resumen', exact: true }).click();
  await expect(page.getByRole('heading', { name: `Total sin servicio: ${expected}`, exact: true })).toBeVisible();
}

test('real private diary: registration, overlaps, PDF, correction, closure and two accounts', async ({ page, browser }) => {
  const chatRequests: string[] = [];
  page.on('request', request => {
    if (/\/(chat|messages|stream)(\/|\?|$)|api\.openai\.com/i.test(request.url())) chatRequests.push('unexpected chat request');
  });
  await login(page, setting('QA_USERNAME_A'));
  await page.getByLabel('Domicilio nuevo', { exact: true }).fill('Domicilio sintético Álvarez QA');
  const created = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/api/domiciles'));
  await page.getByRole('button', { name: 'Registrar domicilio', exact: true }).click();
  const domicileBody: unknown = await (await created).json();
  if (!isDomicile(domicileBody)) throw new Error('Invalid domicile DTO');
  const domicile = domicileBody.id;
  await expect(page.getByRole('form', { name: 'Registrar corte', exact: true })).toBeVisible();
  await createCut(page, '2026-11-01T10:00', '2026-11-01T12:00', 'Observación sintética de energía');
  await createCut(page, '2026-11-01T11:00', '2026-11-01T13:00');
  await expect(page.locator('tbody tr')).toHaveCount(2);
  await query(page, '3 h 0 min');
  // Narrow and desktop layout checks share this single workflow/browser pass.
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole('button', { name: 'Descargar PDF', exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Descargar PDF', exact: true }).focus();
  await expect(page.getByRole('button', { name: 'Descargar PDF', exact: true })).toBeFocused();
  await page.setViewportSize({ width: 1280, height: 900 });
  const closedDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Descargar PDF', exact: true }).click();
  await (await closedDownload).saveAs('/tmp/cu09-artifacts/closed.pdf');

  await createCut(page, '2026-11-01T14:00', '');
  await query(page, '13 h 0 min');
  const ongoingDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Descargar PDF', exact: true }).click();
  await (await ongoingDownload).saveAs('/tmp/cu09-artifacts/ongoing.pdf');
  await page.getByRole('button', { name: 'Cerrar corte', exact: true }).click();
  await page.getByLabel('Fecha de cierre', { exact: true }).fill('2026-11-01T15:00');
  await page.getByRole('button', { name: 'Confirmar cierre', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Confirmar cierre', exact: true })).toHaveCount(0);
  await query(page, '4 h 0 min');

  const row = page.locator('tbody tr').filter({ hasText: '01/11/2026 11:00' });
  await row.getByRole('button', { name: 'Corregir', exact: true }).click();
  const editor = page.getByRole('form', { name: 'Corregir corte', exact: true });
  const ownerSession: unknown = await (await page.request.get('/api/session')).json();
  if (!isSession(ownerSession)) throw new Error('Invalid owner session');
  const ownerHeaders = { Origin: setting('E2E_BASE_URL'), 'X-CSRF-Token': ownerSession.csrf_token };
  const beforeConflict: unknown = await (await page.request.get(`/api/domiciles/${domicile}/interruptions`)).json();
  if (!Array.isArray(beforeConflict)) throw new Error('Missing own records');
  const concurrentCut: unknown = beforeConflict.find((value: unknown) => isCut(value) && value.start_at.startsWith('2026-11-01T11:00'));
  if (!isCut(concurrentCut)) throw new Error('Missing concurrent record');
  const concurrentResponse = await page.request.patch(`/api/interruptions/${concurrentCut.id}`, {
    headers: ownerHeaders, data: { start_at: concurrentCut.start_at, end_at: concurrentCut.end_at,
      observations: 'Otro escritor', complaint_number: concurrentCut.complaint_number, version: concurrentCut.version },
  });
  expect(concurrentResponse.status()).toBe(200);
  await editor.getByLabel('Inicio', { exact: true }).fill('2026-11-01T11:30');
  await editor.getByLabel('Fin (opcional si está en curso)', { exact: true }).fill('2026-11-01T13:30');
  await editor.getByRole('button', { name: 'Guardar corrección', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Descartar borrador y recargar');
  await page.getByRole('button', { name: 'Descartar borrador y recargar', exact: true }).click();
  await expect(editor.getByRole('textbox', { name: 'Observaciones', exact: true })).toHaveValue('Otro escritor');
  // Reopening the same persisted version must reset local state as well.
  await editor.getByRole('textbox', { name: 'Observaciones', exact: true }).fill('Borrador que no debe persistir');
  await row.getByRole('button', { name: 'Corregir', exact: true }).click();
  await expect(editor.getByRole('textbox', { name: 'Observaciones', exact: true })).toHaveValue('Otro escritor');
  await expect(page.getByRole('button', { name: 'Descartar borrador y recargar', exact: true })).toHaveCount(0);
  await editor.getByLabel('Inicio', { exact: true }).fill('2026-11-01T11:30');
  await editor.getByLabel('Fin (opcional si está en curso)', { exact: true }).fill('2026-11-01T13:30');
  await editor.getByRole('button', { name: 'Guardar corrección', exact: true }).click();
  await expect(editor).toHaveCount(0);
  await query(page, '4 h 30 min');
  await page.reload();
  await expect(page.locator('tbody tr')).toHaveCount(3);

  await query(page, '0 h 0 min', '2026-10-30T00:00', '2026-10-31T00:00');
  await expect(page.getByText('0 registros con duración dentro del período.', { exact: false })).toBeVisible();
  await expect(page.locator('tbody tr')).toHaveCount(3);

  const future = page.getByRole('form', { name: 'Registrar corte', exact: true });
  await future.getByLabel('Inicio', { exact: true }).fill('2999-11-01T10:00');
  await future.getByRole('button', { name: 'Guardar corte', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('future');
  await expect(page.locator('tbody tr')).toHaveCount(3);

  const other = await browser.newContext({ baseURL: setting('E2E_BASE_URL') });
  const otherPage = await other.newPage();
  await login(otherPage, setting('QA_USERNAME_B'));
  await expect(otherPage.getByText('Registrá un domicilio para empezar. No se necesita medidor.')).toBeVisible();
  await expect(otherPage.getByRole('form', { name: 'Registrar corte', exact: true })).toHaveCount(0);
  await otherPage.getByLabel('Domicilio nuevo', { exact: true }).fill('Domicilio exclusivo B QA');
  await otherPage.getByRole('button', { name: 'Registrar domicilio', exact: true }).click();
  await expect(otherPage.getByRole('form', { name: 'Registrar corte', exact: true })).toBeVisible();
  await expect(otherPage.getByLabel('Domicilio seleccionado').locator('option')).toHaveText(['Elegí un domicilio', 'Domicilio exclusivo B QA']);
  await expect(page.getByLabel('Domicilio seleccionado').locator('option')).toHaveText(['Elegí un domicilio', 'Domicilio sintético Álvarez QA']);
  const session: unknown = await (await other.request.get('/api/session')).json();
  if (!isSession(session)) throw new Error('Invalid session DTO');
  const headers = { Origin: setting('E2E_BASE_URL'), 'X-CSRF-Token': session.csrf_token };
  const cutsResponse = await page.request.get(`/api/domiciles/${domicile}/interruptions`);
  const cuts: unknown = await cutsResponse.json();
  if (!Array.isArray(cuts)) throw new Error('Missing own cuts');
  const firstCut: unknown = cuts[0];
  if (!isCut(firstCut)) throw new Error('Missing own cut');
  const cutId = firstCut.id;
  const foreignRequests = [
    await other.request.get(`/api/domiciles/${domicile}/interruptions`),
    await other.request.post(`/api/domiciles/${domicile}/interruptions`, { headers, data: { start_at: '2026-11-01T10:00', end_at: null } }),
    await other.request.patch(`/api/interruptions/${cutId}`, { headers, data: { start_at: '2026-11-01T10:00', end_at: '2026-11-01T11:00', version: 1 } }),
    await other.request.post(`/api/interruptions/${cutId}/close`, { headers, data: { end_at: '2026-11-01T11:00', version: 1 } }),
    await other.request.get(`/api/domiciles/${domicile}/summary?period_start=2026-11-01T00:00&period_end=2026-11-02T00:00`),
    await other.request.get(`/api/domiciles/${domicile}/report.pdf?period_start=2026-11-01T00:00&period_end=2026-11-02T00:00`),
  ];
  for (const response of foreignRequests) expect(response.status()).toBe(404);
  const ownerAfter = await page.request.get(`/api/domiciles/${domicile}/interruptions`);
  expect(await ownerAfter.json()).toEqual(cuts);
  await writeFile('/tmp/cu09-artifacts/state.json', JSON.stringify({ domicile, cuts }));
  await future.getByLabel('Inicio', { exact: true }).fill('2026-11-01T16:00');
  await page.getByLabel('Domicilio nuevo', { exact: true }).fill('Segundo domicilio sintético QA');
  await page.getByRole('button', { name: 'Registrar domicilio', exact: true }).click();
  await expect(page.getByText('No hay cortes registrados.', { exact: true })).toBeVisible();
  await expect(page.getByRole('form', { name: 'Registrar corte', exact: true }).getByLabel('Inicio', { exact: true })).toHaveValue('');
  await query(page, '0 h 0 min');
  await expect(page.locator('[data-chat-mount]')).toHaveCount(1);
  await other.close();
  await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Ingresar', exact: true })).toBeEnabled();
  await expect(page.locator('tbody tr')).toHaveCount(0);
  await expect(page.locator('[data-chat-mount]')).toHaveCount(1);
  await expect(page.locator('[data-chat-mount]').getByRole('button')).toBeDisabled();
  expect(chatRequests).toEqual([]);
  expect((await page.request.get('/api/session')).status()).toBe(401);
});
