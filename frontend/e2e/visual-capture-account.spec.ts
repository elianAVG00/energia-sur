import path from 'node:path';
import { mkdir } from 'node:fs/promises';
import { expect, test } from '@playwright/test';
import type { Page, Route } from '@playwright/test';

// Evidence-only spec for the Mi cuenta redesign. Never runs in the regular gate
// unless VISUAL_CAPTURE=1. Every fixture is synthetic.
test.skip(process.env.VISUAL_CAPTURE !== '1', 'Set VISUAL_CAPTURE=1 to write evidence screenshots.');

const OUT_DIR = process.env.VISUAL_DIR;

const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'tablet', width: 820, height: 1180 },
  { name: 'mobile', width: 390, height: 844 },
] as const;

const DOMICILE = { id: 'd', display_address: 'Domicilio sintético 100' };
const METERS = [
  { id: 'm1', domicile_id: 'd', meter_number: '001-A', alias: 'Casa', version: 1 },
  { id: 'm2', domicile_id: 'd', meter_number: '002-B', alias: null, version: 1 },
];
const READING = {
  id: 'r1', meter_id: 'm1', recorded_at: '2026-10-31T15:00:00Z',
  value_kwh: '1200', has_photo: true, version: 1,
};
const BILL = {
  id: 'b1', meter_id: 'm1', period_start: '2026-10-01', period_end: '2026-10-31',
  value_kwh: '100.5', amount_ars: '15000.00', file_type: 'application/pdf', version: 1,
};
const CUT = {
  id: 'c1', domicile_id: 'd', start_at: '2026-11-01T10:00:00-03:00',
  end_at: '2026-11-01T11:00:00-03:00', observations: 'Corte sintético',
  complaint_number: 'TEST-001', version: 1, status: 'closed',
};
const OPEN_CUT = {
  id: 'c2', domicile_id: 'd', start_at: '2026-11-01T12:00:00-03:00',
  end_at: null, observations: null, complaint_number: null, version: 1, status: 'ongoing',
};
const CURRENT_CUT = { ...CUT, version: 2, observations: 'Versión actual del servidor' };
const SUMMARY = {
  domicile: DOMICILE, period_start: '2026-11-01T00:00:00-03:00',
  period_end: '2026-11-02T00:00:00-03:00', generated_at: '2026-11-02T09:00:00-03:00',
  timezone: 'America/Argentina/Buenos_Aires', total_minutes: 60, total_hours: 1,
  remaining_minutes: 0, entries: [CUT],
};
const INTERVAL = {
  start_reading_id: 'r0', end_reading_id: 'r1',
  start_at: '2026-10-01T15:00:00Z', end_at: '2026-10-31T15:00:00Z',
  start_local_date: '2026-10-01', end_local_date: '2026-10-31',
  start_value_kwh: '900', end_value_kwh: '1200',
  consumption_kwh: '300', daily_average_kwh_day: '10.00',
  calculable: true, sub_day: false, below_minimum: false,
};
const CANDIDATE_START = {
  reading_id: 'rs', recorded_at: '2026-09-30T15:00:00Z', local_date: '2026-09-30',
  value_kwh: '900', version: 1,
};
const CANDIDATE_END = {
  reading_id: 're', recorded_at: '2026-10-31T15:00:00Z', local_date: '2026-10-31',
  value_kwh: '1020', version: 1,
};
const COMPARISON_RESULT = {
  bill_id: 'b1', meter_id: 'm1', period_start: '2026-10-01', period_end: '2026-10-31',
  billed_kwh: '100.5', status: 'comparable', reason: null, exact: true,
  start_reading: { ...CANDIDATE_START, local_date: '2026-10-01' },
  end_reading: { ...CANDIDATE_END, value_kwh: '1200' },
  recorded_kwh: '300', difference_kwh: '199.5', outcome: 'recorded_higher',
};
const ESTIMATE = {
  meter_id: 'm1', status: 'available', days: 30, daily_average_kwh_day: '10.00',
  estimate_kwh: '300.00', orientative: true, below_minimum: false,
  daily_average_below_minimum: false, sub_day: false,
  base_start_reading_id: 'r0', base_end_reading_id: 'r1',
  base_start_at: '2026-10-01T15:00:00Z', base_end_at: '2026-10-31T15:00:00Z',
};

