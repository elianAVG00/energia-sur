import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';

async function selectSyntheticMeter(page: Page): Promise<void> {
  // Diagnose session, domicile and meter loading separately from the CU05 selector.
  await expect(page.getByText('Cuenta: synthetic', { exact: true })).toBeVisible();
  await expect(page.getByLabel('Domicilio seleccionado')).toHaveValue('d');
  await expect(page.getByRole('list').getByText('ONE', { exact: true })).toBeVisible();
  await expect(page.getByLabel('Medidor para consultar lecturas')).toBeVisible();
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
}

// Duplicate sibling keys make React reconciliation unsupported and were the root cause of
// the stale meter history. Fail any scenario that reintroduces that warning.
let duplicateKeyWarnings: string[] = [];
test.beforeEach(({ page }) => {
  duplicateKeyWarnings = [];
  page.on('console', message => {
    if (message.text().includes('Encountered two children with the same key')) duplicateKeyWarnings.push(message.text());
  });
});
test.afterEach(() => { expect(duplicateKeyWarnings).toEqual([]); });

test('reading history is scoped to the selected meter and displays Buenos Aires time', async ({ page }) => {
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/meters/m1/readings/r1/photo') {
      await route.fulfill({ status: 200, contentType: 'image/png', body: png }); return;
    }
    const responses: Record<string, unknown> = {
      '/api/session': { account: { id: 'a', username: 'synthetic' }, csrf_token: 'synthetic' },
      '/api/domiciles': [{ id: 'd', display_address: 'Synthetic domicile' }],
      '/api/domiciles/d/management': { id: 'd', display_address: 'Synthetic domicile', version: 1 },
      '/api/domiciles/d/meters': [
        { id: 'm1', domicile_id: 'd', meter_number: 'ONE', alias: null, version: 1 },
        { id: 'm2', domicile_id: 'd', meter_number: 'TWO', alias: null, version: 1 },
      ],
      '/api/domiciles/d/interruptions': [],
      '/api/meters/m1/readings': [{ id: 'r1', meter_id: 'm1', recorded_at: '2026-11-07T15:00:00Z', value_kwh: '9007199254740993', has_photo: true, version: 1 }],
      '/api/meters/m2/readings': [],
    };
    if (!(path in responses)) { await route.fulfill({ status: 404, json: { detail: 'Not found' } }); return; }
    await route.fulfill({ json: responses[path] });
  });
  await page.goto('/');
  await selectSyntheticMeter(page);
  await expect(page.getByText(/9007199254740993 kWh/)).toBeVisible();
  await expect(page.getByText(/07\/11\/2026.*12:00:00/)).toBeVisible();
  // A photo and an open edit form from the previous meter must not survive the switch.
  await page.getByRole('button', { name: 'Ver foto' }).click();
  await expect(page.getByRole('img', { name: 'Foto de la lectura seleccionada' })).toBeVisible();
  await page.getByRole('button', { name: 'Corregir lectura' }).click();
  await expect(page.getByRole('form', { name: 'Corregir lectura' })).toBeVisible();
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m2');
  await expect(page.getByText('No hay lecturas registradas.')).toBeVisible();
  await expect(page.getByText(/9007199254740993 kWh/)).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Corregir lectura' })).toHaveCount(0);
  await expect(page.getByRole('form', { name: 'Corregir lectura' })).toHaveCount(0);
  await expect(page.getByRole('img', { name: 'Foto de la lectura seleccionada' })).toHaveCount(0);
});

