export interface BillOverlap { id: string; period_start: string; period_end: string; version: number }
export interface BillWarning { overlaps: BillOverlap[]; overlap_token: string }

export interface ComparisonCandidate {
  reading_id: string; recorded_at: string; local_date: string; value_kwh: string; version: number;
}
export interface ComparisonConfirmation {
  period_start: string; period_end: string; start_local_date: string; end_local_date: string;
  start_candidates: ComparisonCandidate[]; end_candidates: ComparisonCandidate[];
}

const DATE = /^\d{4}-\d{2}-\d{2}$/;
const INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;
const DECIMAL = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;

export function isComparisonCandidate(value: unknown): value is ComparisonCandidate {
  if (typeof value !== 'object' || value === null) return false;
  const row = value as Record<string, unknown>;
  return typeof row.reading_id === 'string' && row.reading_id.length > 0 &&
    typeof row.recorded_at === 'string' && INSTANT.test(row.recorded_at) &&
    Number.isFinite(Date.parse(row.recorded_at)) &&
    typeof row.local_date === 'string' && DATE.test(row.local_date) &&
    typeof row.value_kwh === 'string' && DECIMAL.test(row.value_kwh) &&
    typeof row.version === 'number' && Number.isSafeInteger(row.version) && row.version > 0;
}

function candidateList(value: unknown): ComparisonCandidate[] | null {
  return Array.isArray(value) && value.every(isComparisonCandidate) ? value : null;
}

export function comparisonConfirmation(body: unknown): ComparisonConfirmation | null {
  if (typeof body !== 'object' || body === null) return null;
  const row = body as Record<string, unknown>;
  const start = candidateList(row.start_candidates);
  const end = candidateList(row.end_candidates);
  if (start === null || end === null) return null;
  if (typeof row.period_start !== 'string' || !DATE.test(row.period_start)) return null;
  if (typeof row.period_end !== 'string' || !DATE.test(row.period_end)) return null;
  if (typeof row.start_local_date !== 'string' || !DATE.test(row.start_local_date)) return null;
  if (typeof row.end_local_date !== 'string' || !DATE.test(row.end_local_date)) return null;
  return {
    period_start: row.period_start, period_end: row.period_end,
    start_local_date: row.start_local_date, end_local_date: row.end_local_date,
    start_candidates: start, end_candidates: end,
  };
}

export class DiaryError extends Error {
  readonly status: number | null;
  readonly kind: 'http' | 'network' | 'invalid-response' | 'aborted' | 'timeout';
  readonly code: 'DUPLICATE_METER' | 'DUPLICATE_READING' | 'DUPLICATE_BILL' | 'OVERLAP_CONFIRMATION_REQUIRED' | 'IDEMPOTENCY_KEY_REUSED' | 'VERSION_CONFLICT' | 'CONFIRMATION_REQUIRED' | null;
  readonly billWarning: BillWarning | null;
  readonly comparisonWarning: ComparisonConfirmation | null;

  constructor(kind: DiaryError['kind'], message: string, status: number | null = null, code: DiaryError['code'] = null, billWarning: BillWarning | null = null, comparisonWarning: ComparisonConfirmation | null = null) {
    super(message);
    this.name = 'DiaryError';
    this.kind = kind;
    this.status = status;
    this.code = code;
    this.billWarning = billWarning;
    this.comparisonWarning = comparisonWarning;
  }
}

export function errorMessage(error: unknown): string {
  return error instanceof DiaryError ? error.message : 'No se pudo completar la operación. Intentá nuevamente.';
}

export function invalidResponse(): DiaryError {
  return new DiaryError('invalid-response', 'La API devolvió una respuesta con formato inesperado. Intentá actualizar.');
}

export function statusMessage(status: number): string {
  switch (status) {
    case 401: return 'La sesión venció. Ingresá nuevamente.';
    case 403: return 'No se pudo autorizar la solicitud. Cerrá la sesión e ingresá nuevamente.';
    case 404: return 'El recurso no está disponible.';
    case 409: return 'El registro fue modificado.';
    case 422: return 'Revisá los datos ingresados.';
    case 503: return 'El servicio no está disponible temporalmente. Intentá nuevamente.';
    default: return `No se pudo completar la solicitud (HTTP ${status}).`;
  }
}
