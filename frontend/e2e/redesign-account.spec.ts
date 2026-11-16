import { expect, test } from '@playwright/test';
import type { Page, Route } from '@playwright/test';

const DOMICILE = { id: 'd', display_address: 'Domicilio sintético 100' };
const SECOND_DOMICILE = { id: 'd2', display_address: 'Domicilio sintético 200' };
const METERS = [
  { id: 'm1', domicile_id: 'd', meter_number: '001-A', alias: 'Casa', version: 1 },
  { id: 'm2', domicile_id: 'd', meter_number: '002-B', alias: null, version: 1 },
];
const READING = {
  id: 'r1', meter_id: 'm1', recorded_at: '2026-10-31T15:00:00Z',
  value_kwh: '1200', has_photo: true, version: 1,
};
const SECOND_READING = {
  id: 'r2', meter_id: 'm2', recorded_at: '2026-10-30T15:00:00Z',
  value_kwh: '77', has_photo: false, version: 1,
};
const BILL = {
  id: 'b1', meter_id: 'm1', period_start: '2026-10-01', period_end: '2026-10-31',
  value_kwh: '100.5', amount_ars: '15000.00', file_type: 'application/pdf', version: 1,
};
const INTERVAL = {
  start_reading_id: 'r0', end_reading_id: 'r1',
  start_at: '2026-10-01T15:00:00Z', end_at: '2026-10-31T15:00:00Z',
  start_local_date: '2026-10-01', end_local_date: '2026-10-31',
  start_value_kwh: '900', end_value_kwh: '1200',
  consumption_kwh: '300', daily_average_kwh_day: '10.00',
  calculable: true, sub_day: false, below_minimum: false,
};
const START_CANDIDATE = {
  reading_id: 'rs', recorded_at: '2026-10-01T15:00:00Z', local_date: '2026-10-01',
  value_kwh: '900', version: 1,
};
const END_CANDIDATE = {
  reading_id: 're', recorded_at: '2026-10-31T15:00:00Z', local_date: '2026-10-31',
  value_kwh: '1200', version: 1,
};
const COMPARISON_RESULT = {
  bill_id: 'b1', meter_id: 'm1', period_start: '2026-10-01', period_end: '2026-10-31',
  billed_kwh: '100.5', status: 'comparable', reason: null, exact: true,
  start_reading: START_CANDIDATE, end_reading: END_CANDIDATE,
  recorded_kwh: '300', difference_kwh: '199.5', outcome: 'recorded_higher',
};
const ESTIMATE = {
  meter_id: 'm1', status: 'available', days: 30, daily_average_kwh_day: '10.00',
  estimate_kwh: '300.00', orientative: true, below_minimum: false,
  daily_average_below_minimum: false, sub_day: false,
  base_start_reading_id: 'r0', base_end_reading_id: 'r1',
  base_start_at: '2026-10-01T15:00:00Z', base_end_at: '2026-10-31T15:00:00Z',
};
const EMPTY_METER_GUIDANCE = 'Este domicilio no tiene medidores registrados. El diario sigue disponible sin medidor.';
interface MockCut {
  id: string; domicile_id: string; start_at: string; end_at: string | null;
  observations: string | null; complaint_number: string | null; version: number;
  status: 'closed' | 'ongoing';
}
const CLOSED_CUT = {
  id: 'c1', domicile_id: 'd', start_at: '2026-11-01T10:00:00-03:00',
  end_at: '2026-11-01T11:00:00-03:00', observations: 'Observación sintética',
  complaint_number: 'TEST-001', version: 1, status: 'closed',
} as const;
const ONGOING_CUT = {
  id: 'c2', domicile_id: 'd', start_at: '2026-11-01T12:00:00-03:00',
  end_at: null, observations: null, complaint_number: null, version: 1, status: 'ongoing',
} as const;
const CURRENT_CUT = { ...CLOSED_CUT, version: 2, observations: 'Versión actual del servidor' } as const;
const SUMMARY = {
  domicile: DOMICILE, period_start: '2026-11-01T00:00:00-03:00',
  period_end: '2026-11-02T00:00:00-03:00', generated_at: '2026-11-02T09:00:00-03:00',
  timezone: 'America/Argentina/Buenos_Aires', total_minutes: 180, total_hours: 3,
  remaining_minutes: 0, entries: [CLOSED_CUT, ONGOING_CUT],
};
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');

interface Options {
  domiciles?: 'none' | 'multiple';
  meters?: 'none';
  addressConflict?: boolean;
  meterConflict?: boolean;
  metersError?: boolean;
  secondMeterReading?: boolean;
  comparisonMode?: 'none' | 'error' | 'approximate';
  comparisonOutcome?: 'no_comparison' | 'billed_higher' | 'equal';
  evolutionError?: boolean;
  estimateMode?: 'available' | 'unavailable' | 'sub-day' | 'error';
  diary?: 'records';
  diaryConflict?: boolean;
  summaryError?: boolean;
  pdfError?: boolean;
}

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
}

function isCutInput(value: unknown): value is {
  start_at: string; end_at: string | null; observations: string | null; complaint_number: string | null;
} {
  return typeof value === 'object' && value !== null &&
    'start_at' in value && typeof value.start_at === 'string' &&
    'end_at' in value && (value.end_at === null || typeof value.end_at === 'string') &&
    'observations' in value && (value.observations === null || typeof value.observations === 'string') &&
    'complaint_number' in value && (value.complaint_number === null || typeof value.complaint_number === 'string');
}

function responseTimestamp(localMinute: string): string {
  return `${localMinute}:00-03:00`;
}