test('a pending previous-meter request is cancelled and never shows stale data', async ({ page }) => {
  const m1Row = { id: 'r1', meter_id: 'm1', recorded_at: '2026-11-07T15:00:00Z', value_kwh: '111', has_photo: false, version: 1 };
  let m1RefreshStarted: () => void = () => undefined;
  let releaseM1Refresh: () => void = () => undefined;
  let gateNextM1 = false;
  const m1RefreshStartedPromise = new Promise<void>(resolve => { m1RefreshStarted = resolve; });
  const m1RefreshGate = new Promise<void>(resolve => { releaseM1Refresh = resolve; });
  const failures: string[] = [];
  page.on('requestfailed', request => {
    if (new URL(request.url()).pathname === '/api/meters/m1/readings') failures.push(request.failure()?.errorText ?? '');
  });
  await page.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === '/api/meters/m1/readings' && request.method() === 'GET') {
      if (gateNextM1) {
        // Hold the manual refresh so the meter switch happens while it is still pending.
        gateNextM1 = false;
        m1RefreshStarted();
        await m1RefreshGate;
      }
      try { await route.fulfill({ json: [m1Row] }); } catch { /* request aborted by the meter switch */ }
      return;
    }
    if (path === '/api/meters/m2/readings' && request.method() === 'GET') {
      await new Promise(resolve => setTimeout(resolve, 800));
      await route.fulfill({ json: [] }); return;
    }
    const responses: Record<string, unknown> = {
      '/api/session': { account: { id: 'a', username: 'synthetic' }, csrf_token: 'synthetic' },
      '/api/domiciles': [{ id: 'd', display_address: 'Synthetic domicile' }],
      '/api/domiciles/d/management': { id: 'd', display_address: 'Synthetic domicile', version: 1 },
      '/api/domiciles/d/meters': [
        { id: 'm1', domicile_id: 'd', meter_number: 'ONE', alias: null, version: 1 },
        { id: 'm2', domicile_id: 'd', meter_number: 'TWO', alias: null, version: 1 },
      ],
      '/api/domiciles/d/interruptions': [],
    };
    if (!(path in responses)) { await route.fulfill({ status: 404, json: { detail: 'Not found' } }); return; }
    await route.fulfill({ json: responses[path] });
  });
  await page.goto('/');
  await selectSyntheticMeter(page);
  await expect(page.getByText(/111 kWh/)).toBeVisible();
  gateNextM1 = true;
  await page.getByRole('button', { name: 'Actualizar lecturas' }).click();
  await m1RefreshStartedPromise;
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m2');
  // While the new history loads, the previous meter's visible reading must already be gone.
  await expect(page.getByText(/111 kWh/)).toHaveCount(0);
  await expect(page.getByText('No hay lecturas registradas.')).toBeVisible();
  await expect.poll(() => failures.length).toBeGreaterThan(0);
  releaseM1Refresh();
  await expect(page.getByText(/111 kWh/)).toHaveCount(0);
});