type Scene =
  | 'sin-domicilio'
  | 'sin-medidor'
  | 'dos-medidores'
  | 'dos-medidores-seleccionado'
  | 'cambio-medidor'
  | 'lecturas'
  | 'lectura-advertencia'
  | 'fotografia-ocr'
  | 'sin-registros'
  | 'facturas'
  | 'factura-superposicion'
  | 'comparacion'
  | 'comparacion-sin-datos'
  | 'comparacion-advertencias'
  | 'consumo'
  | 'consumo-real'
  | 'promedio-diario'
  | 'estimacion'
  | 'estimacion-poco-representativa'
  | 'consumo-vacio'
  | 'consumo-error'
  | 'cortes'
  | 'diario-historial'
  | 'diario-registro'
  | 'diario-correccion'
  | 'diario-cierre'
  | 'diario-conflicto'
  | 'diario-resumen-pdf'
  | 'diario-vacio-error';

const SCENES: readonly Scene[] = [
  'sin-domicilio', 'sin-medidor', 'dos-medidores', 'dos-medidores-seleccionado',
  'cambio-medidor', 'lecturas', 'lectura-advertencia', 'fotografia-ocr',
  'sin-registros', 'facturas', 'factura-superposicion', 'comparacion',
  'comparacion-sin-datos', 'comparacion-advertencias', 'consumo', 'consumo-real',
  'promedio-diario', 'estimacion', 'estimacion-poco-representativa', 'consumo-vacio',
  'consumo-error', 'cortes', 'diario-historial', 'diario-registro', 'diario-correccion',
  'diario-cierre', 'diario-conflicto', 'diario-resumen-pdf', 'diario-vacio-error',
];

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
}

