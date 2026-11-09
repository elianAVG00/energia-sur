import { http } from '../../lib/http.ts';
import type { HttpClient } from '../../lib/http.ts';
import { invalidResponse } from '../../lib/httpError.ts';
import { canonicalReading } from './value.ts';

export interface Reading {
  id: string;
  meter_id: string;
  recorded_at: string;
  value_kwh: string;
  has_photo: boolean;
  version: number;
}
export interface ReadingInput {
  recorded_at: string;
  value_kwh: string;
  confirmed: true;
  photo_base64: string | null;
}
export type PhotoAction = 'keep' | 'remove' | 'replace';
export interface ReadingEdit extends ReadingInput {
  version: number;
  photo_action: PhotoAction;
}
export interface Crop { x: number; y: number; width: number; height: number }
export const OCR_FALLBACK = 'No pudimos identificar con seguridad la lectura del medidor. Intentá subir una fotografía más clara o ingresá manualmente el valor en kWh';
export type OcrResult =
  | { status: 'suggested'; value_kwh: string }
  | { status: 'abstained'; value_kwh: null; message: string };

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function isReading(value: unknown): value is Reading {
  return record(value) && typeof value.id === 'string' && value.id.length > 0 &&
    typeof value.meter_id === 'string' && value.meter_id.length > 0 &&
    typeof value.recorded_at === 'string' &&
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(value.recorded_at) &&
    Number.isFinite(Date.parse(value.recorded_at)) &&
    typeof value.value_kwh === 'string' && canonicalReading(value.value_kwh) === value.value_kwh &&
    typeof value.has_photo === 'boolean' && typeof value.version === 'number' &&
    Number.isSafeInteger(value.version) && value.version > 0;
}
function isOcr(value: unknown): value is OcrResult {
  if (!record(value)) return false;
  if (value.status === 'suggested') {
    return typeof value.value_kwh === 'string' && canonicalReading(value.value_kwh) === value.value_kwh;
  }
  return value.status === 'abstained' && value.value_kwh === null && value.message === OCR_FALLBACK;
}
function path(meterId: string): string { return `/meters/${encodeURIComponent(meterId)}/readings`; }

export class ReadingsClient {
  private readonly transport: HttpClient;
  constructor(transport: HttpClient = http) { this.transport = transport; }

  private async json<T>(url: string, signal: AbortSignal, guard: (value: unknown) => value is T,
    status: number, request: Parameters<HttpClient['request']>[2] = {}): Promise<T> {
    const response = await this.transport.request(url, signal, request);
    const type: unknown = response.headers['content-type'];
    if (signal.aborted || response.status !== status || typeof type !== 'string' ||
        !/^application\/json(?:\s*;|$)/i.test(type) || !guard(response.data)) throw invalidResponse();
    return response.data;
  }

  async list(meterId: string, signal: AbortSignal): Promise<Reading[]> {
    const rows = await this.json(path(meterId), signal,
      (value): value is Reading[] => Array.isArray(value) && value.every(isReading), 200);
    if (!rows.every(row => row.meter_id === meterId)) throw invalidResponse();
    return rows;
  }

  async detail(meterId: string, readingId: string, signal: AbortSignal): Promise<Reading> {
    const row = await this.json(`${path(meterId)}/${encodeURIComponent(readingId)}`, signal, isReading, 200);
    if (row.meter_id !== meterId || row.id !== readingId) throw invalidResponse();
    return row;
  }

  async create(meterId: string, input: ReadingInput, key: string, signal: AbortSignal): Promise<Reading> {
    const row = await this.json(path(meterId), signal, isReading, 201,
      { method: 'POST', data: input, idempotencyKey: key });
    if (row.meter_id !== meterId) throw invalidResponse();
    return row;
  }

  async edit(meterId: string, readingId: string, input: ReadingEdit, signal: AbortSignal): Promise<Reading> {
    const row = await this.json(`${path(meterId)}/${encodeURIComponent(readingId)}`, signal, isReading, 200,
      { method: 'PATCH', data: input });
    if (row.meter_id !== meterId || row.id !== readingId || row.version !== input.version + 1) throw invalidResponse();
    return row;
  }

  async ocr(meterId: string, photo: string, crop: Crop, signal: AbortSignal): Promise<OcrResult> {
    return this.json(`${path(meterId)}/ocr`, signal, isOcr, 200,
      { method: 'POST', data: { photo_base64: photo, crop } });
  }

  async photo(meterId: string, readingId: string, signal: AbortSignal): Promise<Blob> {
    const response = await this.transport.request(`${path(meterId)}/${encodeURIComponent(readingId)}/photo`, signal,
      { responseType: 'blob' });
    const type: unknown = response.headers['content-type'];
    if (signal.aborted || response.status !== 200 || !(response.data instanceof Blob) ||
        response.data.size === 0 || typeof type !== 'string' || !/^image\/(jpeg|png|webp)$/i.test(type)) throw invalidResponse();
    return response.data;
  }
}

export const readingsApi = new ReadingsClient();
