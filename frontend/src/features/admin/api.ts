import type { AxiosResponse } from 'axios';
import { createHttpClient, http } from '../../lib/http.ts';
import type { HttpClient } from '../../lib/http.ts';
import { invalidResponse } from '../../lib/httpError.ts';

export type SourceKey = 'outages' | 'scheduled_works';
export type IntervalSeconds = 300 | 600 | 900 | 1800 | 3600;

export const ALLOWED_INTERVALS: readonly IntervalSeconds[] = [300, 600, 900, 1800, 3600];

export interface SourceStatus {
  key: SourceKey;
  scheduler_enabled: boolean;
  interval_seconds: IntervalSeconds;
  version: number;
  last_attempt_at: string | null;
  last_attempt_outcome: string | null;
  last_attempt_error: string | null;
  last_success_at: string | null;
  last_skipped_locked_at: string | null;
}

export interface SourcesResult {
  sources: SourceStatus[];
}

export interface IntervalResult {
  key: SourceKey;
  interval_seconds: IntervalSeconds;
  version: number;
}

export interface RefreshResult {
  key: SourceKey;
  outcome: string;
  http_status: number | null;
  detail_code: string | null;
  started_at: string | null;
  finished_at: string | null;
}

const KEYS = ['outages', 'scheduled_works'] as const;
const INTERVALS = [300, 600, 900, 1800, 3600] as const;
const INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/;

// Only the synchronous retry gets a longer deadline; the shared client keeps 10 s.
const retryTransport = createHttpClient({
  timeout: 25_000,
  deadlineSignal: () => AbortSignal.timeout(25_000),
});

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function oneOf<T extends string>(value: unknown, values: readonly T[]): value is T {
  return typeof value === 'string' && (values as readonly string[]).includes(value);
}

function isInterval(value: unknown): value is IntervalSeconds {
  return typeof value === 'number' && (INTERVALS as readonly number[]).includes(value);
}

function isPositiveInteger(value: unknown): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value > 0;
}

function optionalText(value: unknown): value is string | null {
  return value === null || (typeof value === 'string' && value.length > 0);
}

function optionalInstant(value: unknown): value is string | null {
  return value === null ||
    (typeof value === 'string' && INSTANT.test(value) && Number.isFinite(Date.parse(value)));
}

function optionalInteger(value: unknown): value is number | null {
  return value === null || Number.isSafeInteger(value);
}

function isSourceStatus(value: unknown): value is SourceStatus {
  if (!record(value)) return false;
  return oneOf(value.key, KEYS) && typeof value.scheduler_enabled === 'boolean' &&
    isInterval(value.interval_seconds) && isPositiveInteger(value.version) &&
    optionalInstant(value.last_attempt_at) && optionalText(value.last_attempt_outcome) &&
    optionalText(value.last_attempt_error) && optionalInstant(value.last_success_at) &&
    optionalInstant(value.last_skipped_locked_at);
}

function isSourcesResult(value: unknown): value is SourcesResult {
  if (!record(value) || !Array.isArray(value.sources) ||
      value.sources.length !== KEYS.length || !value.sources.every(isSourceStatus)) {
    return false;
  }
  return new Set(value.sources.map(source => source.key)).size === KEYS.length;
}

function isIntervalResult(value: unknown): value is IntervalResult {
  return record(value) && oneOf(value.key, KEYS) &&
    isInterval(value.interval_seconds) && isPositiveInteger(value.version);
}

function isRefreshResult(value: unknown): value is RefreshResult {
  return record(value) && oneOf(value.key, KEYS) &&
    typeof value.outcome === 'string' && value.outcome.length > 0 &&
    optionalInteger(value.http_status) && optionalText(value.detail_code) &&
    optionalInstant(value.started_at) && optionalInstant(value.finished_at);
}

function parseJson<T>(
  response: AxiosResponse<unknown>, signal: AbortSignal,
  guard: (value: unknown) => value is T,
): T {
  const type = response.headers['content-type'];
  if (signal.aborted || response.status !== 200 || typeof type !== 'string' ||
      !/^application\/json(?:\s*;|$)/i.test(type) || !guard(response.data)) {
    throw invalidResponse();
  }
  return response.data;
}

export class AdminClient {
  private readonly transport: HttpClient;
  private readonly retry: HttpClient;

  constructor(transport: HttpClient = http, retry: HttpClient = retryTransport) {
    this.transport = transport;
    this.retry = retry;
  }

  async sources(signal: AbortSignal): Promise<SourcesResult> {
    return parseJson(
      await this.transport.request('/admin/sources', signal), signal, isSourcesResult,
    );
  }

  async refresh(key: SourceKey, signal: AbortSignal): Promise<RefreshResult> {
    // This endpoint is synchronous and may outlast the shared 10 s deadline.
    return parseJson(
      await this.retry.request(`/admin/sources/${key}/refresh`, signal, { method: 'POST' }),
      signal, isRefreshResult,
    );
  }

  async setInterval(
    key: SourceKey, interval: IntervalSeconds, version: number, signal: AbortSignal,
  ): Promise<IntervalResult> {
    return parseJson(
      await this.transport.request(`/admin/sources/${key}/interval`, signal, {
        method: 'PATCH', data: { interval_seconds: interval, version },
      }),
      signal, isIntervalResult,
    );
  }
}

export const adminApi = new AdminClient();
