// Presentation helpers for CU08 consumption values. All arithmetic here is done
// on decimal strings, never on JavaScript floats, so display rounding is exact.

export function roundTwoDecimals(value: string): string {
  const negative = value.startsWith('-');
  const abs = negative ? value.slice(1) : value;
  const parts = abs.split('.');
  const intPart = parts[0] ?? '';
  const fracPart = parts[1] ?? '';
  const frac = fracPart.padEnd(3, '0');
  const head = frac.slice(0, 2);
  const third = frac.charCodeAt(2) - 48; // digit value of the third decimal
  let integer = BigInt(intPart === '' ? '0' : intPart);
  let cents = Number(head);
  if (third >= 5) {
    cents += 1;
    if (cents === 100) { cents = 0; integer += 1n; }
  }
  const centsStr = String(cents).padStart(2, '0');
  const sign = negative && (integer !== 0n || cents !== 0) ? '-' : '';
  return `${sign}${integer.toString()}.${centsStr}`;
}

// A positive value whose two-decimal rendering is "0.00" is shown as "< 0.01"
// (below_minimum), never as a bare "0.00". Zero is a real zero.
export function displayKwh(value: string, belowMinimum: boolean): string {
  if (belowMinimum) return '< 0.01';
  return roundTwoDecimals(value);
}
