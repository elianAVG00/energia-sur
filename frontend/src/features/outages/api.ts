import type { AxiosResponse } from 'axios';

import { http } from '../../lib/http.ts';
import type { HttpClient } from '../../lib/http.ts';
import { invalidResponse } from '../../lib/httpError.ts';

export type CoverageStatus = 'covered' | 'out_of_coverage' | 'coverage_unverified';
export type OutageState =
  | 'geographic_error' | 'out_of_coverage' | 'unavailable' | 'stale'
  | 'reported' | 'no_reports' | 'coverage_unverified';
export type Freshness = 'fresh' | 'stale' | 'unavailable';
export type Category = 'medium_voltage' | 'low_voltage' | 'preventive';
export type Granularity = 'localidad' | 'partido';
export type SourceStatus = 'ok' | 'degraded';

export interface Outage {
  category: Category;
  partido: string;
  localidad?: string | null;
  subestacion_alimentador?: string | null;
  affected_users?: number | null;
  normalizacion?: string | null;
}

export interface AreaCoverage {
  partido: string;
  localidad?: string | null;
  status: CoverageStatus;
}

export interface OutagesResult {
  state: OutageState;
  source_status: SourceStatus;
  freshness: Freshness;
  granularity: Granularity;
  source: string;
  source_url: string;
  fetched_at?: string;
  source_updated_at?: string;
  source_reported_time?: string;
  coverage: AreaCoverage;
  totals_scope: 'edesur';
  total_users_without?: number;
  total_users_with?: number;
  users_affected_yesterday?: number;
  outages?: Outage[];
}

export interface AreaLocalidad {
  localidad?: string | null;
  coverage: CoverageStatus;
  reported: boolean;
}

export interface AreaPartido {
  partido: string;
  localidades: AreaLocalidad[];
}

export interface AreasResult {
  coverage_version: string | null;
  coverage_retrieved_on: string | null;
  areas: AreaPartido[];
}

export interface ResolveZone {
  partido: string;
  localidad?: string | null;
  granularity: Granularity;
  coverage: CoverageStatus;
}

export type ResolveResult =
  | { status: 'resolved'; zone: ResolveZone }
  | { status: 'candidates'; candidates: ResolveZone[] };

export interface ResolveHint {
  partido?: string;
  localidad?: string;
}

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function oneOf<T extends string>(value: unknown, values: readonly T[]): value is T {
  return typeof value === 'string' && (values as readonly string[]).includes(value);
}

const CATEGORIES = ['medium_voltage', 'low_voltage', 'preventive'] as const;
const COVERAGE = ['covered', 'out_of_coverage', 'coverage_unverified'] as const;
const STATES = ['geographic_error', 'out_of_coverage', 'unavailable', 'stale',
  'reported', 'no_reports', 'coverage_unverified'] as const;
const FRESHNESS = ['fresh', 'stale', 'unavailable'] as const;
const GRANULARITY = ['localidad', 'partido'] as const;

function optionalInteger(value: unknown): value is number | null | undefined {
  return value === undefined || value === null ||
    (typeof value === 'number' && Number.isSafeInteger(value) && value >= 0);
}

function optionalText(value: unknown): value is string | undefined {
  return value === undefined || (typeof value === 'string' && value.length > 0);
}

function optionalNullableText(value: unknown): value is string | null | undefined {
  return value === undefined || value === null ||
    (typeof value === 'string' && value.length > 0);
}

function isOutage(value: unknown): value is Outage {
  if (!record(value)) return false;
  return oneOf(value.category, CATEGORIES) && typeof value.partido === 'string' &&
    value.partido.length > 0 && optionalNullableText(value.localidad) &&
    optionalNullableText(value.subestacion_alimentador) &&
    optionalNullableText(value.normalizacion) && optionalInteger(value.affected_users);
}

function isAreaCoverage(value: unknown): value is AreaCoverage {
  return record(value) && typeof value.partido === 'string' && value.partido.length > 0 &&
    optionalNullableText(value.localidad) && oneOf(value.status, COVERAGE);
}

