import { useId } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import type { z } from 'zod';
import type { Domicile } from '../../diaryApi.ts';
import { domicileSchema } from '../diary/schemas.ts';
import { Button } from '../../components/ui/button.tsx';
import { Input } from '../../components/ui/input.tsx';
import { Label } from '../../components/ui/label.tsx';
import { duplicateAddress, meterSchema } from './schemas.ts';
import type { ManagedDomicile, Meter, MeterInput } from './api.ts';

export function AddressForm({ row, rows, busy, save, cancel }: {
  row: ManagedDomicile; rows: Domicile[]; busy: boolean; save: (address: string) => Promise<void>; cancel: () => void;
}) {
  const id = useId();
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm<z.input<typeof domicileSchema>, unknown, z.output<typeof domicileSchema>>({
    resolver: zodResolver(domicileSchema), defaultValues: { display_address: row.display_address },
  });
  const error = errors.display_address?.message;
  return <form noValidate aria-label="Corregir domicilio" className="space-y-3" onSubmit={handleSubmit(values => save(values.display_address))}>
    <Label htmlFor={id}>Dirección</Label>
    <Input id={id} {...register('display_address')} required maxLength={300} disabled={busy || isSubmitting} aria-invalid={Boolean(error)} aria-describedby={error ? `${id}-error` : undefined} />
    {error && <p id={`${id}-error`} role="alert">{error}</p>}
    {duplicateAddress(watch('display_address'), rows, row.id) && <p role="status">Ya existe un domicilio con esta dirección. Podés guardarlo igualmente.</p>}
    <p>Los próximos PDF usarán la dirección corregida; los cortes conservan su identidad.</p>
    <div className="flex flex-wrap gap-2"><Button disabled={busy || isSubmitting}>Guardar domicilio</Button><Button type="button" variant="outline" disabled={busy || isSubmitting} onClick={cancel}>Cancelar corrección de domicilio</Button></div>
  </form>;
}

export function MeterForm({ row, busy, save, cancel }: {
  row: Meter | null; busy: boolean; save: (input: MeterInput) => Promise<void>; cancel: () => void;
}) {
  const id = useId();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<z.input<typeof meterSchema>, unknown, z.output<typeof meterSchema>>({
    resolver: zodResolver(meterSchema), defaultValues: { meter_number: row?.meter_number ?? '', alias: row?.alias ?? '' },
  });
  const error = errors.meter_number?.message;
  return <form noValidate aria-label={row ? 'Corregir medidor' : 'Registrar medidor'} className="space-y-3" onSubmit={handleSubmit(save)}>
    <Label htmlFor={`${id}-number`}>Número de medidor</Label>
    <Input id={`${id}-number`} {...register('meter_number')} required disabled={busy || isSubmitting} aria-invalid={Boolean(error)} aria-describedby={error ? `${id}-error` : undefined} />
    {error && <p id={`${id}-error`} role="alert">{error}</p>}
    <Label htmlFor={`${id}-alias`}>Alias (opcional)</Label>
    <Input id={`${id}-alias`} {...register('alias')} disabled={busy || isSubmitting} />
    <div className="flex flex-wrap gap-2"><Button disabled={busy || isSubmitting}>{row ? 'Guardar medidor' : 'Registrar medidor'}</Button>{row && <Button type="button" variant="outline" disabled={busy || isSubmitting} onClick={cancel}>Cancelar corrección de medidor</Button>}</div>
  </form>;
}