test('rapid meter switching keeps only the last selected history and the exact kWh value', async ({ page }) => {
  function gate() {
    let start: () => void = () => undefined;
    let release: () => void = () => undefined;
    const started = new Promise<void>(resolve => { start = resolve; });
    const wait = new Promise<void>(resolve => { release = resolve; });
    return { start, release, started, wait };
  }
  const m1Gates = [gate(), gate()];
  const m2Gate = gate();
  let m1Index = 0;
  await page.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === '/api/meters/m1/readings' && request.method() === 'GET') {
      const current = m1Gates[m1Index++];
      current?.start();
      await current?.wait;
      try {
        await route.fulfill({ json: [{ id: 'r1', meter_id: 'm1', recorded_at: '2026-11-07T15:00:00Z', value_kwh: '9007199254740993', has_photo: false, version: 1 }] });
      } catch { /* superseded request */ }
      return;
    }
    if (path === '/api/meters/m2/readings' && request.method() === 'GET') {
      m2Gate.start();
      await m2Gate.wait;
      try {
        await route.fulfill({ json: [{ id: 'r2', meter_id: 'm2', recorded_at: '2026-11-08T15:00:00Z', value_kwh: '42', has_photo: false, version: 1 }] });
      } catch { /* superseded request */ }
      return;
    }
    const responses: Record<string, unknown> = {
      '/api/session': { account: { id: 'a', username: 'synthetic' }, csrf_token: 'synthetic' },
      '/api/domiciles': [{ id: 'd', display_address: 'Synthetic domicile' }],
      '/api/domiciles/d/management': { id: 'd', display_address: 'Synthetic domicile', version: 1 },
      '/api/domiciles/d/meters': [
        { id: 'm1', domicile_id: 'd', meter_number: 'ONE', alias: null, version: 1 },
        { id: 'm2', domicile_id: 'd', meter_number: 'TWO', alias: null, version: 1 },
      ],
      '/api/domiciles/d/interruptions': [],
    };
    if (!(path in responses)) { await route.fulfill({ status: 404, json: { detail: 'Not found' } }); return; }
    await route.fulfill({ json: responses[path] });
  });
  await page.goto('/');
  const selector = page.getByLabel('Medidor para consultar lecturas');
  await selectSyntheticMeter(page);
  await m1Gates[0]?.started;
  await selector.selectOption('m2');
  await m2Gate.started;
  // Release the newest request first, then the superseded one: the final view must stay on m2.
  m2Gate.release();
  await expect(page.getByText(/42 kWh/)).toBeVisible();
  m1Gates[0]?.release();
  await expect(page.getByText(/42 kWh/)).toBeVisible();
  await expect(page.getByText(/9007199254740993 kWh/)).toHaveCount(0);
  await selector.selectOption('m1');
  await m1Gates[1]?.started;
  m1Gates[1]?.release();
  await expect(page.getByText(/9007199254740993 kWh/)).toBeVisible();
  await expect(page.getByText(/9007199254740992/)).toHaveCount(0);
  await expect(page.getByText(/42 kWh/)).toHaveCount(0);
});

test('an HTTP error for the selected meter does not resurrect the previous reading', async ({ page }) => {
  const m1Row = { id: 'r1', meter_id: 'm1', recorded_at: '2026-11-07T15:00:00Z', value_kwh: '111', has_photo: false, version: 1 };
  await page.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === '/api/meters/m2/readings' && request.method() === 'GET') {
      await route.fulfill({ status: 503, json: { detail: 'Servicio no disponible.' } }); return;
    }
    const responses: Record<string, unknown> = {
      '/api/session': { account: { id: 'a', username: 'synthetic' }, csrf_token: 'synthetic' },
      '/api/domiciles': [{ id: 'd', display_address: 'Synthetic domicile' }],
      '/api/domiciles/d/management': { id: 'd', display_address: 'Synthetic domicile', version: 1 },
      '/api/domiciles/d/meters': [
        { id: 'm1', domicile_id: 'd', meter_number: 'ONE', alias: null, version: 1 },
        { id: 'm2', domicile_id: 'd', meter_number: 'TWO', alias: null, version: 1 },
      ],
      '/api/domiciles/d/interruptions': [],
      '/api/meters/m1/readings': [m1Row],
    };
    if (!(path in responses)) { await route.fulfill({ status: 404, json: { detail: 'Not found' } }); return; }
    await route.fulfill({ json: responses[path] });
  });
  await page.goto('/');
  await selectSyntheticMeter(page);
  await expect(page.getByText(/111 kWh/)).toBeVisible();
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m2');
  await expect(page.getByText('Servicio no disponible.')).toBeVisible();
  await expect(page.getByText(/111 kWh/)).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Corregir lectura' })).toHaveCount(0);
});

