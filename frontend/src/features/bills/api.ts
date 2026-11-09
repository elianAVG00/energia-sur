import { http } from '../../lib/http.ts';
import type { HttpClient } from '../../lib/http.ts';
import { invalidResponse } from '../../lib/httpError.ts';

export interface Bill {
  id: string; meter_id: string; period_start: string; period_end: string;
  value_kwh: string; amount_ars: string | null; file_type: string; version: number;
}
export interface BillInput {
  period_start: string; period_end: string; value_kwh: string; amount_ars: string | null;
  file_base64: string | null; overlap_token: string | null;
}
export interface BillEdit extends BillInput { version: number; file_action: 'keep' | 'replace' }

export function validDecimal(value: string, scale: 2 | 3): boolean {
  return (scale === 3 ? /^[0-9]{1,18}(?:\.[0-9]{1,3})?$/ : /^[0-9]{1,18}(?:\.[0-9]{1,2})?$/).test(value);
}
export function validDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || value.startsWith('0000')) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(date.valueOf()) && date.toISOString().slice(0, 10) === value;
}
function isBill(value: unknown): value is Bill {
  if (typeof value !== 'object' || value === null) return false;
  return 'id' in value && typeof value.id === 'string' && value.id.length > 0 &&
    'meter_id' in value && typeof value.meter_id === 'string' && value.meter_id.length > 0 &&
    'period_start' in value && typeof value.period_start === 'string' && validDate(value.period_start) &&
    'period_end' in value && typeof value.period_end === 'string' && validDate(value.period_end) && value.period_start <= value.period_end &&
    'value_kwh' in value && typeof value.value_kwh === 'string' && validDecimal(value.value_kwh, 3) &&
    'amount_ars' in value && (value.amount_ars === null || (typeof value.amount_ars === 'string' && validDecimal(value.amount_ars, 2))) &&
    'file_type' in value && typeof value.file_type === 'string' && ['application/pdf', 'image/jpeg', 'image/png'].includes(value.file_type) &&
    'version' in value && typeof value.version === 'number' && Number.isSafeInteger(value.version) && value.version > 0;
}
function path(meter: string): string { return `/meters/${encodeURIComponent(meter)}/bills`; }
export class BillsClient {
  private readonly transport: HttpClient;
  constructor(transport: HttpClient = http) { this.transport = transport; }
  private async json<T>(url: string, signal: AbortSignal, guard: (value: unknown) => value is T, status: number, request: Parameters<HttpClient['request']>[2] = {}): Promise<T> {
    const response = await this.transport.request(url, signal, request);
    const type: unknown = response.headers['content-type'];
    if (signal.aborted || response.status !== status || typeof type !== 'string' || !/^application\/json(?:\s*;|$)/i.test(type) || !guard(response.data)) throw invalidResponse();
    return response.data;
  }
  async list(meter: string, signal: AbortSignal): Promise<Bill[]> {
    const rows = await this.json(path(meter), signal, (value): value is Bill[] => Array.isArray(value) && value.every(isBill), 200);
    if (!rows.every(row => row.meter_id === meter)) throw invalidResponse();
    return rows;
  }
  async detail(meter: string, id: string, signal: AbortSignal): Promise<Bill> {
    const row = await this.json(`${path(meter)}/${encodeURIComponent(id)}`, signal, isBill, 200);
    if (row.meter_id !== meter || row.id !== id) throw invalidResponse();
    return row;
  }
  async create(meter: string, input: BillInput, key: string, signal: AbortSignal): Promise<Bill> {
    const row = await this.json(path(meter), signal, isBill, 201, { method: 'POST', data: input, idempotencyKey: key });
    if (row.meter_id !== meter) throw invalidResponse();
    return row;
  }
  async edit(meter: string, id: string, input: BillEdit, signal: AbortSignal): Promise<Bill> {
    const row = await this.json(`${path(meter)}/${encodeURIComponent(id)}`, signal, isBill, 200, { method: 'PATCH', data: input });
    if (row.meter_id !== meter || row.id !== id || row.version !== input.version + 1) throw invalidResponse();
    return row;
  }
  async file(meter: string, id: string, signal: AbortSignal): Promise<Blob> {
    const response = await this.transport.request(`${path(meter)}/${encodeURIComponent(id)}/file`, signal, { responseType: 'blob' });
    const type: unknown = response.headers['content-type'];
    if (signal.aborted || response.status !== 200 || !(response.data instanceof Blob) || !response.data.size || typeof type !== 'string' || !/^(application\/pdf|image\/(?:jpeg|png))$/i.test(type)) throw invalidResponse();
    return response.data;
  }
}
export const billsApi = new BillsClient();
