import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';
import { isCut, isDomicile, isSession, isSummary } from '../src/diaryApi.ts';
import { isMeter } from '../src/features/domiciles/api.ts';

/** The same meter number also appears in the CU05 reading <select>; assert only the list. */
function registeredMeters(page: Page) {
  return page.getByRole('list', { name: 'Medidores registrados' });
}

function setting(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing synthetic QA setting ${name}`);
  return value;
}

test('real CU04 management preserves diary draft and distinguishes conflicts', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Usuario', { exact: true }).fill(setting('QA_USERNAME_A'));
  await page.getByLabel('Contraseña', { exact: true }).fill(setting('QA_PASSWORD'));
  await page.getByRole('button', { name: 'Ingresar', exact: true }).click();
  const suffix = String(Date.now());
  const address = `Domicilio sintético CU04 ${suffix}`;
  await page.getByLabel('Domicilio nuevo').fill(address);
  const created = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/api/domiciles'));
  await page.getByRole('button', { name: 'Registrar domicilio', exact: true }).click();
  const body: unknown = await (await created).json();
  if (!isDomicile(body)) throw new Error('Invalid domicile DTO');
  const diary = page.getByRole('form', { name: 'Registrar corte' });
  await diary.getByLabel('Observaciones').fill('Borrador sintético');
  await page.getByRole('button', { name: 'Corregir domicilio', exact: true }).click();
  const addressForm = page.getByRole('form', { name: 'Corregir domicilio' });
  await addressForm.getByLabel('Dirección').fill(`${address} corregido`);
  await addressForm.getByRole('button', { name: 'Guardar domicilio' }).click();
  await expect(page.getByLabel('Domicilio seleccionado')).toContainText(`${address} corregido`);
  await expect(diary.getByLabel('Observaciones')).toHaveValue('Borrador sintético');

  const number = `QA-${suffix}`;
  const form = page.getByRole('form', { name: 'Registrar medidor' });
  await form.getByLabel('Número de medidor').fill(number);
  const meterResponse = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith(`/api/domiciles/${body.id}/meters`));
  await form.getByRole('button', { name: 'Registrar medidor' }).click();
  const meterBody: unknown = await (await meterResponse).json();
  if (!isMeter(meterBody)) throw new Error('Invalid meter DTO');
  await expect(registeredMeters(page).getByText(number, { exact: true })).toBeVisible();
  await form.getByLabel('Número de medidor').fill(number);
  await form.getByRole('button', { name: 'Registrar medidor' }).click();
  await expect(page.getByRole('alert')).toContainText('ya está registrado');

  await page.getByRole('button', { name: 'Corregir medidor', exact: true }).click();
  const editor = page.getByRole('form', { name: 'Corregir medidor' });
  const session: unknown = await (await page.request.get('/api/session')).json();
  if (!isSession(session)) throw new Error('Invalid session DTO');
  const concurrent = await page.request.patch(`/api/domiciles/${body.id}/meters/${meterBody.id}`, {
    headers: { Origin: setting('E2E_BASE_URL'), 'X-CSRF-Token': session.csrf_token },
    data: { meter_number: number, alias: 'Otro escritor', version: meterBody.version },
  });
  expect(concurrent.status()).toBe(200);
  await editor.getByLabel('Alias (opcional)').fill('Borrador anterior');
  await editor.getByRole('button', { name: 'Guardar medidor' }).click();
  await expect(page.getByRole('button', { name: 'Descartar borrador y recargar administración' })).toBeVisible();
  await page.getByRole('button', { name: 'Descartar borrador y recargar administración' }).click();
  await expect(registeredMeters(page).getByText(`${number} — Otro escritor`, { exact: true })).toBeVisible();
  await expect(diary.getByLabel('Observaciones')).toHaveValue('Borrador sintético');
});

test('real correction retains an existing cut and total and exports the corrected address', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Usuario', { exact: true }).fill(setting('QA_USERNAME_A'));
  await page.getByLabel('Contraseña', { exact: true }).fill(setting('QA_PASSWORD'));
  await page.getByRole('button', { name: 'Ingresar', exact: true }).click();
  const oldAddress = 'Domicilio sintetico PDF CU04 anterior';
  const newAddress = 'Domicilio sintetico PDF CU04 corregido';
  await page.getByLabel('Domicilio nuevo').fill(oldAddress);
  const createdHome = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/api/domiciles'));
  await page.getByRole('button', { name: 'Registrar domicilio', exact: true }).click();
  const home: unknown = await (await createdHome).json();
  if (!isDomicile(home)) throw new Error('Invalid domicile DTO');
  const form = page.getByRole('form', { name: 'Registrar corte' });
  await form.getByLabel('Inicio', { exact: true }).fill('2026-11-01T10:00');
  await form.getByLabel('Fin (opcional si está en curso)', { exact: true }).fill('2026-11-01T12:00');
  const createdCut = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith(`/api/domiciles/${home.id}/interruptions`));
  await form.getByRole('button', { name: 'Guardar corte' }).click();
  const cut: unknown = await (await createdCut).json();
  if (!isCut(cut)) throw new Error('Invalid cut DTO');
  expect(cut.domicile_id).toBe(home.id);
  const query = new URLSearchParams({ period_start: '2026-11-01T00:00', period_end: '2026-11-02T00:00' });
  const summaryPath = `/api/domiciles/${home.id}/summary?${query.toString()}`;
  const beforeResponse = await page.request.get(summaryPath);
  expect(beforeResponse.status()).toBe(200);
  const before: unknown = await beforeResponse.json();
  if (!isSummary(before)) throw new Error('Invalid initial summary DTO');
  expect(before.domicile.id).toBe(home.id);
  expect(before.domicile.display_address).toBe(oldAddress);
  expect(before.entries.map(entry => entry.id)).toEqual([cut.id]);
  expect(before.total_minutes).toBe(120);
  await page.getByRole('button', { name: 'Corregir domicilio', exact: true }).click();
  const addressForm = page.getByRole('form', { name: 'Corregir domicilio' });
  await addressForm.getByLabel('Dirección').fill(newAddress);
  await addressForm.getByRole('button', { name: 'Guardar domicilio' }).click();
  await expect(page.getByLabel('Domicilio seleccionado')).toContainText(newAddress);
  const afterResponse = await page.request.get(summaryPath);
  expect(afterResponse.status()).toBe(200);
  const after: unknown = await afterResponse.json();
  if (!isSummary(after)) throw new Error('Invalid corrected summary DTO');
  expect(after.domicile.id).toBe(home.id);
  expect(after.domicile.display_address).toBe(newAddress);
  expect(after.entries.map(entry => entry.id)).toEqual([cut.id]);
  expect(after.entries[0]?.domicile_id).toBe(home.id);
  expect(after.total_minutes).toBe(before.total_minutes);
  await page.getByLabel('Desde', { exact: true }).fill('2026-11-01T00:00');
  await page.getByLabel('Hasta', { exact: true }).fill('2026-11-02T00:00');
  await page.getByRole('button', { name: 'Consultar resumen', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Total sin servicio: 2 h 0 min', exact: true })).toBeVisible();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Descargar PDF', exact: true }).click();
  await (await download).saveAs('/tmp/cu09-artifacts/cu04-corrected.pdf');
});

test('rendered selection and account switches isolate delayed meter responses', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Usuario', { exact: true }).fill(setting('QA_USERNAME_A'));
  await page.getByLabel('Contraseña', { exact: true }).fill(setting('QA_PASSWORD'));
  await page.getByRole('button', { name: 'Ingresar', exact: true }).click();
  const suffix = String(Date.now());
  const firstAddress = `Domicilio sintético tardío A ${suffix}`;
  const secondAddress = `Domicilio sintético tardío B ${suffix}`;
  const firstNumber = `LATE-A-${suffix}`;
  const secondNumber = `LATE-B-${suffix}`;
  await page.getByLabel('Domicilio nuevo').fill(firstAddress);
  const created = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/api/domiciles'));
  await page.getByRole('button', { name: 'Registrar domicilio', exact: true }).click();
  const first: unknown = await (await created).json();
  if (!isDomicile(first)) throw new Error('Invalid domicile DTO');
  const meterForm = page.getByRole('form', { name: 'Registrar medidor' });
  await meterForm.getByLabel('Número de medidor').fill(firstNumber);
  await meterForm.getByRole('button', { name: 'Registrar medidor' }).click();
  await expect(registeredMeters(page).getByText(firstNumber, { exact: true })).toBeVisible();
  await page.getByLabel('Domicilio nuevo').fill(secondAddress);
  const createdSecond = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/api/domiciles'));
  await page.getByRole('button', { name: 'Registrar domicilio', exact: true }).click();
  const second: unknown = await (await createdSecond).json();
  if (!isDomicile(second)) throw new Error('Invalid second domicile DTO');
  await expect(page.getByLabel('Domicilio seleccionado')).toHaveValue(second.id);
  await meterForm.getByLabel('Número de medidor').fill(secondNumber);
  await meterForm.getByRole('button', { name: 'Registrar medidor' }).click();
  await expect(registeredMeters(page).getByText(secondNumber, { exact: true })).toBeVisible();

  function gate() {
    let start: () => void = () => { throw new Error('Gate not initialized'); };
    let release: () => void = () => { throw new Error('Gate not initialized'); };
    let complete: () => void = () => { throw new Error('Gate not initialized'); };
    const started = new Promise<void>(resolve => { start = resolve; });
    const wait = new Promise<void>(resolve => { release = resolve; });
    const finished = new Promise<void>(resolve => { complete = resolve; });
    return { start, release, complete, started, wait, finished };
  }
  const gates = [gate(), gate()];
  let requestIndex = 0;
  await page.route(`**/api/domiciles/${first.id}/meters`, async route => {
    const current = gates[requestIndex++];
    if (!current) { await route.continue(); return; }
    try {
      const response = await route.fetch();
      current.start();
      await current.wait;
      // The browser may already have canceled the intercepted request on unmount.
      await route.fulfill({ response }).catch(() => undefined);
    } finally { current.complete(); }
  });
  const firstGate = gates[0];
  const secondGate = gates[1];
  if (!firstGate || !secondGate) throw new Error('Missing response gates');
  try {
    await page.getByLabel('Domicilio seleccionado').selectOption({ label: firstAddress });
    await firstGate.started;
    await page.getByLabel('Domicilio seleccionado').selectOption({ label: secondAddress });
    await expect(registeredMeters(page).getByText(secondNumber, { exact: true })).toBeVisible();
    firstGate.release();
    await firstGate.finished;
    await expect(registeredMeters(page).getByText(firstNumber, { exact: true })).toHaveCount(0);
    await expect(registeredMeters(page).getByText(secondNumber, { exact: true })).toBeVisible();

    await page.getByLabel('Domicilio seleccionado').selectOption({ label: firstAddress });
    await secondGate.started;
    await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click();
    await page.getByLabel('Usuario', { exact: true }).fill(setting('QA_USERNAME_B'));
    await page.getByLabel('Contraseña', { exact: true }).fill(setting('QA_PASSWORD'));
    await page.getByRole('button', { name: 'Ingresar', exact: true }).click();
    await expect(page.getByText(`Cuenta: ${setting('QA_USERNAME_B')}`, { exact: true })).toBeVisible();
    secondGate.release();
    await secondGate.finished;
    await expect(registeredMeters(page).getByText(firstNumber, { exact: true })).toHaveCount(0);
    await expect(page.getByRole('option', { name: firstAddress, exact: true })).toHaveCount(0);
    await expect(registeredMeters(page).getByText(secondNumber, { exact: true })).toHaveCount(0);
  } finally {
    firstGate.release(); secondGate.release();
  }
});

test('address and meter drafts survive unrelated saves, failures and conflict recovery', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Usuario', { exact: true }).fill(setting('QA_USERNAME_A'));
  await page.getByLabel('Contraseña', { exact: true }).fill(setting('QA_PASSWORD'));
  await page.getByRole('button', { name: 'Ingresar', exact: true }).click();
  const suffix = String(Date.now());
  const address = `Domicilio sintético borradores ${suffix}`;
  await page.getByLabel('Domicilio nuevo').fill(address);
  const created = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/api/domiciles'));
  await page.getByRole('button', { name: 'Registrar domicilio', exact: true }).click();
  const home: unknown = await (await created).json();
  if (!isDomicile(home)) throw new Error('Invalid domicile DTO');
  const meter = page.getByRole('form', { name: 'Registrar medidor' });
  const meterDraft = `DRAFT-${suffix}`;
  await meter.getByLabel('Número de medidor').fill(meterDraft);
  await meter.getByLabel('Alias (opcional)').fill('Alias sin guardar');
  await page.getByRole('button', { name: 'Corregir domicilio', exact: true }).click();
  const addressForm = page.getByRole('form', { name: 'Corregir domicilio' });
  await addressForm.getByLabel('Dirección').fill(`${address} corregido`);

  // These isolated 503/409 responses exercise recovery without altering server data.
  await page.route(`**/api/domiciles/${home.id}`, route => route.fulfill({ status: 503, json: { detail: 'Falla sintética de domicilio' } }), { times: 1 });
  await addressForm.getByRole('button', { name: 'Guardar domicilio' }).click();
  await expect(page.getByRole('alert')).toContainText('Falla sintética de domicilio');
  await expect(meter.getByLabel('Número de medidor')).toHaveValue(meterDraft);
  await expect(meter.getByLabel('Alias (opcional)')).toHaveValue('Alias sin guardar');
  await expect(addressForm.getByLabel('Dirección')).toHaveValue(`${address} corregido`);
  await page.route(`**/api/domiciles/${home.id}`, route => route.fulfill({ status: 409, json: { detail: 'Conflicto sintético', code: 'VERSION_CONFLICT' } }), { times: 1 });
  await addressForm.getByRole('button', { name: 'Guardar domicilio' }).click();
  await page.getByRole('button', { name: 'Descartar borrador y recargar administración' }).click();
  await expect(addressForm).toHaveCount(0);
  await expect(meter.getByLabel('Número de medidor')).toHaveValue(meterDraft);
  await expect(meter.getByLabel('Alias (opcional)')).toHaveValue('Alias sin guardar');
  await page.getByRole('button', { name: 'Corregir domicilio', exact: true }).click();
  await addressForm.getByLabel('Dirección').fill(`${address} corregido`);
  await addressForm.getByRole('button', { name: 'Guardar domicilio' }).click();
  await expect(page.getByText('Domicilio actualizado.', { exact: true })).toBeVisible();
  await expect(meter.getByLabel('Número de medidor')).toHaveValue(meterDraft);
  await expect(meter.getByLabel('Alias (opcional)')).toHaveValue('Alias sin guardar');

  await page.getByRole('button', { name: 'Corregir domicilio', exact: true }).click();
  const addressDraft = `${address} sin guardar`;
  await addressForm.getByLabel('Dirección').fill(addressDraft);
  await page.route(`**/api/domiciles/${home.id}/meters`, route => route.fulfill({ status: 503, json: { detail: 'Falla sintética de medidor' } }), { times: 1 });
  await meter.getByRole('button', { name: 'Registrar medidor' }).click();
  await expect(page.getByRole('alert')).toContainText('Falla sintética de medidor');
  await expect(addressForm.getByLabel('Dirección')).toHaveValue(addressDraft);
  await expect(meter.getByLabel('Número de medidor')).toHaveValue(meterDraft);
  await page.route(`**/api/domiciles/${home.id}/meters`, route => route.fulfill({ status: 409, json: { detail: 'Conflicto sintético', code: 'VERSION_CONFLICT' } }), { times: 1 });
  await meter.getByRole('button', { name: 'Registrar medidor' }).click();
  await page.getByRole('button', { name: 'Descartar borrador y recargar administración' }).click();
  await expect(meter.getByLabel('Número de medidor')).toHaveValue('');
  await expect(addressForm.getByLabel('Dirección')).toHaveValue(addressDraft);
  await meter.getByLabel('Número de medidor').fill(meterDraft);
  await meter.getByLabel('Alias (opcional)').fill('Alias sin guardar');
  await meter.getByRole('button', { name: 'Registrar medidor' }).click();
  await expect(page.getByText('Medidor guardado.', { exact: true })).toBeVisible();
  await expect(addressForm.getByLabel('Dirección')).toHaveValue(addressDraft);
  await expect(meter.getByLabel('Número de medidor')).toHaveValue('');
});
