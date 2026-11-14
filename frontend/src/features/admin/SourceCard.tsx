// Presentational CU10 source card. State, handlers and requests stay in AdminPanel.
import { Alert } from '../../components/ui/alert.tsx';
import { Button } from '../../components/ui/button.tsx';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card.tsx';
import { Label } from '../../components/ui/label.tsx';
import { formatInstant } from '../outages/state.ts';
import type { IntervalSeconds, SourceStatus } from './api.ts';
import {
  INTERVAL_OPTIONS, intervalLabel, isSuccessOutcome, outcomeLabel, sourceTitle,
} from './state.ts';

const SELECT_CLASS = 'min-h-10 w-full min-w-0 rounded-md border border-input bg-card px-3 text-base shadow-xs outline-none transition-colors focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50';

type Tone = 'attention' | 'neutral' | 'critical';

const TONES: Record<Tone, string> = {
  attention: 'border-primary/30 bg-accent text-accent-foreground',
  neutral: 'border-border bg-muted text-foreground',
  critical: 'border-destructive/40 bg-card text-destructive',
};

function chip(tone: Tone): string {
  return `inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${TONES[tone]}`;
}

export interface BusyState { retry: boolean; save: boolean }
export interface Feedback {
  kind: 'success' | 'warning' | 'error';
  action: 'retry' | 'save';
  text: string;
}

export interface SourceCardProps {
  source: SourceStatus;
  selected: IntervalSeconds | '';
  busy: BusyState;
  feedback: Feedback | null;
  onSelect: (value: string) => void;
  onSave: () => void;
  onRetry: () => void;
}

function attemptTone(source: SourceStatus): Tone {
  if (source.last_attempt_outcome === null) return 'neutral';
  return isSuccessOutcome(source.last_attempt_outcome) ? 'attention' : 'critical';
}

function attemptLabel(source: SourceStatus): string {
  if (source.last_attempt_outcome === null) return 'Sin intentos';
  return isSuccessOutcome(source.last_attempt_outcome) ? 'Último intento exitoso' : 'Último intento con error';
}

function FeedbackNote({ feedback }: { feedback: Feedback | null }) {
  if (!feedback) return null;
  if (feedback.kind === 'success') {
    return <p role="status" className="text-sm">{feedback.text}</p>;
  }
  if (feedback.kind === 'warning') {
    return <Alert role="status" className="border-primary/30 bg-accent text-accent-foreground">
      {feedback.text}
    </Alert>;
  }
  return <Alert>{feedback.text}</Alert>;
}

export function SourceCard({
  source, selected, busy, feedback, onSelect, onSave, onRetry,
}: SourceCardProps) {
  const changed = selected !== '' && selected !== source.interval_seconds;
  return <Card>
    <CardHeader>
      <CardTitle>{sourceTitle(source.key)}</CardTitle>
      <p className="text-sm text-muted-foreground">
        Actualización automática: {source.scheduler_enabled ? 'habilitada' : 'deshabilitada'}
        {' '}(configuración, no garantiza que el proceso esté ejecutándose)
      </p>
      <p className="flex flex-wrap items-center gap-2 pt-1">
        <span className={chip('neutral')}>
          {source.scheduler_enabled
            ? 'Actualización automática habilitada'
            : 'Actualización automática deshabilitada'}
        </span>
        <span className={chip(attemptTone(source))}>{attemptLabel(source)}</span>
      </p>
    </CardHeader>
    <CardContent className="space-y-5">
      <section aria-labelledby={`source-state-${source.key}`} className="space-y-3">
        <h3 id={`source-state-${source.key}`} className="text-sm font-semibold">Estado</h3>
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div className="min-w-0 rounded-lg border border-border bg-muted px-3 py-2">
            <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Último intento</dt>
            <dd className="mt-1 break-words">
              {formatInstant(source.last_attempt_at ?? undefined) || 'Sin intentos registrados'}
            </dd>
          </div>
          <div className="min-w-0 rounded-lg border border-border bg-muted px-3 py-2">
            <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Resultado</dt>
            <dd className="mt-1 break-words">{outcomeLabel(source.last_attempt_outcome)}</dd>
          </div>
          <div className="min-w-0 rounded-lg border border-border bg-muted px-3 py-2">
            <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
              Última actualización exitosa
            </dt>
            <dd className="mt-1 break-words">
              {formatInstant(source.last_success_at ?? undefined) || 'Sin actualización exitosa registrada'}
            </dd>
          </div>
          <div className="min-w-0 rounded-lg border border-border bg-muted px-3 py-2">
            <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Intervalo actual</dt>
            <dd className="mt-1 break-words">{intervalLabel(source.interval_seconds)}</dd>
          </div>
        </dl>

        {source.last_attempt_error && <Alert>Último error: {source.last_attempt_error}</Alert>}
        {source.last_skipped_locked_at && <p className="text-sm text-muted-foreground">
          Última ejecución omitida por bloqueo: {formatInstant(source.last_skipped_locked_at ?? undefined)}
        </p>}
      </section>

      <section aria-labelledby={`source-config-${source.key}`} className="space-y-3 border-t border-border pt-4">
        <h3 id={`source-config-${source.key}`} className="text-sm font-semibold">Configuración</h3>
        <div className="space-y-2">
          <Label htmlFor={`interval-${source.key}`}>Intervalo de actualización</Label>
          <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
            <select id={`interval-${source.key}`} className={SELECT_CLASS}
              aria-describedby={`interval-help-${source.key}`}
              value={selected} onChange={event => onSelect(event.target.value)}>
              {selected === '' && <option value="">Elegí un intervalo</option>}
              {INTERVAL_OPTIONS.map(option => <option key={option.value} value={option.value}>
                {option.label}
              </option>)}
            </select>
            <Button type="button" variant="secondary" className="min-h-11 w-full sm:w-auto"
              disabled={busy.save || !changed} onClick={onSave}
              aria-label={`Guardar intervalo — ${sourceTitle(source.key)}`}>
              {busy.save ? 'Guardando…' : 'Guardar intervalo'}
            </Button>
          </div>
          <p id={`interval-help-${source.key}`} className="text-sm text-muted-foreground">
            Valores permitidos: 5, 10, 15, 30 y 60 minutos.
          </p>
        </div>
        <FeedbackNote feedback={feedback?.action === 'save' ? feedback : null} />
      </section>

      <section aria-labelledby={`source-actions-${source.key}`} className="space-y-3 border-t border-border pt-4">
        <h3 id={`source-actions-${source.key}`} className="text-sm font-semibold">Acciones</h3>
        <Button type="button" className="min-h-11 w-full sm:w-auto" disabled={busy.retry} onClick={onRetry}
          aria-label={`Actualizar ahora — ${sourceTitle(source.key)}`}>
          {busy.retry ? 'Actualizando…' : 'Actualizar ahora'}
        </Button>
        <FeedbackNote feedback={feedback?.action === 'retry' ? feedback : null} />
      </section>
    </CardContent>
  </Card>;
}