async function mockAccount(page: Page, options: Options = {}): Promise<string[]> {
  const requests: string[] = [];
  let diaryRows: MockCut[] = options.diary === 'records' ? [CLOSED_CUT, ONGOING_CUT] : [];
  let returnConflict = options.diaryConflict ?? false;
  await page.route('**/api/**', async route => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    requests.push(path);
    if (path === '/api/session') {
      return json(route, { account: { id: 'synthetic', username: 'synthetic' }, csrf_token: 'synthetic' });
    }
    if (path === '/api/domiciles') return json(route, options.domiciles === 'none' ? [] : options.domiciles === 'multiple' ? [DOMICILE, SECOND_DOMICILE] : [DOMICILE]);
    if (path === '/api/domiciles/d/management') return json(route, { ...DOMICILE, version: 1 });
    if (path === '/api/domiciles/d2/management') return json(route, { ...SECOND_DOMICILE, version: 1 });
    if (path === '/api/domiciles/d2/management') return json(route, { ...SECOND_DOMICILE, version: 1 });
    if (path === '/api/domiciles/d' && request.method() === 'PATCH') {
      return options.addressConflict
        ? json(route, { detail: 'La versión cambió.', code: 'VERSION_CONFLICT' }, 409)
        : json(route, { ...DOMICILE, version: 2 });
    }
    if (path === '/api/domiciles/d/meters' || path === '/api/domiciles/d2/meters') {
      return options.metersError
        ? json(route, { detail: 'Servicio no disponible.' }, 500)
        : json(route, path.includes('/d2/') || options.meters === 'none' ? [] : METERS);
    }
    if (path === '/api/domiciles/d/meters/m1' && request.method() === 'PATCH') {
      return options.meterConflict
        ? json(route, { detail: 'La versión cambió.', code: 'VERSION_CONFLICT' }, 409)
        : json(route, { ...METERS[0], alias: 'Casa corregida', version: 2 });
    }
    if (path === '/api/domiciles/d/interruptions' && request.method() === 'GET') return json(route, diaryRows);
    if (path === '/api/domiciles/d2/interruptions' && request.method() === 'GET') return json(route, []);
    if (path === '/api/domiciles/d/interruptions' && request.method() === 'POST') {
      const input: unknown = request.postDataJSON();
      if (!isCutInput(input)) return json(route, { detail: 'Invalid synthetic payload.' }, 422);
      const status: MockCut['status'] = input.end_at ? 'closed' : 'ongoing';
      const created: MockCut = {
        ...input, start_at: responseTimestamp(input.start_at),
        end_at: input.end_at ? responseTimestamp(input.end_at) : null,
        id: 'c-new', domicile_id: 'd', version: 1, status,
      };
      diaryRows = [created, ...diaryRows];
      return json(route, created, 201);
    }
    if (path === '/api/interruptions/c1' && request.method() === 'PATCH') {
      if (returnConflict) {
        returnConflict = false;
        diaryRows = diaryRows.map(row => row.id === 'c1' ? CURRENT_CUT : row);
        return json(route, { detail: 'La versión cambió.', code: 'VERSION_CONFLICT' }, 409);
      }
      const input: unknown = request.postDataJSON();
      if (!isCutInput(input)) return json(route, { detail: 'Invalid synthetic payload.' }, 422);
      const updated: MockCut = {
        ...CLOSED_CUT, ...input, start_at: responseTimestamp(input.start_at),
        end_at: input.end_at ? responseTimestamp(input.end_at) : null, version: 3,
      };
      diaryRows = diaryRows.map(row => row.id === 'c1' ? updated : row);
      return json(route, updated);
    }
    if (path === '/api/interruptions/c2/close' && request.method() === 'POST') {
      const input: unknown = request.postDataJSON();
      if (typeof input !== 'object' || input === null || !('end_at' in input) || typeof input.end_at !== 'string') {
        return json(route, { detail: 'Invalid synthetic payload.' }, 422);
      }
      const closed: MockCut = {
        ...ONGOING_CUT, end_at: responseTimestamp(input.end_at), status: 'closed', version: 2,
      };
      diaryRows = diaryRows.map(row => row.id === 'c2' ? closed : row);
      return json(route, closed);
    }
    if (path === '/api/domiciles/d/summary') {
      return options.summaryError
        ? json(route, { detail: 'No se pudo generar el resumen.' }, 503)
        : json(route, SUMMARY);
    }
    if (path === '/api/domiciles/d/report.pdf') {
      return options.pdfError
        ? json(route, { detail: 'No se pudo generar el PDF.' }, 503)
        : route.fulfill({ status: 200, contentType: 'application/pdf', body: Buffer.from('%PDF-1.4 synthetic') });
    }
    if (path === '/api/meters/m1/readings/r1/photo') {
      return route.fulfill({ status: 200, contentType: 'image/png', body: PNG });
    }
    if (path === '/api/meters/m1/readings') return json(route, [READING]);
    if (path === '/api/meters/m2/readings') return json(route, options.secondMeterReading ? [SECOND_READING] : []);
    if (path === '/api/meters/m1/bills') return json(route, [BILL]);
    if (path === '/api/meters/m2/bills') return json(route, []);
    if (path === '/api/meters/m1/bills/b1/comparison-candidates') {
      if (options.comparisonMode === 'error') return json(route, { detail: 'Servicio no disponible.' }, 500);
      if (options.comparisonMode === 'none') {
        return json(route, { bill_id: 'b1', meter_id: 'm1', period_start: BILL.period_start, period_end: BILL.period_end, billed_kwh: BILL.value_kwh, start_candidates: [], end_candidates: [] });
      }
      const start = options.comparisonMode === 'approximate'
        ? { ...START_CANDIDATE, local_date: '2026-09-30' }
        : START_CANDIDATE;
      return json(route, {
        bill_id: 'b1', meter_id: 'm1', period_start: BILL.period_start, period_end: BILL.period_end,
        billed_kwh: BILL.value_kwh, start_candidates: [start], end_candidates: [END_CANDIDATE],
      });
    }
    if (path === '/api/meters/m1/bills/b1/comparison') {
      if (options.comparisonOutcome === 'no_comparison') {
        return json(route, {
          ...COMPARISON_RESULT, status: 'no_comparison', reason: 'decreasing_reading',
          end_reading: { ...END_CANDIDATE, value_kwh: '800' },
          recorded_kwh: null, difference_kwh: null, outcome: null,
        });
      }
      if (options.comparisonOutcome === 'billed_higher') {
        return json(route, { ...COMPARISON_RESULT, recorded_kwh: '80', difference_kwh: '20.5', outcome: 'billed_higher' });
      }
      if (options.comparisonOutcome === 'equal') {
        return json(route, { ...COMPARISON_RESULT, recorded_kwh: '100.5', difference_kwh: '0', outcome: 'equal' });
      }
      return json(route, options.comparisonMode === 'approximate'
        ? { ...COMPARISON_RESULT, exact: false, start_reading: { ...START_CANDIDATE, local_date: '2026-09-30' } }
        : COMPARISON_RESULT);
    }
    if (path === '/api/meters/m1/consumption-evolution') {
      return options.evolutionError
        ? json(route, { detail: 'Servicio no disponible.' }, 500)
        : json(route, { meter_id: 'm1', intervals: [INTERVAL] });
    }
    if (path === '/api/meters/m2/consumption-evolution') return json(route, { meter_id: 'm2', intervals: [] });
    if (path === '/api/meters/m1/consumption-estimate') {
      if (options.estimateMode === 'error') return json(route, { detail: 'Servicio no disponible.' }, 500);
      if (options.estimateMode === 'unavailable') {
        return json(route, { meter_id: 'm1', status: 'base_unavailable', reason: 'insufficient_readings' });
      }
      return json(route, options.estimateMode === 'sub-day'
        ? { ...ESTIMATE, sub_day: true, base_start_at: '2026-10-31T15:00:00Z', base_end_at: '2026-10-31T20:00:00Z' }
        : ESTIMATE);
    }
    if (path === '/api/meters/m2/consumption-estimate') {
      return json(route, { meter_id: 'm2', status: 'base_unavailable', reason: 'insufficient_readings' });
    }
    return json(route, { detail: 'not mocked' }, 404);
  });
  return requests;
}

