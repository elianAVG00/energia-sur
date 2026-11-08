import { z } from 'zod';

// Presentation checks only; the server validates and normalizes the submitted values.
export const meterSchema = z.object({
  meter_number: z.string().refine(value => value.trim().length > 0, 'Ingresá el número de medidor.'),
  alias: z.string().transform(value => value === '' ? null : value),
});

export function duplicateAddress(address: string, rows: { id: string; display_address: string }[], excludeId?: string): boolean {
  const candidate = address.trim();
  return candidate.length > 0 && rows.some(row => row.id !== excludeId && row.display_address.trim() === candidate);
}
