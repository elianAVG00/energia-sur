import type { Period } from './diaryApi.ts';

export type Remote<T> = { status: 'loading' } | { status: 'error'; message: string } | { status: 'ready'; data: T };

// Each lane accepts only its latest result, even when a transport ignores abort.
// Invalidation also protects account/domicile switches and component cleanup.
export class RequestScope {
  private readonly controllers = new Map<string, AbortController>();

  begin(lane: string): { signal: AbortSignal; isCurrent: () => boolean } {
    this.controllers.get(lane)?.abort();
    const controller = new AbortController();
    this.controllers.set(lane, controller);
    return {
      signal: controller.signal,
      isCurrent: () => !controller.signal.aborted && this.controllers.get(lane) === controller,
    };
  }

  invalidate(): void {
    for (const controller of this.controllers.values()) controller.abort();
    this.controllers.clear();
  }
}

export function minuteInput(timestamp: string): string {
  // Server timestamps are already expressed in Buenos Aires, not the host zone.
  return timestamp.slice(0, 16);
}

export function displayTimestamp(timestamp: string): string {
  const value = minuteInput(timestamp);
  return `${value.slice(8, 10)}/${value.slice(5, 7)}/${value.slice(0, 4)} ${value.slice(11)}`;
}

export function buenosAiresMinute(now: Date = new Date()): string {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Argentina/Buenos_Aires', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(now);
  const field = (type: Intl.DateTimeFormatPartTypes): string => {
    const value = parts.find((part) => part.type === type)?.value;
    if (!value) throw new Error('Missing calendar field');
    return value;
  };
  return `${field('year')}-${field('month')}-${field('day')}T${field('hour')}:${field('minute')}`;
}

export function defaultPeriod(now: Date = new Date()): Period {
  const day = buenosAiresMinute(now).slice(0, 10);
  // UTC is used only for calendar-day increment, never to reinterpret cut inputs.
  const next = new Date(`${day}T00:00:00Z`);
  next.setUTCDate(next.getUTCDate() + 1);
  return { period_start: `${day}T00:00`, period_end: `${next.toISOString().slice(0, 10)}T00:00` };
}