async function openAccount(page: Page): Promise<void> {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Domicilios', exact: true })).toBeVisible();
}

function sectionIds(page: Page) {
  return page.locator('main section[id]').evaluateAll(nodes => nodes.map(node => node.id));
}

const SECTION_ORDER = ['domicilios', 'medidores', 'cortes', 'lecturas', 'facturas', 'consumo'];

test('Mi cuenta exposes one h1, the six sections and the in-page index', async ({ page }) => {
  await mockAccount(page);
  await openAccount(page);

  await expect(page.locator('h1')).toHaveCount(1);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Mi cuenta');
  for (const name of ['Domicilios', 'Medidores', 'Cortes e interrupciones', 'Lecturas', 'Facturas', 'Consumo y estimación']) {
    await expect(page.getByRole('heading', { name, exact: true })).toBeVisible();
  }
  expect(await sectionIds(page)).toEqual(SECTION_ORDER);

  const index = page.getByRole('navigation', { name: 'Índice de Mi cuenta' });
  await expect(index).toBeVisible();
  const links = index.getByRole('link');
  await expect(links).toHaveCount(6);
  expect(await links.evaluateAll(nodes => nodes.map(node => node.getAttribute('href'))))
    .toEqual(SECTION_ORDER.map(id => `#${id}`));
  await expect(page.getByRole('navigation', { name: 'Secciones' })).toHaveCount(1);
  await expect(page.getByRole('tab')).toHaveCount(0);
  await expect(page.locator('details')).toHaveCount(0);
});

test('the context panel owns the only domicile and meter selectors', async ({ page }) => {
  const requests = await mockAccount(page);
  await openAccount(page);

  await expect(page.getByRole('heading', { name: 'Contexto de trabajo', exact: true })).toBeVisible();
  await expect(page.locator('#selected-domicile')).toHaveCount(1);
  await expect(page.locator('#reading-meter')).toHaveCount(1);
  await expect(page.getByLabel('Domicilio seleccionado')).toHaveValue('d');
  await expect(page.getByText(`Domicilio activo: ${DOMICILE.display_address}`, { exact: true })).toBeVisible();
  await expect(page.getByText('Sin medidor seleccionado.', { exact: true })).toBeVisible();

  const selector = page.getByLabel('Medidor para consultar lecturas');
  await expect(selector.locator('option')).toHaveCount(3);
  await selector.selectOption('m1');
  await expect(page.getByText('Medidor activo: 001-A — Casa', { exact: true })).toBeVisible();
  await expect(page.locator('#selected-domicile')).toHaveCount(1);
  await expect(page.locator('#reading-meter')).toHaveCount(1);
  expect(requests.filter(path => path === '/api/domiciles/d/management')).toHaveLength(1);
  expect(requests.filter(path => path === '/api/domiciles/d/meters')).toHaveLength(1);
  await selector.selectOption('m2');
  expect(requests.filter(path => path === '/api/domiciles/d/management')).toHaveLength(1);
  expect(requests.filter(path => path === '/api/domiciles/d/meters')).toHaveLength(1);
});

test('no domicile keeps only the registration path', async ({ page }) => {
  await mockAccount(page, { domiciles: 'none' });
  await openAccount(page);

  await expect(page.getByText('Registrá un domicilio para empezar. No se necesita medidor.')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Domicilios', exact: true })).toBeVisible();
  await expect(page.getByText('Todavía no hay un domicilio registrado. Usá la sección Domicilios para crear el primero.')).toBeVisible();
  await expect(page.locator('#selected-domicile')).toHaveCount(0);
  await expect(page.locator('#reading-meter')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Medidores', exact: true })).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Cortes e interrupciones', exact: true })).toHaveCount(0);
  await expect(page.getByRole('form', { name: 'Registrar corte' })).toHaveCount(0);
  await expect(page.getByRole('navigation', { name: 'Índice de Mi cuenta' }).getByRole('link')).toHaveCount(1);
  await expect(page.locator('tbody tr')).toHaveCount(0);
});

test('a domicile without meters keeps the diary usable', async ({ page }) => {
  const requests = await mockAccount(page, { meters: 'none' });
  await openAccount(page);

  await expect(page.getByText('No hay medidores registrados. El domicilio puede usarse sin medidor.')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Cortes e interrupciones', exact: true })).toBeVisible();
  await expect(page.getByRole('form', { name: 'Registrar corte' })).toBeVisible();
  await expect(page.getByRole('form', { name: 'Consultar período' })).toBeVisible();
  await expect(page.locator('#reading-meter')).toHaveCount(0);
  await expect(page.getByText('Los medidores se administran en la sección Medidores.')).toBeVisible();
  await expect(page.getByText(EMPTY_METER_GUIDANCE)).toHaveCount(3);
  await expect(page.locator('tbody tr')).toHaveCount(0);
  expect(requests.some(path => path.startsWith('/api/meters/'))).toBe(false);
});

test('a failed meter load is not reported as a domicile without meters', async ({ page }) => {
  await mockAccount(page, { metersError: true });
  await openAccount(page);

  await expect(page.getByText('Servicio no disponible.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Reintentar administración' })).toBeVisible();
  await expect(page.getByText('No hay medidores registrados. El domicilio puede usarse sin medidor.')).toHaveCount(0);
  await expect(page.getByText('No se pudo cargar la lista de medidores. Reintentá en la sección Medidores.')).toHaveCount(4);
  await expect(page.getByRole('form', { name: 'Registrar corte' })).toBeVisible();
});

