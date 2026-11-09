/** Keep kWh readings exact without converting them to JavaScript numbers. */
export const MAX_READING_DIGITS = 131_072;

export function canonicalReading(value: string): string | null {
  if (value.length === 0 || value.length > MAX_READING_DIGITS || !/^[0-9]+$/.test(value)) return null;
  return value.replace(/^0+/, '') || '0';
}

/** Presentation warning only; the backend remains authoritative. */
export function readingIsLower(value: string, previous: string): boolean | null {
  const current = canonicalReading(value);
  const prior = canonicalReading(previous);
  if (current === null || prior === null) return null;
  return current.length < prior.length || (current.length === prior.length && current < prior);
}
