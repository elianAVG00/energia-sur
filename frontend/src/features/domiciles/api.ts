import { http } from '../../lib/http.ts';
import type { HttpClient } from '../../lib/http.ts';
import { DiaryError, invalidResponse } from '../../lib/httpError.ts';

export interface ManagedDomicile { id: string; display_address: string; version: number }
export interface Meter { id: string; domicile_id: string; meter_number: string; alias: string | null; version: number }
export interface MeterInput { meter_number: string; alias: string | null }

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function identifier(value: unknown): value is string { return typeof value === 'string' && value.length > 0; }
function version(value: unknown): value is number { return typeof value === 'number' && Number.isSafeInteger(value) && value > 0; }
export function isManagedDomicile(value: unknown): value is ManagedDomicile {
  return record(value) && identifier(value.id) && identifier(value.display_address) && version(value.version);
}
export function isMeter(value: unknown): value is Meter {
  return record(value) && identifier(value.id) && identifier(value.domicile_id) && identifier(value.meter_number) &&
    (value.alias === null || typeof value.alias === 'string') && version(value.version);
}
function isMeters(value: unknown): value is Meter[] { return Array.isArray(value) && value.every(isMeter); }

export class DomicilesClient {
  private readonly transport: HttpClient;
  constructor(transport: HttpClient = http) { this.transport = transport; }

  private async json<T>(path: string, signal: AbortSignal, validate: (value: unknown) => value is T,
    expected: number, request: Parameters<HttpClient['request']>[2] = {}): Promise<T> {
    const response = await this.transport.request(path, signal, request);
    const contentType: unknown = response.headers['content-type'];
    if (signal.aborted) throw new DiaryError('aborted', 'La solicitud fue cancelada.');
    if (response.status !== expected || typeof contentType !== 'string' || !/^application\/json(?:\s*;|$)/i.test(contentType) || !validate(response.data)) throw invalidResponse();
    return response.data;
  }

  async management(id: string, signal: AbortSignal): Promise<ManagedDomicile> {
    const row = await this.json(`/domiciles/${encodeURIComponent(id)}/management`, signal, isManagedDomicile, 200);
    if (row.id !== id) throw invalidResponse();
    return row;
  }
  async correctDomicile(row: ManagedDomicile, display_address: string, signal: AbortSignal): Promise<ManagedDomicile> {
    const result = await this.json(`/domiciles/${encodeURIComponent(row.id)}`, signal, isManagedDomicile, 200,
      { method: 'PATCH', data: { display_address, version: row.version } });
    if (result.id !== row.id || result.version !== row.version + 1) throw invalidResponse();
    return result;
  }
  async meters(id: string, signal: AbortSignal): Promise<Meter[]> {
    const rows = await this.json(`/domiciles/${encodeURIComponent(id)}/meters`, signal, isMeters, 200);
    if (!rows.every(row => row.domicile_id === id)) throw invalidResponse();
    return rows;
  }
  async createMeter(id: string, input: MeterInput, signal: AbortSignal): Promise<Meter> {
    const row = await this.json(`/domiciles/${encodeURIComponent(id)}/meters`, signal, isMeter, 201, { method: 'POST', data: input });
    if (row.domicile_id !== id) throw invalidResponse();
    return row;
  }
  async meter(id: string, meterId: string, signal: AbortSignal): Promise<Meter> {
    const row = await this.json(`/domiciles/${encodeURIComponent(id)}/meters/${encodeURIComponent(meterId)}`, signal, isMeter, 200);
    if (row.domicile_id !== id || row.id !== meterId) throw invalidResponse();
    return row;
  }
  async correctMeter(row: Meter, input: MeterInput, signal: AbortSignal): Promise<Meter> {
    const result = await this.json(`/domiciles/${encodeURIComponent(row.domicile_id)}/meters/${encodeURIComponent(row.id)}`, signal, isMeter, 200,
      { method: 'PATCH', data: { ...input, version: row.version } });
    if (result.domicile_id !== row.domicile_id || result.id !== row.id || result.version !== row.version + 1) throw invalidResponse();
    return result;
  }
}

export const domicilesApi = new DomicilesClient();
