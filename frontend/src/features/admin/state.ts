import type { IntervalSeconds, SourceKey } from './api.ts';

export const INTERVAL_OPTIONS: readonly { value: IntervalSeconds; label: string }[] = [
  { value: 300, label: '5 minutos' },
  { value: 600, label: '10 minutos' },
  { value: 900, label: '15 minutos' },
  { value: 1800, label: '30 minutos' },
  { value: 3600, label: '60 minutos' },
];

const INTERVAL_LABELS: Record<IntervalSeconds, string> = {
  300: '5 minutos',
  600: '10 minutos',
  900: '15 minutos',
  1800: '30 minutos',
  3600: '60 minutos',
};

const OUTCOME_LABELS: Record<string, string> = {
  ok: 'Actualización exitosa',
  not_modified: 'Sin cambios',
  http_error: 'Error HTTP',
  tls_error: 'Error TLS',
  parse_error: 'Error de formato',
  schema_error: 'Esquema inesperado',
  source_degraded: 'Fuente degradada',
  timeout: 'Tiempo de espera agotado',
};

export function intervalLabel(seconds: IntervalSeconds): string {
  return INTERVAL_LABELS[seconds];
}

export function sourceTitle(key: SourceKey): string {
  return key === 'outages' ? 'ENRE — Cortes actuales' : 'ENRE — Trabajos programados';
}

export function outcomeLabel(outcome: string | null): string {
  if (outcome === null) return 'Sin intentos registrados';
  return OUTCOME_LABELS[outcome] ?? outcome;
}

export function isSuccessOutcome(outcome: string): boolean {
  return outcome === 'ok' || outcome === 'not_modified';
}
