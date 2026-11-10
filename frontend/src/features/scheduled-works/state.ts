import type {
  CoverageStatus, Freshness, Limitation, ScheduledState, ScheduledWork,
} from './api.ts';

const COVERAGE_LABELS: Record<CoverageStatus, string> = {
  covered: 'Cobertura verificada',
  out_of_coverage: 'Fuera de cobertura',
  coverage_unverified: 'Cobertura no verificada',
};

const FRESHNESS_LABELS: Record<Freshness, string> = {
  fresh: 'Información actualizada',
  stale: 'Información desactualizada',
  unavailable: 'Fuente no disponible',
};

const LIMITATION_MESSAGES: Record<Limitation, string> = {
  dates_not_published: 'El ENRE no publica fecha de inicio ni de fin para estos trabajos.',
  reason_not_published: 'El ENRE no publica un motivo para estos trabajos.',
  proximity_not_available: 'No se muestra cercanía porque la fuente no publica coordenadas.',
  announced_works_not_displayed:
    'Hay trabajos anunciados por comunicado que esta versión no muestra.',
};

export function coverageLabel(status: CoverageStatus): string {
  return COVERAGE_LABELS[status];
}

export function freshnessLabel(value: Freshness): string {
  return FRESHNESS_LABELS[value];
}

export function limitationMessage(value: Limitation): string {
  return LIMITATION_MESSAGES[value];
}

export function stateHeading(state: ScheduledState): string {
  switch (state) {
    case 'works_reported': return 'Trabajos informados';
    case 'no_works': return 'Sin trabajos informados';
    case 'stale': return 'Información desactualizada';
    case 'unavailable': return 'Fuente no disponible';
    case 'coverage_unverified': return 'Cobertura no verificada';
    case 'out_of_coverage': return 'Zona fuera de cobertura';
  }
}

export function stateDetail(state: ScheduledState): string {
  switch (state) {
    case 'works_reported':
      return 'Estos son los trabajos de mantenimiento informados por el ENRE para la zona. No son una agenda de trabajos futuros.';
    case 'no_works':
      return 'No hay trabajos de mantenimiento informados para esta zona en la última actualización. El ENRE no publica una agenda de fechas futuras.';
    case 'stale':
      return 'La última actualización tiene más de 15 minutos. Los datos pueden no reflejar la situación actual.';
    case 'unavailable':
      return 'No hay una actualización válida reciente. No podemos confirmar trabajos ni ausencia de trabajos.';
    case 'coverage_unverified':
      return 'No tenemos cobertura territorial verificada para esta zona. No podemos confirmar si hay trabajos ni afirmar que no los hay.';
    case 'out_of_coverage':
      return 'El catálogo territorial indica que esta zona está fuera del área consultada.';
  }
}

export function reasonText(work: ScheduledWork): string {
  return work.reason_text ?? 'No publicado por la fuente';
}

export function restorationText(work: ScheduledWork): string {
  return work.restoration_estimate_text ?? 'No publicado por la fuente';
}

function parts(value: string): Record<string, string> {
  const result: Record<string, string> = {};
  for (const part of new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Argentina/Buenos_Aires', year: 'numeric', month: '2-digit',
    day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(new Date(value))) {
    result[part.type] = part.value;
  }
  return result;
}

export function formatInstant(value: string | undefined): string {
  if (!value) return '';
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) return '';
  const field = parts(value);
  return `${field.day}/${field.month}/${field.year} ${field.hour}:${field.minute}`;
}

export function formatReportedTime(value: string | undefined): string {
  if (!value || value === '--:--') return '';
  return `${value} hs`;
}

export function retryAfterMessage(seconds: number | null): string {
  if (seconds === null || seconds <= 0) {
    return 'Demasiadas solicitudes. Esperá un momento e intentá nuevamente.';
  }
  return `Demasiadas solicitudes. Reintentá en ${seconds} segundos.`;
}
