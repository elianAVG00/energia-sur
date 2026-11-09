import { http } from '../../lib/http.ts';
import type { HttpClient } from '../../lib/http.ts';
import { invalidResponse, isComparisonCandidate } from '../../lib/httpError.ts';
import type { ComparisonCandidate } from '../../lib/httpError.ts';

export type ComparisonOutcome = 'recorded_higher' | 'billed_higher' | 'equal';
export interface CandidateSets {
  bill_id: string; meter_id: string; period_start: string; period_end: string; billed_kwh: string;
  start_candidates: ComparisonCandidate[]; end_candidates: ComparisonCandidate[];
}
export interface ComparisonResult {
  bill_id: string; meter_id: string; period_start: string; period_end: string; billed_kwh: string;
  status: 'comparable' | 'no_comparison';
  reason: 'decreasing_reading' | null;
  exact: boolean;
  start_reading: ComparisonCandidate | null;
  end_reading: ComparisonCandidate | null;
  recorded_kwh: string | null;
  difference_kwh: string | null;
  outcome: ComparisonOutcome | null;
}

const DATE = /^\d{4}-\d{2}-\d{2}$/;
const DECIMAL = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;
const ID = /^[0-9a-zA-Z-]+$/;

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function candidates(value: unknown): value is ComparisonCandidate[] {
  return Array.isArray(value) && value.every(isComparisonCandidate);
}
function isCandidateSets(value: unknown): value is CandidateSets {
  return record(value) &&
    typeof value.bill_id === 'string' && value.bill_id.length > 0 &&
    typeof value.meter_id === 'string' && value.meter_id.length > 0 &&
    typeof value.period_start === 'string' && DATE.test(value.period_start) &&
    typeof value.period_end === 'string' && DATE.test(value.period_end) &&
    value.period_start <= value.period_end &&
    typeof value.billed_kwh === 'string' && DECIMAL.test(value.billed_kwh) &&
    candidates(value.start_candidates) && candidates(value.end_candidates);
}
function isOutcome(value: unknown): value is ComparisonOutcome {
  return value === 'recorded_higher' || value === 'billed_higher' || value === 'equal';
}
function isComparison(value: unknown): value is ComparisonResult {
  if (!record(value)) return false;
  if (typeof value.bill_id !== 'string' || typeof value.meter_id !== 'string') return false;
  if (typeof value.period_start !== 'string' || !DATE.test(value.period_start)) return false;
  if (typeof value.period_end !== 'string' || !DATE.test(value.period_end)) return false;
  if (typeof value.billed_kwh !== 'string' || !DECIMAL.test(value.billed_kwh)) return false;
  if (typeof value.exact !== 'boolean') return false;
  if (value.start_reading !== null && !isComparisonCandidate(value.start_reading)) return false;
  if (value.end_reading !== null && !isComparisonCandidate(value.end_reading)) return false;
  if (value.status === 'no_comparison') {
    return value.reason === 'decreasing_reading' && value.recorded_kwh === null &&
      value.difference_kwh === null && value.outcome === null;
  }
  return value.status === 'comparable' &&
    typeof value.recorded_kwh === 'string' && DECIMAL.test(value.recorded_kwh) &&
    typeof value.difference_kwh === 'string' && DECIMAL.test(value.difference_kwh) &&
    isOutcome(value.outcome) && isComparisonCandidate(value.start_reading) &&
    isComparisonCandidate(value.end_reading);
}
function path(meter: string, bill: string): string {
  return `/meters/${encodeURIComponent(meter)}/bills/${encodeURIComponent(bill)}`;
}
function selection(value: string): string {
  if (!ID.test(value)) throw invalidResponse();
  return encodeURIComponent(value);
}

export class ComparisonsClient {
  private readonly transport: HttpClient;
  constructor(transport: HttpClient = http) { this.transport = transport; }
  private async json<T>(url: string, signal: AbortSignal, guard: (value: unknown) => value is T): Promise<T> {
    const response = await this.transport.request(url, signal);
    const type: unknown = response.headers['content-type'];
    if (signal.aborted || response.status !== 200 || typeof type !== 'string' ||
        !/^application\/json(?:\s*;|$)/i.test(type) || !guard(response.data)) throw invalidResponse();
    return response.data;
  }
  async candidates(meter: string, bill: string, signal: AbortSignal): Promise<CandidateSets> {
    const value = await this.json(`${path(meter, bill)}/comparison-candidates`, signal, isCandidateSets);
    if (value.meter_id !== meter || value.bill_id !== bill) throw invalidResponse();
    return value;
  }
  async compare(meter: string, bill: string, start: string, end: string,
    confirmApproximate: boolean, signal: AbortSignal): Promise<ComparisonResult> {
    const query = new URLSearchParams({
      start_reading_id: selection(start), end_reading_id: selection(end),
    });
    if (confirmApproximate) query.set('confirm_approximate', 'true');
    const value = await this.json(`${path(meter, bill)}/comparison?${query.toString()}`, signal, isComparison);
    if (value.meter_id !== meter || value.bill_id !== bill) throw invalidResponse();
    return value;
  }
}

export const comparisonsApi = new ComparisonsClient();
