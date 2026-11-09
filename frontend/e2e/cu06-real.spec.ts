import { expect, test } from '@playwright/test';
import { readFile, writeFile } from 'node:fs/promises';
import { isDomicile } from '../src/diaryApi.ts';
import { isMeter } from '../src/features/domiciles/api.ts';

function setting(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing synthetic QA setting ${name}`);
  return value;
}

test('CU06 registers, warns, corrects and downloads a private synthetic bill', async ({ page }) => {
  const suffix = String(Date.now());
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
  await page.goto('/');
  await page.getByLabel('Usuario', { exact: true }).fill(setting('QA_USERNAME_A'));
  await page.getByLabel('Contraseña', { exact: true }).fill(setting('QA_PASSWORD'));
  await page.getByRole('button', { name: 'Ingresar', exact: true }).click();
  await page.getByLabel('Domicilio nuevo', { exact: true }).fill(`Domicilio sintético factura ${suffix}`);
  const homeResponse = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/api/domiciles'));
  await page.getByRole('button', { name: 'Registrar domicilio', exact: true }).click();
  const home: unknown = await (await homeResponse).json();
  if (!isDomicile(home)) throw new Error('Invalid synthetic domicile');
  const meterForm = page.getByRole('form', { name: 'Registrar medidor' });
  await meterForm.getByLabel('Número de medidor').fill(`BILL-${suffix}`);
  const meterResponse = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith(`/api/domiciles/${home.id}/meters`));
  await meterForm.getByRole('button', { name: 'Registrar medidor' }).click();
  const meter: unknown = await (await meterResponse).json();
  if (!isMeter(meter)) throw new Error('Invalid synthetic meter');
  await page.getByLabel('Medidor para consultar lecturas').selectOption(meter.id);
  await page.getByLabel('Inicio del período').fill('2026-01-01');
  await page.getByLabel('Fin del período').fill('2026-01-31');
  await page.getByLabel('Consumo facturado (kWh)').fill('123.125');
  await page.getByLabel('Archivo obligatorio').setInputFiles({ name: 'synthetic.png', mimeType: 'image/png', buffer: png });
  const firstBillResponse = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith(`/api/meters/${meter.id}/bills`));
  await page.getByRole('button', { name: 'Guardar factura' }).click();
  const firstBill: unknown = await (await firstBillResponse).json();
  if (typeof firstBill !== 'object' || firstBill === null || typeof (firstBill as Record<string, unknown>).id !== 'string') throw new Error('Invalid synthetic bill');
  await expect(page.getByText('Factura guardada.')).toBeVisible();
  await expect(page.getByText(/123\.125 kWh/)).toBeVisible();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Descargar archivo' }).click();
  expect((await download).suggestedFilename()).toBe('factura.png');
  await page.getByRole('button', { name: 'Corregir factura' }).click();
  await page.getByLabel('Consumo facturado (kWh)').fill('124');
  await page.getByLabel('Reemplazar archivo (opcional)').setInputFiles({ name: 'replacement.png', mimeType: 'image/png', buffer: png });
  await page.getByRole('button', { name: 'Guardar factura' }).click();
  await expect(page.getByText('Factura corregida.')).toBeVisible();
  await page.getByLabel('Inicio del período').fill('2026-01-31');
  await page.getByLabel('Fin del período').fill('2026-02-28');
  await page.getByLabel('Consumo facturado (kWh)').fill('50');
  await page.getByLabel('Archivo obligatorio').setInputFiles({ name: 'synthetic.png', mimeType: 'image/png', buffer: png });
  await page.getByRole('button', { name: 'Guardar factura' }).click();
  await expect(page.getByRole('button', { name: 'Confirmar superposición y guardar' })).toBeVisible();
  await page.getByRole('button', { name: 'Confirmar superposición y guardar' }).click();
  await expect(page.getByText('Factura guardada.')).toBeVisible();
  await writeFile('/tmp/cu06-artifacts/cu06-state.json', JSON.stringify({
    domicile: home.id, meter: meter.id, bill: (firstBill as Record<string, unknown>).id,
  }));
});

test('CU06 hides another account\'s bills and private file', async ({ browser }) => {
  const state: unknown = JSON.parse(await readFile('/tmp/cu06-artifacts/cu06-state.json', 'utf8'));
  if (typeof state !== 'object' || state === null) throw new Error('Invalid state');
  const { meter, bill } = state as Record<string, unknown>;
  if (typeof meter !== 'string' || typeof bill !== 'string') throw new Error('Invalid state');
  const context = await browser.newContext();
  const foreign = await context.newPage();
  await foreign.goto('/');
  await foreign.getByLabel('Usuario', { exact: true }).fill(setting('QA_USERNAME_B'));
  await foreign.getByLabel('Contraseña', { exact: true }).fill(setting('QA_PASSWORD'));
  await foreign.getByRole('button', { name: 'Ingresar', exact: true }).click();
  await expect(foreign.getByText('Cerrar sesión')).toBeVisible();
  const list = await foreign.request.get(`/api/meters/${meter}/bills`);
  expect(list.status()).toBe(404);
  const file = await foreign.request.get(`/api/meters/${meter}/bills/${bill}/file`);
  expect(file.status()).toBe(404);
  await context.close();
});