test('meter selection also isolates the bill and consumption panels', async ({ page }) => {
  const interval = (id: string, start: string, end: string, consumption: string) => ({
    start_reading_id: `s-${id}`, end_reading_id: `e-${id}`, start_at: `${start}T00:00:00Z`, end_at: `${end}T00:00:00Z`,
    start_local_date: start, end_local_date: end, start_value_kwh: '1000', end_value_kwh: '2000',
    consumption_kwh: consumption, daily_average_kwh_day: consumption, calculable: true, sub_day: false, below_minimum: false,
  });
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    const responses: Record<string, unknown> = {
      '/api/session': { account: { id: 'a', username: 'synthetic' }, csrf_token: 'synthetic' },
      '/api/domiciles': [{ id: 'd', display_address: 'Synthetic domicile' }],
      '/api/domiciles/d/management': { id: 'd', display_address: 'Synthetic domicile', version: 1 },
      '/api/domiciles/d/meters': [
        { id: 'm1', domicile_id: 'd', meter_number: 'ONE', alias: null, version: 1 },
        { id: 'm2', domicile_id: 'd', meter_number: 'TWO', alias: null, version: 1 },
      ],
      '/api/domiciles/d/interruptions': [],
      '/api/meters/m1/readings': [],
      '/api/meters/m2/readings': [],
      '/api/meters/m1/bills': [{ id: 'b1', meter_id: 'm1', period_start: '2026-01-01', period_end: '2026-01-31', value_kwh: '100', amount_ars: null, file_type: 'application/pdf', version: 1 }],
      '/api/meters/m2/bills': [{ id: 'b2', meter_id: 'm2', period_start: '2026-02-01', period_end: '2026-02-28', value_kwh: '200', amount_ars: null, file_type: 'application/pdf', version: 1 }],
      '/api/meters/m1/consumption-evolution': { meter_id: 'm1', intervals: [interval('m1', '2026-01-01', '2026-01-31', '517')] },
      '/api/meters/m2/consumption-evolution': { meter_id: 'm2', intervals: [interval('m2', '2026-02-01', '2026-02-28', '731')] },
      '/api/meters/m1/bills/b1/comparison-candidates': { bill_id: 'b1', meter_id: 'm1', period_start: '2026-01-01', period_end: '2026-01-31', billed_kwh: '100', start_candidates: [], end_candidates: [] },
      '/api/meters/m1/consumption-estimate': {
        meter_id: 'm1', status: 'available', days: 30, daily_average_kwh_day: '17.233', estimate_kwh: '517',
        orientative: true, below_minimum: false, daily_average_below_minimum: false, sub_day: false,
        base_start_reading_id: 's-m1', base_end_reading_id: 'e-m1',
        base_start_at: '2026-01-01T00:00:00Z', base_end_at: '2026-01-31T00:00:00Z',
      },
    };
    if (!(path in responses)) { await route.fulfill({ status: 404, json: { detail: 'Not found' } }); return; }
    await route.fulfill({ json: responses[path] });
  });
  await page.goto('/');
  await selectSyntheticMeter(page);
  await expect(page.getByText(/2026-01-01 — 2026-01-31/)).toBeVisible();
  await expect(page.getByText(/517 kWh/).first()).toBeVisible();
  const billForm = page.locator('form').filter({ hasText: 'Registrar factura' });
  await billForm.getByLabel('Inicio del período').fill('2026-03-01');
  await billForm.getByLabel('Consumo facturado (kWh)').fill('999');
  await page.getByRole('button', { name: 'Comparar', exact: true }).click();
  await expect(page.getByText('No hay lecturas compatibles dentro de ±7 días de cada extremo del período. No se puede calcular la comparación.')).toBeVisible();
  await page.getByRole('button', { name: 'Estimar', exact: true }).click();
  await expect(page.getByText(/Estimación a 30 días: 517\.00 kWh/)).toBeVisible();
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m2');
  await expect(page.getByText(/2026-02-01 — 2026-02-28/)).toBeVisible();
  await expect(page.getByText(/731 kWh/).first()).toBeVisible();
  await expect(page.getByText(/2026-01-01 — 2026-01-31/)).toHaveCount(0);
  await expect(page.getByText(/517 kWh/)).toHaveCount(0);
  // The CU06 draft, CU07 comparison and CU08 estimate from m1 do not survive the switch.
  await expect(billForm.getByLabel('Inicio del período')).toHaveValue('');
  await expect(billForm.getByLabel('Consumo facturado (kWh)')).toHaveValue('');
  await expect(page.getByRole('region', { name: 'Comparación con la factura' })).toHaveCount(0);
  await expect(page.getByText(/Estimación a 30 días/)).toHaveCount(0);
});

