import { useEffect, useId } from 'react';
import type { ReactNode } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import type { z } from 'zod';
import type { Cut, CutInput, Period } from '../../diaryApi.ts';
import { defaultPeriod, displayTimestamp, minuteInput } from '../../diaryState.ts';
import { Button } from '../../components/ui/button.tsx';
import { Input } from '../../components/ui/input.tsx';
import { Textarea } from '../../components/ui/textarea.tsx';
import { Label } from '../../components/ui/label.tsx';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card.tsx';
import { loginSchema, domicileSchema, cutSchema, closedCutSchema, closeSchema, periodSchema } from './schemas.ts';

function Field({ id, label, error, children }: { id: string; label: string; error: string | undefined; children: ReactNode }) {
  return <div className="space-y-2"><Label htmlFor={id}>{label}</Label>{children}{error && <p id={`${id}-error`} role="alert" className="text-sm text-destructive">{error}</p>}</div>;
}
function feedback(id: string, error: string | undefined) {
  return { id, 'aria-invalid': Boolean(error), 'aria-describedby': error ? `${id}-error` : undefined };
}
const actions = 'flex flex-wrap gap-3';

export function LoginForm({ pending, login }: { pending: boolean; login: (values: z.output<typeof loginSchema>) => Promise<void> }) {
  const id = useId();
  const { register, handleSubmit, resetField, formState: { errors, isSubmitting } } = useForm<z.input<typeof loginSchema>, unknown, z.output<typeof loginSchema>>({ resolver: zodResolver(loginSchema), defaultValues: { username: '', password: '' }, shouldUnregister: true });
  useEffect(() => () => resetField('password', { defaultValue: '' }), [resetField]);
  const disabled = pending || isSubmitting;
  return <Card><CardHeader><CardTitle>Ingresar</CardTitle></CardHeader><CardContent>
    <form noValidate aria-label="Ingresar" className="max-w-lg space-y-4" onSubmit={handleSubmit(async values => {
      try { await login(values); } finally { resetField('password', { defaultValue: '' }); }
    }, () => resetField('password', { defaultValue: '' }))}>
      <Field id={`${id}-username`} label="Usuario" error={errors.username?.message}><Input {...register('username')} {...feedback(`${id}-username`, errors.username?.message)} required autoComplete="username" maxLength={80} disabled={disabled} /></Field>
      <Field id={`${id}-password`} label="Contraseña" error={errors.password?.message}><Input {...register('password')} {...feedback(`${id}-password`, errors.password?.message)} type="password" required autoComplete="current-password" maxLength={1024} disabled={disabled} /></Field>
      <Button disabled={disabled}>Ingresar</Button>
      <p className="text-sm text-muted-foreground">Usá una cuenta aprovisionada localmente. No hay registro público de cuentas.</p>
    </form>
  </CardContent></Card>;
}

export function DomicileForm({ busy, save }: { busy: boolean; save: (address: string) => Promise<boolean> }) {
  const id = useId();
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<z.input<typeof domicileSchema>, unknown, z.output<typeof domicileSchema>>({ resolver: zodResolver(domicileSchema), defaultValues: { display_address: '' } });
  return <form noValidate className="space-y-4" onSubmit={handleSubmit(async values => { if (await save(values.display_address)) reset(); })}>
    <Field id={id} label="Domicilio nuevo" error={errors.display_address?.message}><Input {...register('display_address')} {...feedback(id, errors.display_address?.message)} required maxLength={300} disabled={busy || isSubmitting} /></Field>
    <Button disabled={busy || isSubmitting}>Registrar domicilio</Button>
  </form>;
}

