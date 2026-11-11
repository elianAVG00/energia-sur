import { expect, test } from '@playwright/test';
import type { Page, Route } from '@playwright/test';

const SSE = [
  'event: conversation\ndata: {"conversation_id":"11111111-1111-1111-1111-111111111111","scope":"persistent"}\n\n',
  'event: delta\ndata: {"text":"Podés pagar en la "}\n\n',
  'event: delta\ndata: {"text":"Oficina Virtual."}\n\n',
  'event: sources\ndata: {"sources":[{"source_name":"Edesur","url":"https://www.edesur.com.ar/servicios-al-cliente/opciones-de-pago/"}]}\n\n',
  'event: done\ndata: {"ok":true}\n\n',
].join('');

async function mockApi(page: Page, deleteStatus = 204): Promise<void> {
  await page.route('**/api/**', async (route: Route) => {
    const url = new URL(route.request().url());
    if (
      route.request().method() === 'DELETE'
      && url.pathname.startsWith('/api/assistant/conversations/')
    ) {
      if (deleteStatus === 204) {
        await route.fulfill({ status: 204, body: '' });
      } else {
        await route.fulfill({ status: deleteStatus, json: { detail: 'Sin permiso' } });
      }
      return;
    }
    if (url.pathname === '/api/session') {
      await route.fulfill({
        status: 200,
        json: {
          account: { id: 'synthetic', username: 'qa-synthetic' },
          csrf_token: 'synthetic-csrf',
        },
      });
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
    if (url.pathname === '/api/logout') {
      await route.fulfill({ status: 204, body: '' });
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

test('authenticated chat streams and logout clears the panel', async ({ page }) => {
  await mockApi(page);
  await page.goto('/');
  await page.getByRole('button', { name: 'Abrir asistente' }).click();
  await page.getByLabel('Consulta al asistente').fill('¿Cómo pago la factura?');
  await page.getByRole('button', { name: 'Enviar' }).click();

  const log = page.getByRole('log');
  await expect(log).toContainText('Podés pagar en la Oficina Virtual.');
  await expect(page.getByRole('link', { name: 'Edesur' })).toHaveAttribute(
    'href', 'https://www.edesur.com.ar/servicios-al-cliente/opciones-de-pago/',
  );

  await page.getByRole('button', { name: 'Cerrar sesión' }).click();
  await expect(page.getByRole('button', { name: 'Ingresar' })).toBeVisible();
  await expect(log).not.toContainText('Podés pagar en la Oficina Virtual.');
});

test('a failed conversation delete keeps the panel and shows an error', async ({ page }) => {
  await mockApi(page, 403);
  await page.goto('/');
  await page.getByRole('button', { name: 'Abrir asistente' }).click();
  await page.getByLabel('Consulta al asistente').fill('¿Cómo pago la factura?');
  await page.getByRole('button', { name: 'Enviar' }).click();
  await expect(page.getByRole('log')).toContainText('Podés pagar en la Oficina Virtual.');

  await page.getByRole('button', { name: 'Limpiar' }).click();
  await expect(page.getByRole('alert')).toContainText(
    'No se pudo borrar la conversación',
  );
  await expect(page.getByRole('log')).toContainText('Podés pagar en la Oficina Virtual.');
});
