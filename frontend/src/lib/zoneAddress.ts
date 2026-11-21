export function parseZoneAddress(input: string, partido: string, localidad: string) {
  const value = input.trim();
  const separator = value.lastIndexOf(',');
  if (separator < 0) {
    return value ? { address: value, hint: { partido, localidad } } : null;
  }

  const address = value.slice(0, separator).trim();
  const typedPartido = value.slice(separator + 1).trim();
  if (!address || !typedPartido) return null;

  return { address, hint: { partido: typedPartido } };
}
