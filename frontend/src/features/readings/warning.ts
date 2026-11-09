import type { Reading } from './api.ts';
import { readingIsLower } from './value.ts';

/** Presentation only: the server remains authoritative for dates and ownership. */
export function lowerReadingWarning(
  readings: readonly Reading[], meterId: string, recordedAt: string, value: string, editingId?: string,
): boolean | null {
  const instant = Date.parse(recordedAt);
  if (!Number.isFinite(instant)) return null;
  let previous: Reading | undefined;
  let previousInstant = -Infinity;
  for (const reading of readings) {
    if (reading.meter_id !== meterId || reading.id === editingId) continue;
    const candidate = Date.parse(reading.recorded_at);
    if (Number.isFinite(candidate) && candidate < instant && candidate > previousInstant) {
      previous = reading;
      previousInstant = candidate;
    }
  }
  return previous ? readingIsLower(value, previous.value_kwh) : null;
}
