import { z } from 'zod';

// Shape and presentation limits only; the backend owns calendar/timezone/order rules.
const minute = z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/, 'Ingresá fecha y hora con precisión de minutos.');
const optionalText = (limit: number) => z.string().max(limit, `Usá como máximo ${limit} caracteres.`).transform(value => value === '' ? null : value);

export const loginSchema = z.object({
  username: z.string().min(1, 'Ingresá el usuario.').max(80, 'Usá como máximo 80 caracteres.'),
  password: z.string().min(1, 'Ingresá la contraseña.').max(1024, 'Usá como máximo 1024 caracteres.'),
});
export const domicileSchema = z.object({ display_address: z.string().trim().min(1, 'Ingresá el domicilio.').max(300, 'Usá como máximo 300 caracteres.') });
export const cutSchema = z.object({
  start_at: minute,
  end_at: z.union([z.literal(''), minute]).transform(value => value === '' ? null : value),
  observations: optionalText(4000),
  complaint_number: optionalText(120),
});
export const closedCutSchema = cutSchema.refine(value => value.end_at !== null, { path: ['end_at'], message: 'Un corte cerrado debe conservar su fecha de fin.' });
export const closeSchema = z.object({ end_at: minute });
export const periodSchema = z.object({ period_start: minute, period_end: minute });
