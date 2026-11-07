import { http } from './lib/http.ts';
import type { HttpClient } from './lib/http.ts';
import { DiaryError, invalidResponse } from './lib/httpError.ts';
export { DiaryError, errorMessage } from './lib/httpError.ts';

export interface Account { id: string; username: string }
export interface Session { account: Account; csrf_token: string }
export interface Domicile { id: string; display_address: string }
export interface Cut {
  id: string;
  domicile_id: string;
  start_at: string;
  end_at: string | null;
  observations: string | null;
  complaint_number: string | null;
  version: number;
  status: 'ongoing' | 'closed';
}
export interface CutInput {
  start_at: string;
  end_at: string | null;
  observations: string | null;
  complaint_number: string | null;
}
export interface Period { period_start: string; period_end: string }
export interface Summary extends Period {
  domicile: Domicile;
  generated_at: string;
  timezone: string;
  total_minutes: number;
  total_hours: number;
  remaining_minutes: number;
  entries: Cut[];
}

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function text(value: unknown): value is string { return typeof value === 'string'; }
function identifier(value: unknown): value is string { return text(value) && value.length > 0; }
function optionalText(value: unknown): value is string | null { return value === null || text(value); }
function integer(value: unknown): value is number { return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0; }
function timestamp(value: unknown): value is string {
  return text(value) && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::00)?[+-]\d{2}:\d{2}$/.test(value) && Number.isFinite(Date.parse(value));
}
export function isSession(value: unknown): value is Session {
  return record(value) && record(value.account) && identifier(value.account.id) &&
    identifier(value.account.username) && identifier(value.csrf_token);
}
export function isDomicile(value: unknown): value is Domicile {
  return record(value) && identifier(value.id) && identifier(value.display_address);
}
export function isCut(value: unknown): value is Cut {
  return record(value) && identifier(value.id) && identifier(value.domicile_id) &&
    timestamp(value.start_at) && (value.end_at === null || timestamp(value.end_at)) &&
    optionalText(value.observations) && optionalText(value.complaint_number) &&
    integer(value.version) && value.version > 0 &&
    ((value.status === 'ongoing' && value.end_at === null) || (value.status === 'closed' && value.end_at !== null));
}
export function isSummary(value: unknown): value is Summary {
  return record(value) && isDomicile(value.domicile) && timestamp(value.period_start) &&
    timestamp(value.period_end) && timestamp(value.generated_at) &&
    value.timezone === 'America/Argentina/Buenos_Aires' && integer(value.total_minutes) &&
    integer(value.total_hours) && integer(value.remaining_minutes) && value.remaining_minutes < 60 &&
    Array.isArray(value.entries) && value.entries.every(isCut);
}
function isDomiciles(value: unknown): value is Domicile[] {
  return Array.isArray(value) && value.every(isDomicile);
}
function isCuts(value: unknown): value is Cut[] { return Array.isArray(value) && value.every(isCut); }
export class DiaryClient {
  private readonly transport: HttpClient;
  constructor(transport: HttpClient = http) { this.transport = transport; }

  private async json<T>(path: string, signal: AbortSignal, validate: (value: unknown) => value is T,
    expected: number, request: Parameters<HttpClient['request']>[2] = {}): Promise<T> {
    const response = await this.transport.request(path, signal, request);
    const contentType: unknown = response.headers['content-type'];
    if (response.status !== expected || typeof contentType !== 'string' || !/^application\/json(?:\s*;|$)/i.test(contentType)) throw invalidResponse();
    const body: unknown = response.data;
    if (signal.aborted) throw new DiaryError('aborted', 'La solicitud fue cancelada.');
    if (!validate(body)) throw invalidResponse();
    return body;
  }

  private mutation(method: 'POST' | 'PATCH', data: unknown) {
    return { method, data };
  }
  session(signal: AbortSignal): Promise<Session> { return this.json('/session', signal, isSession, 200); }
  login(username: string, password: string, signal: AbortSignal): Promise<Session> {
    // The browser supplies Origin. Never forge it or store credentials in browser storage.
    return this.json('/login', signal, isSession, 200, {
      method: 'POST', data: { username, password },
    });
  }
  async logout(csrf: string, signal: AbortSignal): Promise<void> {
    const response = await this.transport.request('/logout', signal, { method: 'POST', logoutToken: csrf });
    if (response.status !== 204) throw invalidResponse();
  }
  domiciles(signal: AbortSignal): Promise<Domicile[]> { return this.json('/domiciles', signal, isDomiciles, 200); }
  createDomicile(display_address: string, _csrf: string, signal: AbortSignal): Promise<Domicile> {
    return this.json('/domiciles', signal, isDomicile, 201, this.mutation('POST', { display_address }));
  }
  async cuts(id: string, signal: AbortSignal): Promise<Cut[]> {
    const cuts = await this.json(`/domiciles/${encodeURIComponent(id)}/interruptions`, signal, isCuts, 200);
    if (!cuts.every((cut) => cut.domicile_id === id)) throw invalidResponse();
    return cuts;
  }
  async createCut(id: string, input: CutInput, _csrf: string, signal: AbortSignal): Promise<Cut> {
    const cut = await this.json(`/domiciles/${encodeURIComponent(id)}/interruptions`, signal, isCut, 201, this.mutation('POST', input));
    if (cut.domicile_id !== id) throw invalidResponse();
    return cut;
  }
  async correctCut(cut: Cut, input: CutInput, _csrf: string, signal: AbortSignal): Promise<Cut> {
    const result = await this.json(`/interruptions/${encodeURIComponent(cut.id)}`, signal, isCut, 200,
      this.mutation('PATCH', { ...input, version: cut.version }));
    if (result.id !== cut.id || result.domicile_id !== cut.domicile_id) throw invalidResponse();
    return result;
  }
  async closeCut(cut: Cut, end_at: string, _csrf: string, signal: AbortSignal): Promise<Cut> {
    const result = await this.json(`/interruptions/${encodeURIComponent(cut.id)}/close`, signal, isCut, 200,
      this.mutation('POST', { end_at, version: cut.version }));
    if (result.id !== cut.id || result.domicile_id !== cut.domicile_id) throw invalidResponse();
    return result;
  }
  async summary(id: string, period: Period, signal: AbortSignal): Promise<Summary> {
    const summary = await this.json(this.reportPath(id, 'summary', period), signal, isSummary, 200);
    if (summary.domicile.id !== id || !summary.entries.every((cut) => cut.domicile_id === id)) throw invalidResponse();
    return summary;
  }
  private reportPath(id: string, resource: string, period: Period): string {
    const query = new URLSearchParams({ period_start: period.period_start, period_end: period.period_end });
    return `/domiciles/${encodeURIComponent(id)}/${resource}?${query.toString()}`;
  }
  async pdf(id: string, period: Period, signal: AbortSignal): Promise<Blob> {
    const response = await this.transport.request(this.reportPath(id, 'report.pdf', period), signal, { responseType: 'blob' });
    const contentType: unknown = response.headers['content-type'];
    if (response.status !== 200 || typeof contentType !== 'string' || !/^application\/pdf(?:\s*;|$)/i.test(contentType)) throw invalidResponse();
    const blob: unknown = response.data;
    if (signal.aborted) throw new DiaryError('aborted', 'La solicitud fue cancelada.');
    if (!(blob instanceof Blob) || blob.size === 0) throw invalidResponse();
    return blob;
  }
}

export const diaryApi = new DiaryClient();