test('manual confirmation, stable create retry and edit reconciliation', async ({ page }) => {
  const requests: { key: string | undefined; body: string | null }[] = [];
  let patchBody: string | null = null;
  const calls: string[] = [];
  const row = { id: 'r1', meter_id: 'm1', recorded_at: '2026-01-01T00:00:00Z', value_kwh: '100', has_photo: false, version: 1 };
  await page.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    calls.push(`${request.method()} ${path}`);
    if (path === '/api/meters/m1/readings' && request.method() === 'POST') {
      requests.push({ key: request.headers()['idempotency-key'], body: request.postData() });
      if (requests.length === 1) await route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
      else await route.fulfill({ status: 201, json: row });
      return;
    }
    if (path === '/api/meters/m1/readings/r1' && request.method() === 'PATCH') {
      patchBody = request.postData();
      await route.fulfill({ status: 503, json: { detail: 'Unavailable' } }); return;
    }
    const responses: Record<string, unknown> = {
      '/api/session': { account: { id: 'a', username: 'synthetic' }, csrf_token: 'synthetic' },
      '/api/domiciles': [{ id: 'd', display_address: 'Synthetic domicile' }],
      '/api/domiciles/d/management': { id: 'd', display_address: 'Synthetic domicile', version: 1 },
      '/api/domiciles/d/meters': [{ id: 'm1', domicile_id: 'd', meter_number: 'ONE', alias: null, version: 1 }],
      '/api/domiciles/d/interruptions': [],
      '/api/meters/m1/readings': [],
      '/api/meters/m1/readings/r1': { ...row, version: 2, value_kwh: '90' },
    };
    if (!(path in responses)) { await route.fulfill({ status: 404, json: { detail: 'Not found' } }); return; }
    await route.fulfill({ json: responses[path] });
  });
  await page.goto('/');
  await selectSyntheticMeter(page);
  const form = page.getByRole('form', { name: 'Registrar lectura' });
  await form.getByLabel('Fecha y hora con zona horaria').fill('2026-01-01T00:00:00Z');
  await form.getByLabel('Lectura acumulada en kWh').fill('100');
  await form.getByRole('button', { name: 'Guardar lectura' }).click();
  await expect(form.getByText('Confirmá la lectura antes de guardar.')).toBeVisible();
  expect(requests).toHaveLength(0);
  await form.getByLabel('Confirmo que revisé la lectura').check();
  await form.getByRole('button', { name: 'Guardar lectura' }).click();
  await expect(page.getByRole('button', { name: 'Reintentar la misma creación' })).toBeVisible();
  expect(requests).toHaveLength(1);
  await page.getByRole('button', { name: 'Reintentar la misma creación' }).click();
  await expect(page.getByText('Lectura guardada.')).toBeVisible();
  expect(requests).toHaveLength(2);
  expect(requests[0]?.key).toMatch(/^[0-9a-f-]{36}$/);
  expect(requests[1]).toEqual(requests[0]);
  expect(JSON.parse(requests[0]?.body ?? 'null')).toEqual({ recorded_at: '2026-01-01T00:00:00Z', value_kwh: '100', confirmed: true, photo_base64: null });
  await page.getByRole('button', { name: 'Corregir lectura' }).click();
  const edit = page.getByRole('form', { name: 'Corregir lectura' });
  await edit.getByLabel('Lectura acumulada en kWh').fill('90');
  await edit.getByLabel('Confirmo que revisé la lectura').check();
  await edit.getByRole('button', { name: 'Guardar corrección' }).click();
  await expect(page.getByRole('button', { name: 'Consultar versión actual' })).toBeVisible();
  expect(JSON.parse(patchBody ?? 'null')).toEqual({ recorded_at: '2026-01-01T00:00:00Z', value_kwh: '90', confirmed: true, photo_base64: null, photo_action: 'keep', version: 1 });
  await expect(page.getByRole('form', { name: 'Corregir lectura' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Consultar versión actual' }).click();
  await expect(page.getByLabel('Lectura acumulada en kWh')).toHaveValue('90');
  expect(calls.filter(call => call === 'PATCH /api/meters/m1/readings/r1')).toHaveLength(1);
  expect(calls).toContain('GET /api/meters/m1/readings/r1');
});

test('rechecks history before saving and requires confirmation again when the warning changes', async ({ page }) => {
  let listCalls = 0;
  let posts = 0;
  const prior = { id: 'prior', meter_id: 'm1', recorded_at: '2026-01-01T00:00:00Z', value_kwh: '100', has_photo: false, version: 1 };
  await page.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === '/api/meters/m1/readings' && request.method() === 'GET') {
      listCalls++;
      if (listCalls === 2) { await route.fulfill({ status: 503, json: { detail: 'Unavailable' } }); return; }
      await route.fulfill({ json: listCalls >= 4 ? [prior] : [] }); return;
    }
    if (path === '/api/meters/m1/readings' && request.method() === 'POST') {
      posts++;
      await route.fulfill({ status: 201, json: { ...prior, id: 'new', recorded_at: '2026-01-02T00:00:00Z', value_kwh: '90' } }); return;
    }
    const responses: Record<string, unknown> = {
      '/api/session': { account: { id: 'a', username: 'synthetic' }, csrf_token: 'synthetic' },
      '/api/domiciles': [{ id: 'd', display_address: 'Synthetic domicile' }],
      '/api/domiciles/d/management': { id: 'd', display_address: 'Synthetic domicile', version: 1 },
      '/api/domiciles/d/meters': [{ id: 'm1', domicile_id: 'd', meter_number: 'ONE', alias: null, version: 1 }],
      '/api/domiciles/d/interruptions': [],
    };
    if (!(path in responses)) { await route.fulfill({ status: 404, json: { detail: 'Not found' } }); return; }
    await route.fulfill({ json: responses[path] });
  });
  await page.goto('/');
  await selectSyntheticMeter(page);
  const form = page.getByRole('form', { name: 'Registrar lectura' });
  await form.getByLabel('Fecha y hora con zona horaria').fill('2026-01-02T00:00:00Z');
  await form.getByLabel('Lectura acumulada en kWh').fill('90');
  await form.getByLabel('Confirmo que revisé la lectura').check();
  await form.getByRole('button', { name: 'Guardar lectura' }).click();
  await expect(page.getByText('No se pudo comprobar el historial. Actualizá las lecturas y revisá antes de confirmar.')).toBeVisible();
  expect(posts).toBe(0);
  await expect(form.getByLabel('Confirmo que revisé la lectura')).not.toBeChecked();
  await page.getByRole('button', { name: 'Actualizar lecturas' }).click();
  await form.getByLabel('Confirmo que revisé la lectura').check();
  await form.getByRole('button', { name: 'Guardar lectura' }).click();
  await expect(page.getByText('La lectura es menor que la lectura anterior. Revisala; podés confirmarla igualmente.')).toBeVisible();
  await expect(form.getByLabel('Confirmo que revisé la lectura')).not.toBeChecked();
  expect(posts).toBe(0);
  await form.getByLabel('Confirmo que revisé la lectura').check();
  await form.getByRole('button', { name: 'Guardar lectura' }).click();
  await expect(page.getByText('Lectura guardada.')).toBeVisible();
  expect(posts).toBe(1);
});

