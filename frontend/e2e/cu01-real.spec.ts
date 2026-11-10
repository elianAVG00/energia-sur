import { expect, test } from '@playwright/test';

// Real backend smoke for the CU01 serialization contract. Requires an isolated
// backend seeded from tests/fixtures/enre_data_eds_redacted.js and the frontend
// proxy pointing at it. Run with CU01_LIVE=1.
test('real backend: partido-only, low-voltage row and covered no-reports', async ({ page }) => {
  test.skip(!process.env.CU01_LIVE, 'Requires a seeded real backend');
  await page.goto('/');
  await page.getByRole('button', { name: 'Cortes' }).click();

  await page.getByLabel('Partido', { exact: true }).selectOption('ALMIRANTE BROWN');
  await page.getByLabel('Localidad (opcional)', { exact: true }).selectOption('SAN JOSE');
  await page.getByRole('button', { name: 'Consultar cortes' }).click();
  await expect(page.getByRole('heading', { name: 'Cortes reportados' })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Baja tensión' })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Sin datos' })).toBeVisible();

  await page.getByLabel('Localidad (opcional)', { exact: true }).selectOption('');
  await page.getByRole('button', { name: 'Consultar cortes' }).click();
  await expect(page.getByText('Resultado por partido')).toBeVisible();

  await page.getByLabel('Partido', { exact: true }).selectOption('BERAZATEGUI');
  await page.getByLabel('Localidad (opcional)', { exact: true }).selectOption('BERAZATEGUI');
  await page.getByRole('button', { name: 'Consultar cortes' }).click();
  await expect(page.getByRole('heading', { name: 'Sin cortes reportados' })).toBeVisible();
  await expect(page.getByText('Esto no garantiza el suministro eléctrico.')).toBeVisible();
});
