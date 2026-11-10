import type { Category, CoverageStatus, Freshness, OutageState, OutagesResult } from './api.ts';

const CATEGORY_LABELS: Record<Category, string> = {
  medium_voltage: 'Media tensión',
  low_voltage: 'Baja tensión',
  preventive: 'Corte preventivo',
};

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

export function categoryLabel(category: Category): string {
  return CATEGORY_LABELS[category];
}

export function coverageLabel(status: CoverageStatus): string {
  return COVERAGE_LABELS[status];
}

export function freshnessLabel(value: Freshness): string {
  return FRESHNESS_LABELS[value];
}

export function stateHeading(state: OutageState): string {
  switch (state) {
    case 'reported': return 'Cortes reportados';
    case 'no_reports': return 'Sin cortes reportados';
    case 'stale': return 'Información desactualizada';
    case 'unavailable': return 'Fuente no disponible';
    case 'coverage_unverified': return 'Cobertura no verificada';
    case 'out_of_coverage': return 'Zona fuera de cobertura';
    case 'geographic_error': return 'No pudimos ubicar la zona';
  }
}

export function stateDetail(state: OutageState): string {
  switch (state) {
    case 'reported':
      return 'Estos son los cortes informados por el ENRE para la zona. No indican el estado de un domicilio en particular.';
    case 'no_reports':
      return 'No hay cortes reportados para esta zona en la última actualización. Esto no garantiza el suministro eléctrico.';
    case 'stale':
      return 'La última actualización tiene más de 15 minutos. Los datos pueden no reflejar la situación actual.';
    case 'unavailable':
      return 'No hay una actualización válida reciente. No podemos confirmar cortes ni ausencia de cortes.';
    case 'coverage_unverified':
      return 'No tenemos cobertura territorial verificada para esta zona. No podemos confirmar si hay cortes ni afirmar que no los hay.';
    case 'out_of_coverage':
      return 'El catálogo territorial indica que esta zona está fuera del área de cobertura consultada.';
    case 'geographic_error':
      return 'No pudimos resolver la ubicación con la información disponible. Probá con partido y localidad.';
  }
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

export function outageCount(result: OutagesResult): number {
  return result.outages?.length ?? 0;
}

export function retryAfterMessage(seconds: number | null): string {
  if (seconds === null || seconds <= 0) {
    return 'Demasiadas solicitudes. Esperá un momento e intentá nuevamente.';
  }
  return `Demasiadas solicitudes. Reintentá en ${seconds} segundos.`;
}