test('photo selection, OCR fallback and explicit remove stay unconfirmed until the owner saves', async ({ page }) => {
  const fallback = 'No pudimos identificar con seguridad la lectura del medidor. Intentá subir una fotografía más clara o ingresá manualmente el valor en kWh';
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
  const row = { id: 'r1', meter_id: 'm1', recorded_at: '2026-11-07T15:00:00Z', value_kwh: '100', has_photo: true, version: 1 };
  let createBody: Record<string, unknown> | null = null;
  let ocrBody: Record<string, unknown> | null = null;
  let patchBody: Record<string, unknown> | null = null;
  await page.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === '/api/meters/m1/readings' && request.method() === 'POST') {
      createBody = JSON.parse(request.postData() ?? 'null') as Record<string, unknown>;
      await route.fulfill({ status: 201, json: row }); return;
    }
    if (path === '/api/meters/m1/readings/ocr' && request.method() === 'POST') {
      ocrBody = JSON.parse(request.postData() ?? 'null') as Record<string, unknown>;
      await route.fulfill({ json: { status: 'abstained', value_kwh: null, message: fallback } }); return;
    }
    if (path === '/api/meters/m1/readings/r1' && request.method() === 'PATCH') {
      patchBody = JSON.parse(request.postData() ?? 'null') as Record<string, unknown>;
      await route.fulfill({ json: { ...row, has_photo: false, version: 2 } }); return;
    }
    const responses: Record<string, unknown> = {
      '/api/session': { account: { id: 'a', username: 'synthetic' }, csrf_token: 'synthetic' },
      '/api/domiciles': [{ id: 'd', display_address: 'Synthetic domicile' }],
      '/api/domiciles/d/management': { id: 'd', display_address: 'Synthetic domicile', version: 1 },
      '/api/domiciles/d/meters': [{ id: 'm1', domicile_id: 'd', meter_number: 'ONE', alias: null, version: 1 }],
      '/api/domiciles/d/interruptions': [],
      '/api/meters/m1/readings': [row],
    };
    if (!(path in responses)) { await route.fulfill({ status: 404, json: { detail: 'Not found' } }); return; }
    await route.fulfill({ json: responses[path] });
  });
  await page.goto('/');
  await selectSyntheticMeter(page);
  const form = page.getByRole('form', { name: 'Registrar lectura' });
  await expect(form.getByLabel(/Fotografía/)).toBeVisible();
  await form.getByLabel(/Fotografía/).setInputFiles({ name: 'synthetic.png', mimeType: 'image/png', buffer: png });
  await expect(form.getByText(/1×1/)).toBeVisible();
  await form.getByRole('button', { name: 'Leer dígitos con OCR' }).click();
  await expect(form.getByText(fallback, { exact: true })).toBeVisible();
  await expect(form.getByLabel('Lectura acumulada en kWh')).toHaveValue('');
  expect(ocrBody).not.toBeNull();
  expect(Buffer.from(String(ocrBody?.['photo_base64']), 'base64').equals(png)).toBe(true);
  expect(ocrBody?.['crop']).toEqual({ x: 0, y: 0, width: 1, height: 1 });

  await form.getByLabel('Fecha y hora con zona horaria').fill('2026-11-07T15:00:00Z');
  await form.getByLabel('Lectura acumulada en kWh').fill('100');
  await form.getByLabel('Confirmo que revisé la lectura').check();
  await form.getByRole('button', { name: 'Guardar lectura' }).click();
  await expect(page.getByText('Lectura guardada.')).toBeVisible();
  expect(createBody).not.toBeNull();
  expect(createBody?.['photo_base64'] === null).toBe(false);
  expect(Buffer.from(String(createBody?.['photo_base64']), 'base64').equals(png)).toBe(true);
  expect(createBody).not.toHaveProperty('photo_action');

  await page.getByRole('button', { name: 'Corregir lectura' }).click();
  const edit = page.getByRole('form', { name: 'Corregir lectura' });
  await expect(edit.getByText('Esta lectura tiene una fotografía adjunta.')).toBeVisible();
  await edit.getByRole('button', { name: 'Quitar foto al guardar' }).click();
  await expect(edit.getByText('La fotografía actual se quitará al guardar.')).toBeVisible();
  await edit.getByLabel('Confirmo que revisé la lectura').check();
  await edit.getByRole('button', { name: 'Guardar corrección' }).click();
  await expect(page.getByText('Lectura corregida.')).toBeVisible();
  expect(patchBody?.['photo_action']).toBe('remove');
  expect(patchBody?.['photo_base64']).toBeNull();
  await expect(page.getByRole('button', { name: 'Ver foto' })).toHaveCount(0);
});

