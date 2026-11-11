import { expect, test } from '@playwright/test';
import type { Page, Route } from '@playwright/test';

const SSE = [
  'event: conversation\ndata: {"conversation_id":"synthetic","scope":"temporary"}\n\n',
  'event: delta\ndata: {"text":"Podés pagar en la "}\n\n',
  'event: delta\ndata: {"text":"Oficina Virtual."}\n\n',
  'event: sources\ndata: {"sources":[{"source_name":"Edesur","url":"https://www.edesur.com.ar/servicios-al-cliente/opciones-de-pago/"}]}\n\n',
  'event: done\ndata: {"ok":true}\n\n',
].join('');

async function mockApi(page: Page): Promise<void> {
  await page.route('**/api/**', async (route: Route) => {
    const url = new URL(route.request().url());
    if (url.pathname === '/api/session') {
      await route.fulfill({ status: 401, json: { detail: 'Sin sesión' } });
      return;
    }
    if (url.pathname === '/api/health') {
      await route.fulfill({ status: 200, json: { status: 'ok' } });
      return;
    }
    if (url.pathname === '/api/domiciles') {
      await route.fulfill({ status: 200, json: [] });
      return;
    }
    if (url.pathname === '/api/assistant/chat') {
      await route.fulfill({
        status: 200,
        headers: { 'content-type': 'text/event-stream', 'cache-control': 'no-store' },
        body: SSE,
      });
      return;
    }
    await route.fulfill({ status: 404, json: { detail: 'not mocked' } });
  });
}

test('visitor chats with the assistant and receives an official source', async ({ page }) => {
  await mockApi(page);
  await page.goto('/');
  await page.getByRole('button', { name: 'Abrir asistente' }).click();
  await page.getByLabel('Consulta al asistente').fill('¿Cómo pago la factura?');
  await page.getByRole('button', { name: 'Enviar' }).click();

  const log = page.getByRole('log');
  await expect(log).toContainText('Podés pagar en la Oficina Virtual.');
  await expect(log).toContainText('¿Cómo pago la factura?');

  const source = page.getByRole('link', { name: 'Edesur' });
  await expect(source).toHaveAttribute(
    'href', 'https://www.edesur.com.ar/servicios-al-cliente/opciones-de-pago/',
  );
  await expect(source).toHaveAttribute('rel', 'noopener noreferrer');
  await expect(page.getByRole('button', { name: 'Enviar' })).toBeDisabled();
  await expect(page.locator('#assistant-panel img')).toHaveCount(0);
});
