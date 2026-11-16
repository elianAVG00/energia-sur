import { useEffect, useId, useState } from 'react';
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
import { loginSchema, registrationSchema, domicileSchema, cutSchema, closedCutSchema, closeSchema, periodSchema } from './schemas.ts';
import { duplicateAddress } from '../domiciles/schemas.ts';
import { DiaryError, errorMessage } from '../../diaryApi.ts';

function Field({ id, label, error, children }: { id: string; label: string; error: string | undefined; children: ReactNode }) {
  return <div className="space-y-2"><Label htmlFor={id}>{label}</Label>{children}{error && <p id={`${id}-error`} role="alert" className="text-sm text-destructive">{error}</p>}</div>;
}
function feedback(id: string, error: string | undefined) {
  return { id, 'aria-invalid': Boolean(error), 'aria-describedby': error ? `${id}-error` : undefined };
}
const actions = 'flex flex-wrap gap-3';

export function RegisterForm({ pending, username, onUsernameChange, registerAccount, onSuccess }: {
  pending: boolean;
  username: string;
  onUsernameChange: (username: string) => void;
  registerAccount: (values: z.output<typeof registrationSchema>) => Promise<void>;
  onSuccess: (username: string) => void;
}) {
  const id = useId();
  const [serverError, setServerError] = useState('');
  const { register, handleSubmit, resetField, formState: { errors, isSubmitting } } = useForm<z.input<typeof registrationSchema>, unknown, z.output<typeof registrationSchema>>({
    resolver: zodResolver(registrationSchema),
    defaultValues: { username, password: '', confirmPassword: '' },
    shouldUnregister: true,
  });
  useEffect(() => () => {
    resetField('password', { defaultValue: '' });
    resetField('confirmPassword', { defaultValue: '' });
  }, [resetField]);
  const disabled = pending || isSubmitting;
  async function submit(values: z.output<typeof registrationSchema>) {
    setServerError('');
    try {
      await registerAccount(values);
      onUsernameChange(values.username);
      onSuccess(values.username);
    } catch (reason: unknown) {
      if (reason instanceof DiaryError && reason.status === 409) {
        setServerError('Ese usuario ya está registrado. Elegí otro o ingresá con tu cuenta.');
      } else if (reason instanceof DiaryError && reason.status === 429) {
        setServerError(reason.retryAfter
          ? `Se alcanzó el límite de registros. Esperá ${reason.retryAfter} segundos e intentá nuevamente.`
          : 'Se alcanzó el límite de registros. Esperá un momento e intentá nuevamente.');
      } else {
        setServerError(errorMessage(reason));
      }
    } finally {
      resetField('password', { defaultValue: '' });
      resetField('confirmPassword', { defaultValue: '' });
    }
  }
  return <Card><CardHeader><CardTitle>Crear cuenta</CardTitle></CardHeader><CardContent>
    <form noValidate aria-label="Crear cuenta" className="max-w-lg space-y-4" onSubmit={handleSubmit(submit, () => {
      resetField('password', { defaultValue: '' });
      resetField('confirmPassword', { defaultValue: '' });
    })}>
      <Field id={`${id}-username`} label="Usuario" error={errors.username?.message}>
        <Input {...register('username', { onChange: event => onUsernameChange(event.target.value) })} {...feedback(`${id}-username`, errors.username?.message)} required autoComplete="username" maxLength={32} disabled={disabled} />
      </Field>
      <Field id={`${id}-password`} label="Contraseña" error={errors.password?.message}>
        <Input {...register('password')} {...feedback(`${id}-password`, errors.password?.message)} type="password" required autoComplete="new-password" maxLength={128} disabled={disabled} />
      </Field>
      <Field id={`${id}-confirmation`} label="Confirmar contraseña" error={errors.confirmPassword?.message}>
        <Input {...register('confirmPassword')} {...feedback(`${id}-confirmation`, errors.confirmPassword?.message)} type="password" required autoComplete="new-password" maxLength={128} disabled={disabled} />
      </Field>
      {serverError && <p role="alert" className="text-sm text-destructive">{serverError}</p>}
      <Button disabled={disabled}>Crear cuenta</Button>
    </form>
  </CardContent></Card>;
}