test('an OCR suggestion only fills an editable field and never saves without confirmation', async ({ page }) => {
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
  const row = { id: 'r1', meter_id: 'm1', recorded_at: '2026-11-07T15:00:00Z', value_kwh: '12345', has_photo: true, version: 1 };
  let creates = 0;
  let posted: Record<string, unknown> | null = null;
  await page.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === '/api/meters/m1/readings/ocr' && request.method() === 'POST') {
      await route.fulfill({ json: { status: 'suggested', value_kwh: '12345' } }); return;
    }
    if (path === '/api/meters/m1/readings' && request.method() === 'POST') {
      creates++;
      posted = JSON.parse(request.postData() ?? 'null') as Record<string, unknown>;
      await route.fulfill({ status: 201, json: row }); return;
    }
    const responses: Record<string, unknown> = {
      '/api/session': { account: { id: 'a', username: 'synthetic' }, csrf_token: 'synthetic' },
      '/api/domiciles': [{ id: 'd', display_address: 'Synthetic domicile' }],
      '/api/domiciles/d/management': { id: 'd', display_address: 'Synthetic domicile', version: 1 },
      '/api/domiciles/d/meters': [{ id: 'm1', domicile_id: 'd', meter_number: 'ONE', alias: null, version: 1 }],
      '/api/domiciles/d/interruptions': [],
      '/api/meters/m1/readings': [],
    };
    if (!(path in responses)) { await route.fulfill({ status: 404, json: { detail: 'Not found' } }); return; }
    await route.fulfill({ json: responses[path] });
  });
  await page.goto('/');
  await selectSyntheticMeter(page);
  const form = page.getByRole('form', { name: 'Registrar lectura' });
  await form.getByLabel('Fecha y hora con zona horaria').fill('2026-11-07T15:00:00Z');
  await form.getByLabel(/Fotografía/).setInputFiles({ name: 'synthetic.png', mimeType: 'image/png', buffer: png });
  await expect(form.getByText(/1×1/)).toBeVisible();
  await form.getByRole('button', { name: 'Leer dígitos con OCR' }).click();
  await expect(form.getByLabel('Lectura acumulada en kWh')).toHaveValue('12345');
  await expect(form.getByText('Valor sugerido por OCR. Revisalo y confirmá antes de guardar.')).toBeVisible();
  await expect(form.getByLabel('Confirmo que revisé la lectura')).not.toBeChecked();
  expect(creates).toBe(0);
  await form.getByLabel('Lectura acumulada en kWh').fill('12346');
  await form.getByRole('button', { name: 'Guardar lectura' }).click();
  await expect(form.getByText('Confirmá la lectura antes de guardar.')).toBeVisible();
  expect(creates).toBe(0);
  await form.getByLabel('Confirmo que revisé la lectura').check();
  await form.getByRole('button', { name: 'Guardar lectura' }).click();
  await expect(page.getByText('Lectura guardada.')).toBeVisible();
  expect(creates).toBe(1);
  expect(posted?.['value_kwh']).toBe('12346');
});
