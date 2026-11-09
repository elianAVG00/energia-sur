import { expect, test } from '@playwright/test';
import { writeFile } from 'node:fs/promises';
import { isDomicile } from '../src/diaryApi.ts';
import { isMeter } from '../src/features/domiciles/api.ts';

const FALLBACK = 'No pudimos identificar con seguridad la lectura del medidor. Intentá subir una fotografía más clara o ingresá manualmente el valor en kWh';

function setting(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing synthetic QA setting ${name}`);
  return value;
}

function createdId(value: unknown, label: string): string {
  if (typeof value !== 'object' || value === null) throw new Error(`Invalid ${label} DTO`);
  const id = (value as Record<string, unknown>).id;
  if (typeof id !== 'string' || id === '') throw new Error(`Invalid ${label} id`);
  return id;
}

test('real CU05: manual reading with synthetic photo survives reload, OCR abstains', async ({ page }) => {
  // 1×1 transparent PNG: synthetic, never a real meter photo.
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
  const suffix = String(Date.now());
  const address = `Domicilio sintético lecturas ${suffix}`;
  const meterNumber = `LECT-${suffix}`;

  await page.goto('/');
  await page.getByLabel('Usuario', { exact: true }).fill(setting('QA_USERNAME_A'));
  await page.getByLabel('Contraseña', { exact: true }).fill(setting('QA_PASSWORD'));
  await page.getByRole('button', { name: 'Ingresar', exact: true }).click();

  await page.getByLabel('Domicilio nuevo', { exact: true }).fill(address);
  const domicileResponse = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/api/domiciles'));
  await page.getByRole('button', { name: 'Registrar domicilio', exact: true }).click();
  const domicileBody: unknown = await (await domicileResponse).json();
  if (!isDomicile(domicileBody)) throw new Error('Invalid domicile DTO');

  const meterForm = page.getByRole('form', { name: 'Registrar medidor' });
  await meterForm.getByLabel('Número de medidor').fill(meterNumber);
  const meterResponse = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith(`/api/domiciles/${domicileBody.id}/meters`));
  await meterForm.getByRole('button', { name: 'Registrar medidor' }).click();
  const meterBody: unknown = await (await meterResponse).json();
  if (!isMeter(meterBody)) throw new Error('Invalid meter DTO');

  await page.getByLabel('Medidor para consultar lecturas').selectOption(meterBody.id);
  const form = page.getByRole('form', { name: 'Registrar lectura' });
  await form.getByLabel('Fecha y hora con zona horaria').fill('2026-11-07T15:00:00Z');
  await form.getByLabel('Lectura acumulada en kWh').fill('12345');
  await form.getByLabel(/Fotografía/).setInputFiles({ name: 'synthetic.png', mimeType: 'image/png', buffer: png });
  await expect(form.getByText(/1×1/)).toBeVisible();

  // OCR is fail-closed: the fallback appears and the manual value is untouched.
  await form.getByRole('button', { name: 'Leer dígitos con OCR' }).click();
  await expect(form.getByText(FALLBACK, { exact: true })).toBeVisible();
  await expect(form.getByLabel('Lectura acumulada en kWh')).toHaveValue('12345');

  await form.getByLabel('Confirmo que revisé la lectura').check();
  const created = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith(`/api/meters/${meterBody.id}/readings`));
  await form.getByRole('button', { name: 'Guardar lectura' }).click();
  const readingId = createdId(await (await created).json(), 'reading');
  await expect(page.getByText('Lectura guardada.', { exact: true })).toBeVisible();
  await expect(page.getByText(/12345 kWh/)).toBeVisible();

  // The private photo is served by the real backend through the session cookie.
  await page.getByRole('button', { name: 'Ver foto' }).click();
  await expect(page.getByRole('img', { name: 'Foto de la lectura seleccionada' })).toBeVisible();

  await page.reload();
  await page.getByLabel('Domicilio seleccionado').selectOption({ value: domicileBody.id });
  await page.getByLabel('Medidor para consultar lecturas').selectOption(meterBody.id);
  await expect(page.getByText(/12345 kWh/)).toBeVisible();
  await page.getByRole('button', { name: 'Ver foto' }).click();
  await expect(page.getByRole('img', { name: 'Foto de la lectura seleccionada' })).toBeVisible();

  // Let the acceptance script verify the same reading and photo after a backend restart.
  await writeFile('/tmp/cu09-artifacts/cu05-state.json', JSON.stringify({
    domicile: domicileBody.id, meter: meterBody.id, reading: readingId,
  }));
});

test('real CU05: browser-rendered digits are suggested without saving', async ({ page }) => {
  const suffix = String(Date.now());
  const meterNumber = `OCR-${suffix}`;
  await page.goto('/');
  await page.getByLabel('Usuario', { exact: true }).fill(setting('QA_USERNAME_A'));
  await page.getByLabel('Contraseña', { exact: true }).fill(setting('QA_PASSWORD'));
  await page.getByRole('button', { name: 'Ingresar', exact: true }).click();
  await page.getByLabel('Domicilio nuevo', { exact: true }).fill(`OCR synthetic ${suffix}`);
  const homeResponse = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/api/domiciles'));
  await page.getByRole('button', { name: 'Registrar domicilio', exact: true }).click();
  const home: unknown = await (await homeResponse).json();
  if (!isDomicile(home)) throw new Error('Invalid domicile DTO');
  const meterForm = page.getByRole('form', { name: 'Registrar medidor' });
  await meterForm.getByLabel('Número de medidor').fill(meterNumber);
  const meterResponse = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith(`/api/domiciles/${home.id}/meters`));
  await meterForm.getByRole('button', { name: 'Registrar medidor' }).click();
  const meter: unknown = await (await meterResponse).json();
  if (!isMeter(meter)) throw new Error('Invalid meter DTO');
  await page.getByLabel('Medidor para consultar lecturas').selectOption(meter.id);
  const form = page.getByRole('form', { name: 'Registrar lectura' });
  const encoded = await page.evaluate(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 560; canvas.height = 120;
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Canvas unavailable');
    context.fillStyle = 'white'; context.fillRect(0, 0, 560, 120);
    context.fillStyle = 'black'; context.font = '75px sans-serif';
    context.fillText('56538', 20, 80);
    return canvas.toDataURL('image/png').split(',')[1];
  });
  await form.getByLabel(/Fotografía/).setInputFiles({ name: 'synthetic.png', mimeType: 'image/png', buffer: Buffer.from(encoded, 'base64') });
  await form.getByRole('button', { name: 'Leer dígitos con OCR' }).click();
  await expect(form.getByLabel('Lectura acumulada en kWh')).toHaveValue('56538');
  await expect(form.getByLabel('Confirmo que revisé la lectura')).not.toBeChecked();
  await form.getByLabel('Lectura acumulada en kWh').fill('42');
  await expect(form.getByLabel('Lectura acumulada en kWh')).toHaveValue('42');
  const history = await page.request.get(`/api/meters/${meter.id}/readings`);
  expect(history.status()).toBe(200);
  expect(await history.json()).toEqual([]);
});
