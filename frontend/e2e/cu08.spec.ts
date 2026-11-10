import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';
import { readFileSync } from 'node:fs';

interface Scenario { domicile: string; meter: string; readings: string[] }

const state = JSON.parse(readFileSync(process.env.CU08_STATE ?? '/state/cu08-state.json', 'utf8')) as Record<string, Scenario>;
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

async function openConsumption(page: Page, seeded: Scenario): Promise<void> {
  await page.goto('/');
  await page.getByLabel('Domicilio seleccionado').selectOption(seeded.domicile);
  await page.getByLabel('Medidor para consultar lecturas').selectOption(seeded.meter);
  await expect(page.getByText('Consumo y estimación')).toBeVisible();
}

test('CU08 shows two views and a deterministic estimate with the orientative warning', async ({ page }) => {
  await login(page, userA);
  await openConsumption(page, scenario('main'));
  await expect(page.getByText('Consumo real (kWh)')).toBeVisible();
  await expect(page.getByText('Promedio diario (kWh/día)')).toBeVisible();
  await expect(page.getByRole('cell', { name: '20 kWh' })).toBeVisible();
  await expect(page.getByRole('cell', { name: '10.00 kWh/día' })).toBeVisible();
  await expect(page.getByRole('cell', { name: '60 kWh' })).toBeVisible();
  await expect(page.getByRole('cell', { name: '15.00 kWh/día' })).toBeVisible();

  await page.getByLabel('Días a estimar (1–90)').fill('7');
  await page.getByRole('button', { name: 'Estimar' }).click();
  await expect(page.getByText('Estimación a 7 días: 105.00 kWh')).toBeVisible();
  await expect(page.getByText('Estimación orientativa, no facturada.')).toBeVisible();
});

test('CU08 reports a decreasing last interval without estimating', async ({ page }) => {
  await login(page, userA);
  await openConsumption(page, scenario('decreasing'));
  await expect(page.getByRole('cell', { name: 'no calculable' }).first()).toBeVisible();
  await page.getByLabel('Días a estimar (1–90)').fill('7');
  await page.getByRole('button', { name: 'Estimar' }).click();
  await expect(page.getByText('No se estima porque la última lectura es menor que la anterior.')).toBeVisible();
});

test('CU08 shows zero consumption and a zero estimate', async ({ page }) => {
  await login(page, userA);
  await openConsumption(page, scenario('zero'));
  await page.getByLabel('Días a estimar (1–90)').fill('30');
  await page.getByRole('button', { name: 'Estimar' }).click();
  await expect(page.getByText('Estimación a 30 días: 0.00 kWh')).toBeVisible();
});

test('CU08 hides another account\'s consumption resources', async ({ page, browser }) => {
  await login(page, userA);
  const shared = scenario('isolation');
  const context = await browser.newContext();
  const foreign = await context.newPage();
  await login(foreign, userB);
  for (const path of [
    `/api/meters/${shared.meter}/consumption-evolution`,
    `/api/meters/${shared.meter}/consumption-estimate?days=7`,
  ]) {
    const response = await context.request.get(path);
    expect(response.status()).toBe(404);
  }
  await context.close();
});