test('the selected meter drives the meter sections and isolates the previous one', async ({ page }) => {
  await mockAccount(page);
  await openAccount(page);
  const selector = page.getByLabel('Medidor para consultar lecturas');
  await selector.selectOption('m1');

  await expect(page.getByText(/1200 kWh/)).toBeVisible();
  await expect(page.getByText(/2026-10-01 — 2026-10-31/)).toBeVisible();
  await expect(page.getByText(/300 kWh/).first()).toBeVisible();
  // The index link and the section heading must not make the CU08 locator ambiguous.
  await expect(page.getByRole('heading', { name: 'Consumo y estimación', exact: true })).toHaveCount(1);

  await selector.selectOption('m2');
  await expect(page.getByText('No hay lecturas registradas.')).toBeVisible();
  await expect(page.getByText('No hay facturas registradas.')).toBeVisible();
  await expect(page.getByText('No hay suficientes lecturas para mostrar la evolución.')).toBeVisible();
  await expect(page.getByText(/1200 kWh/)).toHaveCount(0);
  await expect(page.getByText(/2026-10-01 — 2026-10-31/)).toHaveCount(0);
  await expect(page.getByRole('region', { name: 'Comparación con la factura' })).toHaveCount(0);
});

test('switching meters A then B then A shows only the active meter data', async ({ page }) => {
  await mockAccount(page, { secondMeterReading: true });
  await openAccount(page);
  const selector = page.getByLabel('Medidor para consultar lecturas');

  await selector.selectOption('m1');
  await expect(page.getByText(/1200 kWh/)).toBeVisible();
  await selector.selectOption('m2');
  await expect(page.getByText(/77 kWh/)).toBeVisible();
  await expect(page.getByText(/1200 kWh/)).toHaveCount(0);
  await selector.selectOption('m1');
  await expect(page.getByText(/1200 kWh/)).toBeVisible();
  await expect(page.getByText(/77 kWh/)).toHaveCount(0);
});

