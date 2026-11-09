import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';
import { readFileSync } from 'node:fs';

interface Scenario { domicile: string; meter: string; bill: string; readings: string[] }

const state = JSON.parse(readFileSync(process.env.CU07_STATE ?? '/state/cu07-state.json', 'utf8')) as Record<string, Scenario>;
const password = process.env.QA_PASSWORD ?? '';
const userA = process.env.QA_USERNAME_A ?? '';
const userB = process.env.QA_USERNAME_B ?? '';

function scenario(name: string): Scenario {
  const value = state[name];
  if (!value) throw new Error(`Missing seeded scenario ${name}`);
  return value;
}

async function login(page: Page, username: string): Promise<void> {
  await page.goto('/');
  await page.getByLabel('Usuario', { exact: true }).fill(username);
  await page.getByLabel('Contraseña', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Ingresar', exact: true }).click();
  await expect(page.getByText('Cerrar sesión')).toBeVisible();
}

async function openComparison(page: Page, seeded: Scenario): Promise<void> {
  await page.goto('/');
  await page.getByLabel('Domicilio seleccionado').selectOption(seeded.domicile);
  await page.getByLabel('Medidor para consultar lecturas').selectOption(seeded.meter);
  await page.getByRole('button', { name: 'Comparar' }).first().click();
}

test('CU07 compares exact boundaries directly without a percentage', async ({ page }) => {
  await login(page, userA);
  await openComparison(page, scenario('exact'));
  await expect(page.getByText('Consumo registrado: 120 kWh', { exact: true })).toBeVisible();
  await expect(page.getByText('Consumo facturado: 100 kWh', { exact: true })).toBeVisible();
  await expect(page.getByText('Diferencia: 20 kWh', { exact: true })).toBeVisible();
  await expect(page.getByText('El consumo registrado es mayor que el facturado.')).toBeVisible();
  await expect(page.getByText(/porcentaje/i)).toHaveCount(0);
});

test('CU07 handles multiple candidates and approximate confirmation', async ({ page }) => {
  await login(page, userA);
  const multiple = scenario('multiple');
  await openComparison(page, multiple);
  const startSelect = page.getByLabel('Lectura inicial (candidatas)');
  await expect(startSelect.locator('option')).toHaveCount(4);
  await startSelect.selectOption(multiple.readings[0] ?? '');
  await page.getByLabel('Lectura final (candidatas)').selectOption(multiple.readings[2] ?? '');
  await page.getByRole('button', { name: 'Calcular comparación' }).click();
  await expect(page.getByText('Consumo registrado: 120 kWh')).toBeVisible();

  const approximate = scenario('approximate');
  await openComparison(page, approximate);
  await page.getByLabel('Lectura inicial (candidatas)').selectOption(approximate.readings[0] ?? '');
  await page.getByLabel('Lectura final (candidatas)').selectOption(approximate.readings[1] ?? '');
  const submit = page.getByRole('button', { name: 'Calcular comparación' });
  await expect(submit).toBeDisabled();
  await page.getByLabel('Confirmo que quiero comparar con estas fechas aproximadas.').check();
  await expect(submit).toBeEnabled();
  await submit.click();
  await expect(page.getByText('Consumo registrado: 120 kWh')).toBeVisible();
  await expect(page.getByText(/Comparación aproximada/)).toBeVisible();
});

test('CU07 reports zero and decreasing consumption without calculating negative values', async ({ page }) => {
  await login(page, userA);
  await openComparison(page, scenario('zero'));
  await expect(page.getByText('Consumo registrado: 0 kWh')).toBeVisible();
  await expect(page.getByText('El consumo facturado es mayor que el registrado.')).toBeVisible();
  await openComparison(page, scenario('decreasing'));
  await expect(page.getByText('No se calculó la comparación porque la lectura final es menor que la lectura inicial.')).toBeVisible();
});

test('CU07 hides another account\'s comparison resources', async ({ page, browser }) => {
  await login(page, userA);
  const shared = scenario('isolation');
  const context = await browser.newContext();
  const foreign = await context.newPage();
  await login(foreign, userB);
  for (const path of [
    `/api/meters/${shared.meter}/bills/${shared.bill}/comparison-candidates`,
    `/api/meters/${shared.meter}/bills/${shared.bill}/comparison?start_reading_id=${shared.readings[0]}&end_reading_id=${shared.readings[1]}`,
  ]) {
    const response = await context.request.get(path);
    expect(response.status()).toBe(404);
  }
  await context.close();
});