export function CutForm({ cut, busy, save, cancel }: { cut: Cut | null; busy: boolean; save: (input: CutInput) => Promise<void>; cancel: () => void }) {
  const id = useId();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<z.input<typeof cutSchema>, unknown, z.output<typeof cutSchema>>({
    resolver: zodResolver(cut?.status === 'closed' ? closedCutSchema : cutSchema),
    defaultValues: { start_at: cut ? minuteInput(cut.start_at) : '', end_at: cut?.end_at ? minuteInput(cut.end_at) : '', observations: cut?.observations ?? '', complaint_number: cut?.complaint_number ?? '' },
  });
  const disabled = busy || isSubmitting;
  return <Card><CardHeader><CardTitle>{cut ? 'Corregir corte' : 'Registrar corte'}</CardTitle></CardHeader><CardContent>
    <form noValidate aria-label={cut ? 'Corregir corte' : 'Registrar corte'} className="space-y-4" onSubmit={handleSubmit(save)}>
      <div className="grid gap-4 md:grid-cols-2">
        <Field id={`${id}-start`} label="Inicio" error={errors.start_at?.message}><Input {...register('start_at')} {...feedback(`${id}-start`, errors.start_at?.message)} type="datetime-local" step="60" min="1970-01-01T00:00" required disabled={disabled} /></Field>
        <Field id={`${id}-end`} label="Fin (opcional si está en curso)" error={errors.end_at?.message}><Input {...register('end_at')} {...feedback(`${id}-end`, errors.end_at?.message)} type="datetime-local" step="60" min="1970-01-01T00:00" required={cut?.status === 'closed'} disabled={disabled} /></Field>
      </div>
      <Field id={`${id}-notes`} label="Observaciones" error={errors.observations?.message}><Textarea {...register('observations')} {...feedback(`${id}-notes`, errors.observations?.message)} maxLength={4000} disabled={disabled} /></Field>
      <Field id={`${id}-claim`} label="Número de reclamo" error={errors.complaint_number?.message}><Input {...register('complaint_number')} {...feedback(`${id}-claim`, errors.complaint_number?.message)} maxLength={120} disabled={disabled} /></Field>
      <div className={actions}><Button disabled={disabled}>{cut ? 'Guardar corrección' : 'Guardar corte'}</Button>{cut && <Button type="button" variant="outline" disabled={disabled} onClick={cancel}>Cancelar corrección</Button>}</div>
    </form>
  </CardContent></Card>;
}

export function CloseForm({ cut, busy, save, cancel }: { cut: Cut; busy: boolean; save: (end: string) => Promise<void>; cancel: () => void }) {
  const id = useId();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<z.input<typeof closeSchema>, unknown, z.output<typeof closeSchema>>({ resolver: zodResolver(closeSchema), defaultValues: { end_at: '' } });
  const disabled = busy || isSubmitting;
  return <Card><CardContent><form noValidate aria-label="Cerrar corte" className="space-y-4" onSubmit={handleSubmit(values => save(values.end_at))}>
    <h3 className="text-lg font-semibold">Cerrar corte de {displayTimestamp(cut.start_at)}</h3>
    <Field id={id} label="Fecha de cierre" error={errors.end_at?.message}><Input {...register('end_at')} {...feedback(id, errors.end_at?.message)} type="datetime-local" step="60" min="1970-01-01T00:00" required disabled={disabled} /></Field>
    <div className={actions}><Button disabled={disabled}>Confirmar cierre</Button><Button type="button" variant="outline" disabled={disabled} onClick={cancel}>Cancelar cierre</Button></div>
  </form></CardContent></Card>;
}

export function PeriodForm({ busy, query, changed }: { busy: boolean; query: (period: Period) => Promise<void>; changed: () => void }) {
  const id = useId();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<z.input<typeof periodSchema>, unknown, z.output<typeof periodSchema>>({ resolver: zodResolver(periodSchema), defaultValues: defaultPeriod() });
  const disabled = busy || isSubmitting;
  return <form noValidate aria-label="Consultar período" className="space-y-4" onChange={changed} onSubmit={handleSubmit(query)}>
    <div className="grid gap-4 md:grid-cols-2">
      <Field id={`${id}-from`} label="Desde" error={errors.period_start?.message}><Input {...register('period_start')} {...feedback(`${id}-from`, errors.period_start?.message)} type="datetime-local" step="60" min="1970-01-01T00:00" required disabled={disabled} /></Field>
      <Field id={`${id}-to`} label="Hasta" error={errors.period_end?.message}><Input {...register('period_end')} {...feedback(`${id}-to`, errors.period_end?.message)} type="datetime-local" step="60" min="1970-01-01T00:00" required disabled={disabled} /></Field>
    </div>
    <Button disabled={disabled}>Consultar resumen</Button>
  </form>;
}