test('switching meters removes the previous photograph', async ({ page }) => {
  await mockAccount(page);
  await openAccount(page);
  const selector = page.getByLabel('Medidor para consultar lecturas');

  await selector.selectOption('m1');
  await expect(page.getByText(/1200 kWh/)).toBeVisible();
  await page.getByRole('button', { name: 'Ver foto' }).click();
  await expect(page.getByRole('img', { name: 'Foto de la lectura seleccionada' })).toBeVisible();

  await selector.selectOption('m2');
  await expect(page.getByRole('img', { name: 'Foto de la lectura seleccionada' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Ver foto' })).toHaveCount(0);
});

test('the reorganized sections do not nest cards', async ({ page }) => {
  await mockAccount(page);
  await openAccount(page);
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
  await expect(page.getByText(/1200 kWh/)).toBeVisible();

  for (const id of ['domicilios', 'medidores', 'lecturas', 'facturas', 'consumo', 'cortes']) {
    await expect(page.locator(`#${id} [data-slot="card"] [data-slot="card"]`)).toHaveCount(0);
  }
});

test('CU05 and CU06 expose distinct, readable form and history groups without extra cards', async ({ page }) => {
  const requests = await mockAccount(page);
  await openAccount(page);
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');

  const readings = page.locator('#lecturas');
  await expect(readings.getByRole('heading', { name: 'Registrar lectura', exact: true })).toBeVisible();
  await expect(readings.getByRole('heading', { name: 'Historial de lecturas', exact: true })).toBeVisible();
  await expect(readings.getByLabel('Lectura acumulada en kWh')).toBeVisible();
  await expect(readings.getByLabel(/Fotografía/)).toBeVisible();
  await expect(readings.locator('[data-slot="card"] [data-slot="card"]')).toHaveCount(0);

  const bills = page.locator('#facturas');
  await expect(bills.getByRole('heading', { name: 'Registrar factura', exact: true })).toBeVisible();
  await expect(bills.getByRole('heading', { name: 'Facturas registradas', exact: true })).toBeVisible();
  await expect(bills.getByText('Registrar factura', { exact: true })).toBeVisible();
  await expect(bills.getByLabel('Inicio del período')).toBeVisible();
  await expect(bills.getByLabel('Archivo obligatorio')).toBeVisible();
  await expect(bills.locator('[data-slot="card"] [data-slot="card"]')).toHaveCount(0);
  expect(requests.filter(path => path === '/api/meters/m1/readings')).toHaveLength(1);
  expect(requests.filter(path => path === '/api/meters/m1/bills')).toHaveLength(1);
});

test('CU07 identifies the selected bill and shows existing values, difference and units', async ({ page }) => {
  await mockAccount(page);
  await openAccount(page);
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
  await page.getByRole('button', { name: 'Comparar', exact: true }).click();

  const comparison = page.getByRole('region', { name: 'Comparación con la factura' });
  await expect(comparison.getByText('Factura seleccionada')).toBeVisible();
  await expect(comparison.getByText('2026-10-01 — 2026-10-31')).toBeVisible();
  await expect(comparison.getByText('100.5 kWh', { exact: true })).toBeVisible();
  await expect(comparison.getByText('300 kWh')).toBeVisible();
  await expect(comparison.getByText('199.5 kWh')).toBeVisible();
  await expect(comparison.getByText('El consumo registrado es mayor que el facturado.')).toBeVisible();
  await expect(comparison.getByText(/porcentaje/i)).toHaveCount(0);
});

test('CU07 presents the decreasing-reading state and every comparison outcome', async ({ page }) => {
  const scenarios = [
    {
      mode: 'no_comparison' as const,
      expected: 'No se calculó la comparación porque la lectura final es menor que la lectura inicial.',
    },
    {
      mode: 'billed_higher' as const,
      expected: 'El consumo facturado es mayor que el registrado.',
    },
    {
      mode: 'equal' as const,
      expected: 'No hay diferencia entre el consumo registrado y el facturado.',
    },
  ];

  for (const scenario of scenarios) {
    await page.unroute('**/api/**');
    await mockAccount(page, { comparisonOutcome: scenario.mode });
    await openAccount(page);
    await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
    await page.getByRole('button', { name: 'Comparar', exact: true }).click();

    const comparison = page.getByRole('region', { name: 'Comparación con la factura' });
    await expect(comparison.getByRole('heading', { name: 'Resultado de la comparación' })).toBeVisible();
    await expect(comparison.getByText(scenario.expected, { exact: true })).toBeVisible();
    if (scenario.mode === 'no_comparison') {
      await expect(comparison.getByText('Diferencia:', { exact: false })).toHaveCount(0);
    }
  }
});

test('CU07 presents insufficient candidates, approximate warnings and comparison errors', async ({ page }) => {
  await mockAccount(page, { comparisonMode: 'none' });
  await openAccount(page);
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
  await page.getByRole('button', { name: 'Comparar', exact: true }).click();
  const comparison = page.getByRole('region', { name: 'Comparación con la factura' });
  await expect(comparison.getByText(/No hay lecturas compatibles/)).toBeVisible();

  await mockAccount(page, { comparisonMode: 'approximate' });
  await openAccount(page);
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
  await page.getByRole('button', { name: 'Comparar', exact: true }).click();
  const approximate = page.getByRole('region', { name: 'Comparación con la factura' });
  await expect(approximate.getByText(/no coinciden exactamente/)).toBeVisible();
  await approximate.getByLabel('Confirmo que quiero comparar con estas fechas aproximadas.').check();
  await approximate.getByRole('button', { name: 'Calcular comparación' }).click();
  await expect(approximate.getByText(/Comparación aproximada/)).toBeVisible();

  await mockAccount(page, { comparisonMode: 'error' });
  await openAccount(page);
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
  await page.getByRole('button', { name: 'Comparar', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Comparación con la factura' }).getByRole('alert')).toBeVisible();
});

test('changing meter while a comparison is open clears the previous comparison', async ({ page }) => {
  await mockAccount(page);
  await openAccount(page);
  const selector = page.getByLabel('Medidor para consultar lecturas');
  await selector.selectOption('m1');
  await page.getByRole('button', { name: 'Comparar', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Comparación con la factura' }).getByText('300 kWh')).toBeVisible();
  await selector.selectOption('m2');
  await expect(page.getByRole('region', { name: 'Comparación con la factura' })).toHaveCount(0);
});

test('CU08 keeps the selected date range, real intervals and daily averages distinct', async ({ page }) => {
  const evolutionRequests: string[] = [];
  page.on('request', request => {
    const url = new URL(request.url());
    if (url.pathname === '/api/meters/m1/consumption-evolution') evolutionRequests.push(url.href);
  });
  await mockAccount(page);
  await openAccount(page);
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');

  const consumption = page.locator('#consumo');
  await expect(consumption.getByRole('heading', { name: 'Consumo real (kWh)', exact: true })).toBeVisible();
  await expect(consumption.getByRole('heading', { name: 'Promedio diario (kWh/día)', exact: true })).toBeVisible();
  await expect(consumption.getByRole('cell', { name: '300 kWh', exact: true })).toBeVisible();
  await expect(consumption.getByRole('cell', { name: '10.00 kWh/día', exact: true })).toBeVisible();
  await consumption.getByLabel('Desde').fill('2026-10-01');
  await consumption.getByLabel('Hasta').fill('2026-10-31');
  await expect.poll(() => evolutionRequests.some(value => value.includes('from=2026-10-01') && value.includes('to=2026-10-31'))).toBe(true);
  await expect(consumption.locator('[data-slot="card"] [data-slot="card"]')).toHaveCount(0);
});

test('CU08 shows an available estimate, its period, representative warning and insufficient state', async ({ page }) => {
  await mockAccount(page, { estimateMode: 'sub-day' });
  await openAccount(page);
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
  const consumption = page.locator('#consumo');
  await consumption.getByRole('button', { name: 'Estimar', exact: true }).click();
  const result = consumption.getByRole('region', { name: 'Resultado de la estimación' });
  await expect(result.getByText('300.00 kWh')).toBeVisible();
  await expect(result.getByText(/Intervalo considerado/)).toBeVisible();
  await expect(result.getByText(/Buenos Aires/)).toBeVisible();
  await expect(result.getByText(/poco representativo/)).toBeVisible();
  await expect(result.getByText('Estimación orientativa, no facturada.')).toBeVisible();

  await mockAccount(page, { estimateMode: 'unavailable' });
  await openAccount(page);
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
  await page.locator('#consumo').getByRole('button', { name: 'Estimar', exact: true }).click();
  await expect(page.locator('#consumo').getByText('No hay suficientes lecturas para estimar.')).toBeVisible();
});

test('CU08 clears a visible estimate after switching meters and shows service errors', async ({ page }) => {
  await mockAccount(page);
  await openAccount(page);
  const selector = page.getByLabel('Medidor para consultar lecturas');
  await selector.selectOption('m1');
  const consumption = page.locator('#consumo');
  await consumption.getByRole('button', { name: 'Estimar', exact: true }).click();
  await expect(consumption.getByRole('region', { name: 'Resultado de la estimación' })).toBeVisible();
  await selector.selectOption('m2');
  await expect(page.locator('#consumo').getByRole('region', { name: 'Resultado de la estimación' })).toHaveCount(0);

  await mockAccount(page, { evolutionError: true, estimateMode: 'error' });
  await openAccount(page);
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
  const failedConsumption = page.locator('#consumo');
  await expect(failedConsumption.getByRole('alert')).toBeVisible();
  await failedConsumption.getByRole('button', { name: 'Estimar', exact: true }).click();
  await expect(failedConsumption.getByRole('alert')).toBeVisible();
});

test('account layout keeps one chat mount, no health request and no overflow', async ({ page }) => {
  const requests = await mockAccount(page);
  await openAccount(page);
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
  await expect(page.getByText(/1200 kWh/)).toBeVisible();
  await page.getByRole('button', { name: 'Comparar', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Comparación con la factura' })).toBeVisible();
  await page.locator('#consumo').getByRole('button', { name: 'Estimar', exact: true }).click();
  await expect(page.locator('#consumo').getByRole('region', { name: 'Resultado de la estimación' })).toBeVisible();

  await expect(page.locator('[data-chat-mount="cu03"]')).toHaveCount(1);
  expect(requests.filter(path => path === '/api/health')).toEqual([]);

  for (const width of [390, 820, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, `no horizontal overflow at ${width}px`).toBe(0);
  }

  const colors = await page.evaluate(() => ({
    background: getComputedStyle(document.body).backgroundColor,
    foreground: getComputedStyle(document.body).color,
  }));
  expect(colors).toEqual({ background: 'rgb(248, 250, 252)', foreground: 'rgb(15, 23, 42)' });
});

test('in-page anchors reach their sections', async ({ page }) => {
  await mockAccount(page);
  await openAccount(page);

  const links = page.getByRole('navigation', { name: 'Índice de Mi cuenta' }).getByRole('link');
  await links.filter({ hasText: 'Consumo y estimación' }).focus();
  await expect(links.filter({ hasText: 'Consumo y estimación' })).toBeFocused();
  await links.filter({ hasText: 'Consumo y estimación' }).press('Enter');
  await expect(page).toHaveURL(/#consumo$/);
  await expect(page.locator('#consumo')).toBeInViewport();
  await expect(page.getByRole('heading', { name: 'Consumo y estimación', exact: true })).toBeInViewport();
});

test('the address draft and the meter draft survive an address conflict and its recovery', async ({ page }) => {
  await mockAccount(page, { addressConflict: true });
  await openAccount(page);

  const meter = page.getByRole('form', { name: 'Registrar medidor' });
  await meter.getByLabel('Número de medidor').fill('DRAFT-1');
  await meter.getByLabel('Alias (opcional)').fill('Alias sin guardar');

  await page.getByRole('button', { name: 'Corregir domicilio', exact: true }).click();
  const address = page.getByRole('form', { name: 'Corregir domicilio' });
  await address.getByLabel('Dirección').fill('Domicilio sintético 100 bis');
  await address.getByRole('button', { name: 'Guardar domicilio' }).click();

  await expect(page.getByRole('alert')).toContainText('La versión cambió. Descartá el borrador y recargá antes de volver a editar.');
  await expect(meter.getByLabel('Número de medidor')).toHaveValue('DRAFT-1');
  await expect(meter.getByLabel('Alias (opcional)')).toHaveValue('Alias sin guardar');
  await expect(address.getByLabel('Dirección')).toHaveValue('Domicilio sintético 100 bis');

  await page.getByRole('button', { name: 'Descartar borrador y recargar administración' }).click();
  await expect(meter.getByLabel('Número de medidor')).toHaveValue('DRAFT-1');
  await expect(meter.getByLabel('Alias (opcional)')).toHaveValue('Alias sin guardar');
  await page.getByRole('button', { name: 'Corregir domicilio', exact: true }).click();
  await expect(address.getByLabel('Dirección')).toHaveValue(DOMICILE.display_address);
});

test('the address draft survives a meter conflict and its recovery', async ({ page }) => {
  await mockAccount(page, { meterConflict: true });
  await openAccount(page);

  await page.getByRole('button', { name: 'Corregir domicilio', exact: true }).click();
  const address = page.getByRole('form', { name: 'Corregir domicilio' });
  await address.getByLabel('Dirección').fill('Domicilio sintético 100 bis');

  const meters = page.getByRole('list', { name: 'Medidores registrados' });
  await meters.getByRole('button', { name: 'Corregir medidor' }).first().click();
  const editor = page.getByRole('form', { name: 'Corregir medidor' });
  await editor.getByLabel('Alias (opcional)').fill('Casa corregida');
  await editor.getByRole('button', { name: 'Guardar medidor' }).click();

  await expect(page.getByRole('alert')).toContainText('La versión cambió. Descartá el borrador y recargá antes de volver a editar.');
  await expect(address.getByLabel('Dirección')).toHaveValue('Domicilio sintético 100 bis');

  await page.getByRole('button', { name: 'Descartar borrador y recargar administración' }).click();
  await expect(page.getByRole('form', { name: 'Registrar medidor' }).getByLabel('Número de medidor')).toHaveValue('');
  await expect(address.getByLabel('Dirección')).toHaveValue('Domicilio sintético 100 bis');
});

test('switching domiciles resets the meter selection and the meter-scoped data', async ({ page }) => {
  const first = { id: 'd1', display_address: 'Domicilio sintético uno' };
  const second = { id: 'd2', display_address: 'Domicilio sintético dos' };
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    const responses: Record<string, unknown> = {
      '/api/session': { account: { id: 'synthetic', username: 'synthetic' }, csrf_token: 'synthetic' },
      '/api/domiciles': [first, second],
      '/api/domiciles/d1/management': { ...first, version: 1 },
      '/api/domiciles/d2/management': { ...second, version: 1 },
      '/api/domiciles/d1/meters': [{ id: 'm1', domicile_id: 'd1', meter_number: '001-A', alias: null, version: 1 }],
      '/api/domiciles/d2/meters': [{ id: 'm2', domicile_id: 'd2', meter_number: '002-B', alias: null, version: 1 }],
      '/api/domiciles/d1/interruptions': [],
      '/api/domiciles/d2/interruptions': [],
      '/api/meters/m1/readings': [{ ...READING, id: 'r1', meter_id: 'm1', value_kwh: '1200' }],
      '/api/meters/m2/readings': [{ ...READING, id: 'r2', meter_id: 'm2', value_kwh: '77' }],
      '/api/meters/m1/bills': [],
      '/api/meters/m2/bills': [],
      '/api/meters/m1/consumption-evolution': { meter_id: 'm1', intervals: [INTERVAL] },
      '/api/meters/m2/consumption-evolution': { meter_id: 'm2', intervals: [] },
    };
    if (!(path in responses)) return json(route, { detail: 'not mocked' }, 404);
    return json(route, responses[path]);
  });

  await page.goto('/');
  await expect(page.getByLabel('Domicilio seleccionado')).toHaveValue('d1');
  const newDomicile = page.getByLabel('Domicilio nuevo');
  await newDomicile.fill('Borrador sintético pendiente');
  await page.getByLabel('Medidor para consultar lecturas').selectOption('m1');
  await expect(page.getByText(/1200 kWh/)).toBeVisible();

  await page.getByLabel('Domicilio seleccionado').selectOption('d2');
  await expect(page.getByLabel('Domicilio seleccionado')).toHaveValue('d2');
  await expect(page.getByLabel('Medidor para consultar lecturas').locator('option')).toHaveCount(2);
  await expect(page.getByText(/1200 kWh/)).toHaveCount(0);
  await expect(page.getByText('Sin medidor seleccionado.', { exact: true })).toBeVisible();
  await expect(page.getByRole('list').getByText('002-B', { exact: true })).toBeVisible();
  await expect(newDomicile).toHaveValue('Borrador sintético pendiente');

  await page.getByLabel('Medidor para consultar lecturas').selectOption('m2');
  await expect(page.getByText(/77 kWh/)).toBeVisible();
  await expect(page.getByText(/1200 kWh/)).toHaveCount(0);
});

test('CU09 presents registration, history, correction and closure within one main card', async ({ page }) => {
  await mockAccount(page, { diary: 'records' });
  await openAccount(page);

  const diary = page.locator('#cortes');
  await expect(diary.getByRole('heading', { name: 'Registrar interrupción', exact: true })).toBeVisible();
  await expect(diary.getByRole('heading', { name: 'Historial de interrupciones', exact: true })).toBeVisible();
  await expect(diary.getByRole('heading', { name: 'Resumen por período', exact: true })).toBeVisible();
  await expect(diary.locator('[data-slot="card"]')).toHaveCount(1);
  await expect(diary.locator('[data-slot="card"] [data-slot="card"]')).toHaveCount(0);

  const history = diary.getByRole('region', { name: 'Cortes registrados' });
  await expect(history.getByRole('columnheader')).toHaveText([
    'Inicio', 'Fin', 'Estado', 'Observaciones', 'Reclamo', 'Acciones',
  ]);
  await expect(history.getByRole('cell', { name: 'Observación sintética' })).toBeVisible();
  await expect(history.getByRole('cell', { name: 'TEST-001' })).toBeVisible();
  await expect(history.getByRole('cell', { name: 'En curso' })).toHaveCount(2);
  await expect(history.getByRole('button', { name: 'Corregir', exact: true })).toHaveCount(2);
  await expect(history.getByRole('button', { name: 'Cerrar corte', exact: true })).toHaveCount(1);

  for (const width of [390, 820, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth === document.documentElement.clientWidth))
      .toBe(true);
    await expect(history).toHaveAttribute('tabindex', '0');
    const hasInternalOverflow = await history.evaluate(element => element.scrollWidth > element.clientWidth);
    expect(hasInternalOverflow).toBe(width < 1440);
  }
});

test('CU09 registers a cut with the existing fields and refreshes the history', async ({ page }) => {
  const requests = await mockAccount(page);
  await openAccount(page);
  const form = page.getByRole('form', { name: 'Registrar corte', exact: true });
  await form.getByLabel('Inicio', { exact: true }).fill('2026-11-01T09:00');
  await form.getByLabel('Fin (opcional si está en curso)', { exact: true }).fill('2026-11-01T10:00');
  await form.getByRole('textbox', { name: 'Observaciones', exact: true }).fill('Interrupción sintética');
  await form.getByLabel('Número de reclamo', { exact: true }).fill('TEST-REG-01');
  await form.getByRole('button', { name: 'Guardar corte', exact: true }).click();

  await expect(page.getByText('Operación guardada.', { exact: true })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'TEST-REG-01' })).toBeVisible();
  expect(requests.filter(path => path === '/api/domiciles/d/interruptions')).toHaveLength(3);
  await expect(form.getByLabel('Inicio', { exact: true })).toHaveValue('');
});

test('CU09 corrects closed cuts and closes ongoing cuts with versioned actions preserved', async ({ page }) => {
  await mockAccount(page, { diary: 'records' });
  await openAccount(page);
  const history = page.getByRole('region', { name: 'Cortes registrados' });
  const closedRow = history.getByRole('row').filter({ hasText: 'TEST-001' });
  await closedRow.getByRole('button', { name: 'Corregir', exact: true }).click();
  const editor = page.getByRole('form', { name: 'Corregir corte', exact: true });
  await expect(editor.getByLabel('Fin (opcional si está en curso)', { exact: true })).toHaveValue('2026-11-01T11:00');
  await editor.getByRole('textbox', { name: 'Observaciones', exact: true }).fill('Nota corregida');
  await editor.getByRole('button', { name: 'Guardar corrección', exact: true }).click();
  await expect(page.getByText('Operación guardada.', { exact: true })).toBeVisible();
  await expect(history.getByRole('cell', { name: 'Nota corregida' })).toBeVisible();

  await history.getByRole('button', { name: 'Cerrar corte', exact: true }).click();
  const close = page.getByRole('form', { name: 'Cerrar corte', exact: true });
  await close.getByLabel('Fecha de cierre', { exact: true }).fill('2026-11-01T13:00');
  await close.getByRole('button', { name: 'Confirmar cierre', exact: true }).click();
  await expect(page.getByText('Operación guardada.', { exact: true })).toBeVisible();
  await expect(history.getByRole('button', { name: 'Cerrar corte', exact: true })).toHaveCount(0);
  await expect(history.getByRole('cell', { name: 'Cerrado' })).toHaveCount(2);
});

test('CU09 preserves an edit draft through 409 and reloads the current server version on explicit discard', async ({ page }) => {
  await mockAccount(page, { diary: 'records', diaryConflict: true });
  await openAccount(page);
  const history = page.getByRole('region', { name: 'Cortes registrados' });
  await history.getByRole('button', { name: 'Corregir', exact: true }).first().click();
  const editor = page.getByRole('form', { name: 'Corregir corte', exact: true });
  await editor.getByRole('textbox', { name: 'Observaciones', exact: true }).fill('Borrador no guardado');
  await editor.getByRole('button', { name: 'Guardar corrección', exact: true }).click();

  await expect(page.getByRole('alert')).toContainText('Descartar borrador y recargar');
  await expect(editor.getByRole('textbox', { name: 'Observaciones', exact: true })).toHaveValue('Borrador no guardado');
  await page.getByRole('button', { name: 'Descartar borrador y recargar', exact: true }).click();
  await expect(page.getByRole('form', { name: 'Corregir corte', exact: true })
    .getByRole('textbox', { name: 'Observaciones', exact: true })).toHaveValue('Versión actual del servidor');
  await expect(page.getByRole('button', { name: 'Descartar borrador y recargar', exact: true })).toHaveCount(0);
});

test('CU09 keeps PDF download available with the accepted overlap-safe summary', async ({ page }) => {
  await mockAccount(page, { diary: 'records' });
  await openAccount(page);
  const diary = page.locator('#cortes');
  await expect(diary.getByRole('button', { name: 'Descargar PDF', exact: true })).toHaveCount(0);
  await diary.getByLabel('Desde', { exact: true }).fill('2026-11-01T00:00');
  await diary.getByLabel('Hasta', { exact: true }).fill('2026-11-02T00:00');
  await diary.getByRole('button', { name: 'Consultar resumen', exact: true }).click();
  const result = diary.getByRole('region', { name: 'Resultado del resumen' });
  await expect(result.getByRole('heading', { name: 'Total sin servicio: 3 h 0 min', exact: true })).toBeVisible();
  await expect(result.getByText('2 registros con duración dentro del período. El tiempo superpuesto se cuenta una sola vez.')).toBeVisible();

  const downloadPromise = page.waitForEvent('download');
  await result.getByRole('button', { name: 'Descargar PDF', exact: true }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('interruption-diary.pdf');
});

test('CU09 keeps summary and PDF generation errors visible near the period action', async ({ page }) => {
  await mockAccount(page, { summaryError: true });
  await openAccount(page);
  await page.getByRole('button', { name: 'Consultar resumen', exact: true }).click();
  await expect(page.locator('#cortes').getByRole('alert')).toBeVisible();

  await mockAccount(page, { diary: 'records', pdfError: true });
  await openAccount(page);
  await page.getByRole('button', { name: 'Consultar resumen', exact: true }).click();
  await page.getByRole('button', { name: 'Descargar PDF', exact: true }).click();
  await expect(page.locator('#cortes').getByRole('alert')).toBeVisible();
});

test('CU09 diary follows the selected domicile without depending on meter selection', async ({ page }) => {
  await mockAccount(page, { domiciles: 'multiple', diary: 'records' });
  await openAccount(page);
  await expect(page.getByRole('cell', { name: 'TEST-001' })).toBeVisible();
  await page.getByLabel('Domicilio seleccionado', { exact: true }).selectOption('d2');
  await expect(page.getByLabel('Domicilio seleccionado', { exact: true })).toHaveValue('d2');
  await expect(page.getByText('No hay cortes registrados.', { exact: true })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'TEST-001' })).toHaveCount(0);
  await expect(page.getByRole('form', { name: 'Registrar corte', exact: true })).toBeVisible();
  await expect(page.locator('#reading-meter')).toHaveCount(0);
});

test('CU09 clears prior diary data when the authenticated user changes', async ({ page }) => {
  const accountADomicile = { id: 'da', display_address: 'Domicilio sintético de cuenta A' };
  const accountBDomicile = { id: 'db', display_address: 'Domicilio sintético de cuenta B' };
  const accountACut: MockCut = {
    ...CLOSED_CUT, id: 'account-a-cut', domicile_id: accountADomicile.id,
    observations: 'Dato privado de cuenta A',
  };
  let activeAccount: 'a' | 'b' = 'a';
  await page.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === '/api/session') {
      return json(route, {
        account: { id: activeAccount, username: `synthetic-${activeAccount}` }, csrf_token: 'synthetic',
      });
    }
    if (path === '/api/logout') return route.fulfill({ status: 204 });
    if (path === '/api/login' && request.method() === 'POST') {
      const body: unknown = request.postDataJSON();
      if (typeof body !== 'object' || body === null || !('username' in body) || body.username !== 'synthetic-b') {
        return json(route, { detail: 'Invalid synthetic login.' }, 403);
      }
      activeAccount = 'b';
      return json(route, {
        account: { id: 'b', username: 'synthetic-b' }, csrf_token: 'synthetic-b',
      });
    }
    if (path === '/api/domiciles') return json(route, [activeAccount === 'a' ? accountADomicile : accountBDomicile]);
    if (path === `/api/domiciles/${accountADomicile.id}/management`) {
      return json(route, { ...accountADomicile, version: 1 });
    }
    if (path === `/api/domiciles/${accountBDomicile.id}/management`) {
      return json(route, { ...accountBDomicile, version: 1 });
    }
    if (path.endsWith('/meters')) return json(route, []);
    if (path === `/api/domiciles/${accountADomicile.id}/interruptions`) {
      return json(route, activeAccount === 'a' ? [accountACut] : []);
    }
    if (path === `/api/domiciles/${accountBDomicile.id}/interruptions`) return json(route, []);
    return json(route, { detail: 'not mocked' }, 404);
  });

  await page.goto('/');
  await expect(page.getByRole('cell', { name: 'Dato privado de cuenta A' })).toBeVisible();
  await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click();
  await expect(page.getByRole('form', { name: 'Ingresar', exact: true })).toBeVisible();
  await page.getByLabel('Usuario', { exact: true }).fill('synthetic-b');
  await page.getByLabel('Contraseña', { exact: true }).fill('synthetic-password');
  await page.getByRole('button', { name: 'Ingresar', exact: true }).click();

  await expect(page.getByLabel('Domicilio seleccionado', { exact: true })).toHaveValue('db');
  await expect(page.getByText('Domicilio activo: Domicilio sintético de cuenta B', { exact: true })).toBeVisible();
  await expect(page.getByText('Dato privado de cuenta A', { exact: true })).toHaveCount(0);
  await expect(page.getByRole('form', { name: 'Registrar corte', exact: true })).toBeVisible();
  await expect(page.locator('#reading-meter')).toHaveCount(0);
});
