// Presentational CU01 result. Behaviour, validation and data come from the panel
// and the validated API result; labels/formatting are reused from state.ts.
import { Alert } from '../../components/ui/alert.tsx';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card.tsx';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table.tsx';
import type { CoverageStatus, Freshness, OutagesResult } from './api.ts';
import {
  categoryLabel, coverageLabel, formatInstant, formatReportedTime, freshnessLabel,
  stateDetail, stateHeading,
} from './state.ts';

type Tone = 'attention' | 'neutral' | 'critical';

const TONES: Record<Tone, string> = {
  attention: 'border-primary/30 bg-accent text-accent-foreground',
  neutral: 'border-border bg-muted text-foreground',
  critical: 'border-destructive/40 bg-card text-destructive',
};

function chip(tone: Tone): string {
  return `inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${TONES[tone]}`;
}

function optionalNumber(value: number | null | undefined): string {
  return value === undefined || value === null ? 'Sin dato' : String(value);
}

function coverageNote(result: OutagesResult): string | null {
  if (result.coverage.status === 'coverage_unverified' && (result.outages?.length ?? 0) > 0) {
    return 'La cobertura de esta zona no está verificada. Los cortes listados son los reportados por el ENRE.';
  }
  return null;
}

// "attention" is never a success/green signal: it only marks a verified dimension.
// An unknown or unverified coverage stays neutral so it cannot read as "no outages".
function coverageTone(status: CoverageStatus): Tone {
  if (status === 'covered') return 'attention';
  if (status === 'out_of_coverage') return 'critical';
  return 'neutral';
}

const FRESHNESS_TONES: Record<Freshness, Tone> = {
  fresh: 'attention',
  stale: 'neutral',
  unavailable: 'critical',
};

function freshnessTone(result: OutagesResult): Tone {
  if (result.source_status === 'degraded') return 'critical';
  return FRESHNESS_TONES[result.freshness];
}

export function OutagesResultCard({ result }: { result: OutagesResult }) {
  const note = coverageNote(result);
  const outages = result.outages ?? [];

  return <Card aria-live="polite">
    <CardHeader>
      <CardTitle>{stateHeading(result.state)}</CardTitle>
      <p className="flex flex-wrap items-center gap-2">
        <span className={chip('neutral')}>
          {result.granularity === 'localidad' ? 'Resultado por localidad' : 'Resultado por partido'}
        </span>
        <span className={chip(coverageTone(result.coverage.status))}>
          {coverageLabel(result.coverage.status)}
        </span>
        <span className={chip(freshnessTone(result))}>
          {result.source_status === 'degraded' ? 'Fuente degradada' : freshnessLabel(result.freshness)}
        </span>
      </p>
    </CardHeader>
    <CardContent className="space-y-5">
      <p className="max-w-3xl text-sm sm:text-base">
        {result.source_status === 'degraded' && result.state === 'unavailable'
          ? 'El ENRE informó que no está actualizando la información. No podemos confirmar cortes ni ausencia de cortes.'
          : stateDetail(result.state)}
      </p>

      {result.source_status === 'degraded' && <Alert>
        El ENRE informó que no está actualizando la información. Se muestran los últimos datos válidos.
      </Alert>}
      {result.freshness !== 'fresh' && <Alert>
        {freshnessLabel(result.freshness)}: {stateDetail(result.freshness === 'stale' ? 'stale' : 'unavailable')}
      </Alert>}
      {note !== null && <Alert>{note}</Alert>}

      <section aria-label="Totales oficiales" className="space-y-3 rounded-lg border border-border p-4">
        <div className="space-y-1">
          <h3 className="text-sm font-semibold">Total Edesur (todos los partidos, no la zona consultada)</h3>
          <p className="text-sm text-muted-foreground">
            Los totales corresponden a Edesur en general y no necesariamente a la zona consultada.
          </p>
        </div>
        <dl className="grid gap-3 sm:grid-cols-3">
          <div className="min-w-0 rounded-lg border border-border bg-muted px-4 py-3">
            <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Sin suministro</dt>
            <dd className="mt-1 text-2xl font-semibold tabular-nums">{optionalNumber(result.total_users_without)}</dd>
            <dd className="text-xs text-muted-foreground">usuarios</dd>
          </div>
          <div className="min-w-0 rounded-lg border border-border bg-muted px-4 py-3">
            <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Con suministro</dt>
            <dd className="mt-1 text-2xl font-semibold tabular-nums">{optionalNumber(result.total_users_with)}</dd>
            <dd className="text-xs text-muted-foreground">usuarios</dd>
          </div>
          <div className="min-w-0 rounded-lg border border-border bg-muted px-4 py-3">
            <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Afectados el día anterior</dt>
            <dd className="mt-1 text-2xl font-semibold tabular-nums">{optionalNumber(result.users_affected_yesterday)}</dd>
            <dd className="text-xs text-muted-foreground">usuarios</dd>
          </div>
        </dl>
      </section>

      {outages.length > 0 && <div className="space-y-3">
        <h3 className="text-sm font-semibold">Detalle de cortes informados</h3>
        <p className="text-xs text-muted-foreground sm:hidden">
          Desplazá horizontalmente la tabla para ver todas las columnas.
        </p>
        <Table className="min-w-[44rem]">
          <TableHeader><TableRow>
            <TableHead scope="col">Categoría</TableHead><TableHead scope="col">Zona</TableHead>
            <TableHead scope="col">Alimentador</TableHead><TableHead scope="col">Usuarios afectados</TableHead>
            <TableHead scope="col">Normalización</TableHead>
          </TableRow></TableHeader>
          <TableBody>
            {outages.map((outage, index) => <TableRow key={`${outage.category}-${outage.partido}-${outage.localidad ?? ''}-${index}`}>
              <TableCell>{categoryLabel(outage.category)}</TableCell>
              <TableCell>{outage.partido}{outage.localidad ? ` · ${outage.localidad}` : ''}</TableCell>
              <TableCell>{outage.subestacion_alimentador ?? 'Sin dato'}</TableCell>
              <TableCell>{outage.affected_users === null || outage.affected_users === undefined
                ? 'Sin dato' : String(outage.affected_users)}</TableCell>
              <TableCell>{outage.normalizacion ?? 'Sin datos'}</TableCell>
            </TableRow>)}
          </TableBody>
        </Table>
      </div>}

      <dl className="grid gap-4 rounded-lg border border-border bg-muted/40 p-4 text-sm sm:grid-cols-2">
        <div className="min-w-0 space-y-1">
          <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Fuente</dt>
          <dd className="break-words">
            <a className="font-medium text-primary underline underline-offset-2" href={result.source_url}
              target="_blank" rel="noreferrer">{result.source}</a>
          </dd>
        </div>
        <div className="min-w-0 space-y-1">
          <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            Última actualización de la fuente
          </dt>
          <dd>{formatInstant(result.source_updated_at) || 'No informada'}</dd>
        </div>
        <div className="min-w-0 space-y-1">
          <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Consultado</dt>
          <dd>{formatInstant(result.fetched_at) || 'No disponible'}</dd>
        </div>
        <div className="min-w-0 space-y-1">
          <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            Hora informada por la fuente
          </dt>
          <dd>{formatReportedTime(result.source_reported_time) || 'No informada'}</dd>
        </div>
      </dl>
    </CardContent>
  </Card>;
}