async function mockAccount(page: Page, scene: Scene): Promise<void> {
  let diaryRows = ['diario-historial', 'diario-correccion', 'diario-cierre', 'diario-conflicto'].includes(scene)
    ? [CUT, OPEN_CUT]
    : scene === 'cortes' ? [CUT] : [];
  await page.route('**/api/**', async route => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;

    if (path === '/api/session') {
      return json(route, { account: { id: 'synthetic', username: 'synthetic' }, csrf_token: 'synthetic' });
    }
    if (path === '/api/domiciles') {
      return json(route, scene === 'sin-domicilio' ? [] : [DOMICILE]);
    }
    if (path === '/api/domiciles/d/management') {
      return json(route, { ...DOMICILE, version: 1 });
    }
    if (path === '/api/domiciles/d/meters') {
      return json(route, scene === 'sin-medidor' ? [] : METERS);
    }
    if (path === '/api/domiciles/d/interruptions') {
      if (request.method() === 'GET') return json(route, diaryRows);
      if (request.method() === 'POST') {
        return json(route, { ...CUT, id: 'c-new', start_at: '2026-11-01T09:00:00-03:00' }, 201);
      }
    }
    if (path === '/api/interruptions/c1' && request.method() === 'PATCH') {
      if (scene === 'diario-conflicto') {
        diaryRows = diaryRows.map(row => row.id === CUT.id ? CURRENT_CUT : row);
        return json(route, { detail: 'La versión cambió.', code: 'VERSION_CONFLICT' }, 409);
      }
      return json(route, { ...CUT, version: 3 });
    }
    if (path === '/api/interruptions/c2/close' && request.method() === 'POST') {
      return json(route, { ...OPEN_CUT, end_at: '2026-11-01T12:30:00-03:00', status: 'closed', version: 2 });
    }
    if (path === '/api/domiciles/d/summary') {
      return scene === 'diario-vacio-error'
        ? json(route, { detail: 'No se pudo generar el resumen.' }, 503)
        : json(route, SUMMARY);
    }
    if (path === '/api/domiciles/d/report.pdf') {
      return json(route, { detail: 'Synthetic PDF response.' }, 503);
    }
    if (path === '/api/meters/m1/readings') {
      return json(route, ['lecturas', 'lectura-advertencia', 'fotografia-ocr', 'dos-medidores-seleccionado', 'cambio-medidor'].includes(scene) ? [READING] : []);
    }
    if (path === '/api/meters/m2/readings') {
      return json(route, []);
    }
    if (path === '/api/meters/m1/bills' && request.method() === 'GET') {
      return json(route, scene === 'facturas' || scene.startsWith('comparacion') ? [BILL] : []);
    }
    if (path === '/api/meters/m1/bills' && request.method() === 'POST' && scene === 'factura-superposicion') {
      return json(route, {
        detail: 'Revisá los períodos superpuestos.', code: 'OVERLAP_CONFIRMATION_REQUIRED',
        overlap_token: 'synthetic-overlap-token',
        overlaps: [{ id: 'b-existing', period_start: '2026-10-01', period_end: '2026-10-31', version: 1 }],
      }, 409);
    }
    if (path === '/api/meters/m1/readings/ocr' && request.method() === 'POST') {
      return json(route, { status: 'suggested', value_kwh: '1234' });
    }
    if (path === '/api/meters/m2/bills') {
      return json(route, []);
    }
    if (path === '/api/meters/m1/bills/b1/comparison-candidates') {
      if (scene === 'comparacion-sin-datos') {
        return json(route, {
          bill_id: 'b1', meter_id: 'm1', period_start: BILL.period_start, period_end: BILL.period_end,
          billed_kwh: BILL.value_kwh, start_candidates: [], end_candidates: [],
        });
      }
      const start = scene === 'comparacion-advertencias' ? CANDIDATE_START
        : { ...CANDIDATE_START, local_date: '2026-10-01' };
      return json(route, {
        bill_id: 'b1', meter_id: 'm1', period_start: '2026-10-01', period_end: '2026-10-31',
        billed_kwh: '100.5', start_candidates: [start], end_candidates: [CANDIDATE_END],
      });
    }
    if (path === '/api/meters/m1/bills/b1/comparison') {
      return json(route, scene === 'comparacion-advertencias'
        ? { ...COMPARISON_RESULT, exact: false }
        : COMPARISON_RESULT);
    }
    if (path === '/api/meters/m1/consumption-evolution') {
      if (scene === 'consumo-vacio') return json(route, { meter_id: 'm1', intervals: [] });
      if (scene === 'consumo-error') return json(route, { detail: 'Servicio de consumo no disponible.' }, 500);
      return json(route, { meter_id: 'm1', intervals: [INTERVAL] });
    }
    if (path === '/api/meters/m1/consumption-estimate') {
      return json(route, scene === 'estimacion-poco-representativa'
        ? { ...ESTIMATE, sub_day: true, base_start_at: '2026-10-31T15:00:00Z', base_end_at: '2026-10-31T20:00:00Z' }
        : ESTIMATE);
    }
    return json(route, { detail: 'not mocked' }, 404);
  });
}

async function capture(page: Page, name: string): Promise<void> {
  if (!OUT_DIR) throw new Error('VISUAL_DIR is required when VISUAL_CAPTURE=1.');
  await mkdir(OUT_DIR, { recursive: true });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: path.join(OUT_DIR, name), fullPage: true });
}