function isOutagesResult(value: unknown): value is OutagesResult {
  if (!record(value)) return false;
  if (!oneOf(value.state, STATES) || !oneOf(value.freshness, FRESHNESS) ||
      !oneOf(value.granularity, GRANULARITY) || !oneOf(value.source_status, ['ok', 'degraded'])) {
    return false;
  }
  if (typeof value.source !== 'string' || !value.source || typeof value.source_url !== 'string' ||
      !value.source_url.startsWith('https://')) return false;
  if (!isAreaCoverage(value.coverage) || value.totals_scope !== 'edesur') return false;
  for (const key of ['fetched_at', 'source_updated_at', 'source_reported_time'] as const) {
    if (!optionalText(value[key])) return false;
  }
  for (const key of ['total_users_without', 'total_users_with', 'users_affected_yesterday'] as const) {
    if (!optionalInteger(value[key])) return false;
  }
  if (value.outages !== undefined &&
      (!Array.isArray(value.outages) || !value.outages.every(isOutage))) return false;
  return true;
}

function isAreaLocalidad(value: unknown): value is AreaLocalidad {
  return record(value) && optionalNullableText(value.localidad) &&
    oneOf(value.coverage, COVERAGE) && typeof value.reported === 'boolean';
}

function isAreaPartido(value: unknown): value is AreaPartido {
  return record(value) && typeof value.partido === 'string' && value.partido.length > 0 &&
    Array.isArray(value.localidades) && value.localidades.every(isAreaLocalidad);
}

function isAreasResult(value: unknown): value is AreasResult {
  return record(value) &&
    (value.coverage_version === null || typeof value.coverage_version === 'string') &&
    (value.coverage_retrieved_on === null || typeof value.coverage_retrieved_on === 'string') &&
    Array.isArray(value.areas) && value.areas.every(isAreaPartido);
}

function isResolveZone(value: unknown): value is ResolveZone {
  return record(value) && typeof value.partido === 'string' && value.partido.length > 0 &&
    optionalNullableText(value.localidad) && oneOf(value.granularity, GRANULARITY) &&
    oneOf(value.coverage, COVERAGE);
}

function isResolveResult(value: unknown): value is ResolveResult {
  if (!record(value)) return false;
  if (value.status === 'resolved') return isResolveZone(value.zone);
  if (value.status === 'candidates') {
    return Array.isArray(value.candidates) && value.candidates.length > 0 &&
      value.candidates.every(isResolveZone);
  }
  return false;
}

function parseJson<T>(response: AxiosResponse<unknown>, signal: AbortSignal,
                      guard: (value: unknown) => value is T): T {
  const type = response.headers['content-type'];
  if (signal.aborted || response.status !== 200 || typeof type !== 'string' ||
      !/^application\/json(?:\s*;|$)/i.test(type) || !guard(response.data)) {
    throw invalidResponse();
  }
  return response.data;
}

export class OutagesClient {
  private readonly transport: HttpClient;
  constructor(transport: HttpClient = http) { this.transport = transport; }

  private async get<T>(url: string, signal: AbortSignal,
                       guard: (value: unknown) => value is T): Promise<T> {
    return parseJson(await this.transport.request(url, signal), signal, guard);
  }

  private async post<T>(url: string, body: object, signal: AbortSignal,
                        guard: (value: unknown) => value is T): Promise<T> {
    return parseJson(
      await this.transport.request(url, signal, { method: 'POST', data: body }), signal, guard,
    );
  }

  areas(signal: AbortSignal): Promise<AreasResult> {
    return this.get('/outages/areas', signal, isAreasResult);
  }

  query(partido: string, localidad: string, signal: AbortSignal): Promise<OutagesResult> {
    const query = new URLSearchParams({ partido });
    if (localidad) query.set('localidad', localidad);
    return this.get(`/outages?${query.toString()}`, signal, isOutagesResult);
  }

  resolve(address: string, hint: ResolveHint, signal: AbortSignal): Promise<ResolveResult> {
    const body: Record<string, string> = { address };
    if (hint.partido) body.partido = hint.partido;
    if (hint.localidad) body.localidad = hint.localidad;
    return this.post('/outages/resolve', body, signal, isResolveResult);
  }

  resolveLocation(lat: number, lon: number, signal: AbortSignal): Promise<ResolveResult> {
    return this.post('/outages/resolve-location', { lat, lon }, signal, isResolveResult);
  }
}

export const outagesApi = new OutagesClient();