export function LoginForm({ pending, login, registerAccount, registrationComplete }: {
  pending: boolean;
  login: (values: z.output<typeof loginSchema>) => Promise<void>;
  registerAccount: (values: z.output<typeof registrationSchema>) => Promise<void>;
  registrationComplete?: string;
}) {
  const id = useId();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const { register, handleSubmit, reset, resetField, formState: { errors, isSubmitting } } = useForm<z.input<typeof loginSchema>, unknown, z.output<typeof loginSchema>>({ resolver: zodResolver(loginSchema), defaultValues: { username, password: '' }, shouldUnregister: true });
  useEffect(() => () => resetField('password', { defaultValue: '' }), [resetField]);
  const disabled = pending || isSubmitting;
  return <section aria-label="Acceso a la cuenta" className="space-y-4">
    <div className={actions} role="group" aria-label="Elegir acceso">
      <Button type="button" aria-label="Ingresar (cambiar formulario)" variant={mode === 'login' ? 'default' : 'outline'} aria-pressed={mode === 'login'} onClick={() => setMode('login')}>Ingresar</Button>
      <Button type="button" aria-label="Crear cuenta (cambiar formulario)" variant={mode === 'register' ? 'default' : 'outline'} aria-pressed={mode === 'register'} onClick={() => setMode('register')}>Crear cuenta</Button>
    </div>
    {registrationComplete && mode === 'login' && <p role="status">La cuenta se creó correctamente. Ingresá con tu usuario y contraseña.</p>}
    {mode === 'register' ? <RegisterForm pending={pending} username={username} onUsernameChange={setUsername}
      registerAccount={registerAccount} onSuccess={name => {
        setUsername(name);
        reset({ username: name, password: '' });
        setMode('login');
      }} /> :
      <Card><CardHeader><CardTitle>Ingresar</CardTitle></CardHeader><CardContent>
        <form noValidate aria-label="Ingresar" className="max-w-lg space-y-4" onSubmit={handleSubmit(async values => {
          try { await login(values); } finally { resetField('password', { defaultValue: '' }); }
        }, () => resetField('password', { defaultValue: '' }))}>
          <Field id={`${id}-username`} label="Usuario" error={errors.username?.message}><Input {...register('username', { onChange: event => setUsername(event.target.value) })} value={username} {...feedback(`${id}-username`, errors.username?.message)} required autoComplete="username" maxLength={80} disabled={disabled} /></Field>
          <Field id={`${id}-password`} label="Contraseña" error={errors.password?.message}><Input {...register('password')} {...feedback(`${id}-password`, errors.password?.message)} type="password" required autoComplete="current-password" maxLength={1024} disabled={disabled} /></Field>
          <Button disabled={disabled}>Ingresar</Button>
        </form>
      </CardContent></Card>}
  </section>;
}

export function DomicileForm({ busy, save, addresses }: { busy: boolean; save: (address: string) => Promise<boolean>; addresses: { id: string; display_address: string }[] }) {
  const id = useId();
  const { register, handleSubmit, reset, watch, formState: { errors, isSubmitting } } = useForm<z.input<typeof domicileSchema>, unknown, z.output<typeof domicileSchema>>({ resolver: zodResolver(domicileSchema), defaultValues: { display_address: '' } });
  const address = watch('display_address').trim();
  return <form noValidate className="space-y-4" onSubmit={handleSubmit(async values => { if (await save(values.display_address)) reset(); })}>
    <Field id={id} label="Domicilio nuevo" error={errors.display_address?.message}><Input {...register('display_address')} {...feedback(id, errors.display_address?.message)} required maxLength={300} disabled={busy || isSubmitting} /></Field>
    {duplicateAddress(address, addresses) && <p role="status">Ya existe un domicilio con esta dirección. Podés registrarlo igualmente.</p>}
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
  return <form noValidate aria-label={cut ? 'Corregir corte' : 'Registrar corte'} className="space-y-4" onSubmit={handleSubmit(save)}>
      <div className="grid gap-4 md:grid-cols-2">
        <Field id={`${id}-start`} label="Inicio" error={errors.start_at?.message}><Input {...register('start_at')} {...feedback(`${id}-start`, errors.start_at?.message)} type="datetime-local" step="60" min="1970-01-01T00:00" required disabled={disabled} /></Field>
        <Field id={`${id}-end`} label="Fin (opcional si está en curso)" error={errors.end_at?.message}><Input {...register('end_at')} {...feedback(`${id}-end`, errors.end_at?.message)} type="datetime-local" step="60" min="1970-01-01T00:00" required={cut?.status === 'closed'} disabled={disabled} /></Field>
      </div>
      <Field id={`${id}-notes`} label="Observaciones" error={errors.observations?.message}><Textarea {...register('observations')} {...feedback(`${id}-notes`, errors.observations?.message)} maxLength={4000} disabled={disabled} /></Field>
      <Field id={`${id}-claim`} label="Número de reclamo" error={errors.complaint_number?.message}><Input {...register('complaint_number')} {...feedback(`${id}-claim`, errors.complaint_number?.message)} maxLength={120} disabled={disabled} /></Field>
      <div className={actions}><Button disabled={disabled}>{cut ? 'Guardar corrección' : 'Guardar corte'}</Button>{cut && <Button type="button" variant="outline" disabled={disabled} onClick={cancel}>Cancelar corrección</Button>}</div>
    </form>;
}

export function CloseForm({ cut, busy, save, cancel }: { cut: Cut; busy: boolean; save: (end: string) => Promise<void>; cancel: () => void }) {
  const id = useId();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<z.input<typeof closeSchema>, unknown, z.output<typeof closeSchema>>({ resolver: zodResolver(closeSchema), defaultValues: { end_at: '' } });
  const disabled = busy || isSubmitting;
  return <form noValidate aria-label="Cerrar corte" className="space-y-4" onSubmit={handleSubmit(values => save(values.end_at))}>
    <h3 className="text-lg font-semibold">Cerrar corte de {displayTimestamp(cut.start_at)}</h3>
    <Field id={id} label="Fecha de cierre" error={errors.end_at?.message}><Input {...register('end_at')} {...feedback(id, errors.end_at?.message)} type="datetime-local" step="60" min="1970-01-01T00:00" required disabled={disabled} /></Field>
    <div className={actions}><Button disabled={disabled}>Confirmar cierre</Button><Button type="button" variant="outline" disabled={disabled} onClick={cancel}>Cancelar cierre</Button></div>
  </form>;
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