async function prepare(page: Page, scene: Scene): Promise<void> {
  await page.goto('/');
  await page.addStyleTag({ content: '*, *::before, *::after { transition: none !important; animation: none !important; }' });
  await expect(page.getByRole('heading', { name: 'Domicilios' })).toBeVisible();
  if (scene === 'sin-domicilio') {
    await expect(page.getByText('Registrá un domicilio para empezar. No se necesita medidor.')).toBeVisible();
    return;
  }
  if (scene === 'sin-medidor') {
    await expect(page.getByText('No hay medidores registrados. El domicilio puede usarse sin medidor.')).toBeVisible();
    return;
  }
  if (scene === 'dos-medidores') {
    await expect(page.getByLabel('Medidor para consultar lecturas')).toBeVisible();
    return;
  }
  if (scene === 'dos-medidores-seleccionado') {
    await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
    await expect(page.getByText(/1200 kWh/)).toBeVisible();
    return;
  }
  if (scene === 'cambio-medidor') {
    await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
    await expect(page.getByText(/1200 kWh/)).toBeVisible();
    await page.getByLabel('Medidor para consultar lecturas').selectOption('m2');
    await expect(page.getByText('No hay lecturas registradas.')).toBeVisible();
    return;
  }
  if (scene === 'sin-registros') {
    await page.getByLabel('Medidor para consultar lecturas').selectOption('m2');
    await expect(page.getByText('No hay lecturas registradas.')).toBeVisible();
    await expect(page.getByText('No hay facturas registradas.')).toBeVisible();
    return;
  }
  if (scene === 'cortes') {
    await page.getByLabel('Desde', { exact: true }).fill('2026-11-01T00:00');
    await page.getByLabel('Hasta', { exact: true }).fill('2026-11-02T00:00');
    await page.getByRole('button', { name: 'Consultar resumen', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Total sin servicio: 1 h 0 min', exact: true })).toBeVisible();
    return;
  }
  if (scene.startsWith('diario-')) {
    const form = page.getByRole('form', { name: 'Registrar corte', exact: true });
    if (scene === 'diario-registro') {
      await form.getByLabel('Inicio', { exact: true }).fill('2026-11-01T09:00');
      await form.getByLabel('Fin (opcional si está en curso)', { exact: true }).fill('');
      return;
    }
    if (scene === 'diario-correccion' || scene === 'diario-conflicto') {
      await page.getByRole('button', { name: 'Corregir', exact: true }).first().click();
      const editor = page.getByRole('form', { name: 'Corregir corte', exact: true });
      await editor.getByLabel('Inicio', { exact: true }).fill('2026-11-01T10:15');
      if (scene === 'diario-conflicto') {
        const conflictResponse = page.waitForResponse(response =>
          response.request().method() === 'PATCH' && response.url().endsWith('/api/interruptions/c1'));
        await editor.getByRole('button', { name: 'Guardar corrección', exact: true }).click();
        expect((await conflictResponse).status()).toBe(409);
        await expect(page.getByRole('button', { name: 'Descartar borrador y recargar', exact: true })).toBeVisible();
      }
      return;
    }
    if (scene === 'diario-cierre') {
      await page.getByRole('button', { name: 'Cerrar corte', exact: true }).click();
      await page.getByLabel('Fecha de cierre', { exact: true }).fill('2026-11-01T12:30');
      return;
    }
    if (scene === 'diario-resumen-pdf' || scene === 'diario-vacio-error') {
      await page.getByLabel('Desde', { exact: true }).fill('2026-11-01T00:00');
      await page.getByLabel('Hasta', { exact: true }).fill('2026-11-02T00:00');
      await page.getByRole('button', { name: 'Consultar resumen', exact: true }).click();
      if (scene === 'diario-resumen-pdf') {
        await expect(page.getByRole('button', { name: 'Descargar PDF', exact: true })).toBeVisible();
      } else {
        await expect(page.getByRole('alert')).toBeVisible();
      }
      return;
    }
    if (scene === 'diario-historial') return;
  }
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
  if (scene === 'lecturas') {
    await expect(page.getByText(/1200 kWh/)).toBeVisible();
  }
  if (scene === 'lectura-advertencia') {
    await page.getByLabel('Fecha y hora con zona horaria').fill('2026-11-01T15:00:00Z');
    await page.getByLabel('Lectura acumulada en kWh').fill('1100');
    await expect(page.getByText('La lectura es menor que la lectura anterior. Revisala; podés confirmarla igualmente.')).toBeVisible();
  }
  if (scene === 'fotografia-ocr') {
    const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
    const form = page.getByRole('form', { name: 'Registrar lectura' });
    await form.getByLabel(/Fotografía/).setInputFiles({ name: 'sintetica.png', mimeType: 'image/png', buffer: png });
    await expect(form.getByRole('img', { name: 'Vista previa de la fotografía' })).toBeVisible();
    await form.getByRole('button', { name: 'Leer dígitos con OCR' }).click();
    await expect(form.getByText('Valor sugerido por OCR. Revisalo y confirmá antes de guardar.')).toBeVisible();
  }
  if (scene === 'facturas') {
    await expect(page.getByText(/2026-10-01 — 2026-10-31/)).toBeVisible();
  }
  if (scene === 'factura-superposicion') {
    const form = page.locator('form').filter({ hasText: 'Registrar factura' });
    await form.getByLabel('Inicio del período').fill('2026-10-15');
    await form.getByLabel('Fin del período').fill('2026-11-15');
    await form.getByLabel('Consumo facturado (kWh)').fill('88.25');
    const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
    await form.getByLabel('Archivo obligatorio').setInputFiles({ name: 'sintetica.png', mimeType: 'image/png', buffer: png });
    await form.getByRole('button', { name: 'Guardar factura' }).click();
    await expect(form.getByRole('button', { name: 'Confirmar superposición y guardar' })).toBeVisible();
  }
  if (scene === 'comparacion' || scene === 'comparacion-advertencias' || scene === 'comparacion-sin-datos') {
    await page.getByRole('button', { name: 'Comparar', exact: true }).click();
    await expect(page.getByRole('region', { name: 'Comparación con la factura' })).toBeVisible();
    if (scene === 'comparacion-advertencias') {
      await page.getByLabel('Confirmo que quiero comparar con estas fechas aproximadas.').check();
      await page.getByRole('button', { name: 'Calcular comparación' }).click();
      await expect(page.getByText(/Comparación aproximada/)).toBeVisible();
    } else if (scene === 'comparacion-sin-datos') {
      await expect(page.getByText(/No hay lecturas compatibles/)).toBeVisible();
    } else {
      await expect(page.getByText('Diferencia')).toBeVisible();
    }
  }
  if (['consumo', 'consumo-real', 'promedio-diario', 'estimacion', 'estimacion-poco-representativa', 'consumo-vacio', 'consumo-error'].includes(scene)) {
    if (scene === 'consumo-error' || scene === 'consumo-vacio') {
      if (scene === 'consumo-error') {
        await expect(page.locator('#consumo').getByRole('alert')).toBeVisible();
      } else {
        await expect(page.locator('#consumo').getByText('No hay suficientes lecturas para mostrar la evolución.')).toBeVisible();
      }
      return;
    }
    await expect(page.getByRole('heading', { name: 'Consumo real (kWh)', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Promedio diario (kWh/día)', exact: true })).toBeVisible();
    if (scene === 'consumo-real') return;
    if (scene === 'promedio-diario') return;
    await page.getByRole('button', { name: 'Estimar', exact: true }).click();
    await expect(page.getByText('300.00 kWh')).toBeVisible();
    if (scene === 'estimacion-poco-representativa') {
      await expect(page.getByText(/poco representativo/)).toBeVisible();
    }
  }
}

for (const scene of SCENES) {
  test(`captures Mi cuenta ${scene}`, async ({ page }) => {
    await mockAccount(page, scene);
    for (const viewport of VIEWPORTS) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await prepare(page, scene);
      await capture(page, `cuenta-${scene}-${viewport.name}.png`);
    }
  });
}
