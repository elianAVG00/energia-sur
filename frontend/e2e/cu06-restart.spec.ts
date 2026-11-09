import { expect, test } from '@playwright/test';
import { readFile } from 'node:fs/promises';

function setting(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing synthetic QA setting ${name}`);
  return value;
}

test('CU06 bills and private files survive a backend restart', async ({ page }) => {
  const state: unknown = JSON.parse(await readFile('/tmp/cu06-artifacts/cu06-state.json', 'utf8'));
  if (typeof state !== 'object' || state === null) throw new Error('Invalid restart state');
  const { domicile, meter } = state as Record<string, unknown>;
  if (typeof domicile !== 'string' || typeof meter !== 'string') throw new Error('Invalid restart state');
  await page.goto('/');
  await page.getByLabel('Usuario', { exact: true }).fill(setting('QA_USERNAME_A'));
  await page.getByLabel('Contraseña', { exact: true }).fill(setting('QA_PASSWORD'));
  await page.getByRole('button', { name: 'Ingresar', exact: true }).click();
  await page.getByLabel('Domicilio seleccionado').selectOption({ value: domicile });
  await page.getByLabel('Medidor para consultar lecturas').selectOption(meter);
  await expect(page.getByText(/124 kWh/)).toBeVisible();
  await expect(page.getByText(/2026-01-31 — 2026-02-28/)).toBeVisible();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Descargar archivo' }).first().click();
  expect((await download).suggestedFilename()).toBe('factura.png');
});
