import { http } from '../../lib/http.ts';
import type { HttpClient } from '../../lib/http.ts';
import { invalidResponse } from '../../lib/httpError.ts';

const INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;
const DATE = /^\d{4}-\d{2}-\d{2}$/;
const DECIMAL = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;

export interface ConsumptionInterval {
  start_reading_id: string;
  end_reading_id: string;
  start_at: string;
  end_at: string;
  start_local_date: string;
  end_local_date: string;
  start_value_kwh: string;
  end_value_kwh: string;
  consumption_kwh: string | null;
  daily_average_kwh_day: string | null;
  calculable: boolean;
  sub_day: boolean;
  below_minimum: boolean;
}

export interface ConsumptionEvolution {
  meter_id: string;
  intervals: ConsumptionInterval[];
}

export type EstimateReason = 'insufficient_readings' | 'decreasing_latest';

export type ConsumptionEstimate =
  | {
      meter_id: string;
      status: 'available';
      days: number;
      daily_average_kwh_day: string;
      estimate_kwh: string;
      orientative: true;
      below_minimum: boolean;
      daily_average_below_minimum: boolean;
      sub_day: boolean;
      base_start_reading_id: string;
      base_end_reading_id: string;
      base_start_at: string;
      base_end_at: string;
    }
  | { meter_id: string; status: 'base_unavailable'; reason: EstimateReason };

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function decimal(value: unknown): value is string {
  return typeof value === 'string' && DECIMAL.test(value);
}

function isInterval(value: unknown): value is ConsumptionInterval {
  if (!record(value)) return false;
  const row = value;
  const id = (v: unknown): v is string => typeof v === 'string' && v.length > 0;
  if (!id(row.start_reading_id) || !id(row.end_reading_id)) return false;
  for (const key of ['start_at', 'end_at'] as const) {
    if (typeof row[key] !== 'string' || !INSTANT.test(row[key]) ||
        !Number.isFinite(Date.parse(row[key]))) return false;
  }
  for (const key of ['start_local_date', 'end_local_date'] as const) {
    if (typeof row[key] !== 'string' || !DATE.test(row[key])) return false;
  }
  if (!decimal(row.start_value_kwh) || !decimal(row.end_value_kwh)) return false;
  if (typeof row.calculable !== 'boolean' || typeof row.sub_day !== 'boolean' ||
      typeof row.below_minimum !== 'boolean') return false;
  if (row.calculable) {
    return decimal(row.consumption_kwh) && decimal(row.daily_average_kwh_day);
  }
  return row.consumption_kwh === null && row.daily_average_kwh_day === null;
}

function isEvolution(value: unknown): value is ConsumptionEvolution {
  return record(value) && typeof value.meter_id === 'string' && value.meter_id.length > 0 &&
    Array.isArray(value.intervals) && value.intervals.every(isInterval);
}

function isEstimate(value: unknown): value is ConsumptionEstimate {
  if (!record(value)) return false;
  if (typeof value.meter_id !== 'string' || value.meter_id.length === 0) return false;
  if (value.status === 'base_unavailable') {
    return value.reason === 'insufficient_readings' || value.reason === 'decreasing_latest';
  }
  if (value.status !== 'available') return false;
  return typeof value.days === 'number' && Number.isSafeInteger(value.days) &&
    value.days >= 1 && value.days <= 90 &&
    decimal(value.daily_average_kwh_day) && decimal(value.estimate_kwh) &&
    value.orientative === true && typeof value.below_minimum === 'boolean' &&
    typeof value.daily_average_below_minimum === 'boolean' &&
    typeof value.sub_day === 'boolean' &&
    typeof value.base_start_reading_id === 'string' && value.base_start_reading_id.length > 0 &&
    typeof value.base_end_reading_id === 'string' && value.base_end_reading_id.length > 0 &&
    typeof value.base_start_at === 'string' && INSTANT.test(value.base_start_at) &&
    Number.isFinite(Date.parse(value.base_start_at)) &&
    typeof value.base_end_at === 'string' && INSTANT.test(value.base_end_at) &&
    Number.isFinite(Date.parse(value.base_end_at));
}

function path(meterId: string): string {
  return `/meters/${encodeURIComponent(meterId)}/consumption-evolution`;
}

export class ConsumptionClient {
  private readonly transport: HttpClient;
  constructor(transport: HttpClient = http) { this.transport = transport; }

  private async json<T>(url: string, signal: AbortSignal, guard: (value: unknown) => value is T): Promise<T> {
    const response = await this.transport.request(url, signal);
    const type: unknown = response.headers['content-type'];
    if (signal.aborted || response.status !== 200 || typeof type !== 'string' ||
        !/^application\/json(?:\s*;|$)/i.test(type) || !guard(response.data)) throw invalidResponse();
    return response.data;
  }

  async evolution(meterId: string, from: string, to: string, signal: AbortSignal): Promise<ConsumptionEvolution> {
    const query = new URLSearchParams();
    if (from) query.set('from', from);
    if (to) query.set('to', to);
    const suffix = query.size ? `?${query.toString()}` : '';
    const value = await this.json(`${path(meterId)}${suffix}`, signal, isEvolution);
    if (value.meter_id !== meterId) throw invalidResponse();
    return value;
  }

  async estimate(meterId: string, days: number, signal: AbortSignal): Promise<ConsumptionEstimate> {
    const value = await this.json(
      `/meters/${encodeURIComponent(meterId)}/consumption-estimate?days=${days}`, signal, isEstimate);
    if (value.meter_id !== meterId) throw invalidResponse();
    return value;
  }
}

export const consumptionApi = new ConsumptionClient();
