// Presentational CU02 result. Behaviour, validation and data come from the panel
// and the validated API result; labels/formatting are reused from state.ts.
import { Alert } from '../../components/ui/alert.tsx';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card.tsx';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table.tsx';
import type { CoverageStatus, Freshness, ScheduledWork, ScheduledWorksResult } from './api.ts';
import {
  coverageLabel, formatInstant, formatReportedTime, freshnessLabel, limitationMessage,
  reasonText, restorationText, stateDetail, stateHeading,
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

function zoneLabel(work: ScheduledWork): string {
  return work.localidad ? `${work.partido} · ${work.localidad}` : work.partido;
}

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

function freshnessTone(result: ScheduledWorksResult): Tone {
  if (result.source_status === 'degraded') return 'critical';
  return FRESHNESS_TONES[result.freshness];
}

function queriedZone(result: ScheduledWorksResult): string {
  const localidad = result.coverage.localidad;
  return localidad ? `${result.coverage.partido} · ${localidad}` : result.coverage.partido;
}

// The accepted CU02 contract fixes planned instants to null. This helper keeps the
// presentation honest if a future source ever publishes one without inventing a value.
function plannedText(values: readonly (string | null | undefined)[]): string {
  const present = Array.from(new Set(values.filter((value): value is string => Boolean(value))));
  if (present.length === 0) return 'No publicado';
  if (present.length > 1) return 'Informado por trabajo';
  return formatInstant(present[0]) || 'No publicado';
}

export function ScheduledWorksResultCard({ result }: { result: ScheduledWorksResult }) {
  const works = result.works ?? [];
  const plannedStart = plannedText(works.map(work => work.planned_start_at));
  const plannedEnd = plannedText(works.map(work => work.planned_end_at));

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
      <p className="max-w-3xl text-sm sm:text-base">{stateDetail(result.state)}</p>

      {result.source_status === 'degraded' && <Alert>
        La última sincronización de trabajos no fue exitosa. Se muestran los últimos datos válidos.
      </Alert>}
      {result.freshness !== 'fresh' && <Alert>
        {freshnessLabel(result.freshness)}: {stateDetail(result.freshness === 'stale' ? 'stale' : 'unavailable')}
      </Alert>}
      {result.limitations.includes('dates_not_published') &&
        <Alert className="border-primary/30 bg-accent text-accent-foreground">
          {limitationMessage('dates_not_published')}
        </Alert>}
      {result.limitations.includes('announced_works_not_displayed') &&
        <Alert className="border-primary/30 bg-accent text-accent-foreground">
          {limitationMessage('announced_works_not_displayed')}
        </Alert>}
      {result.limitations.includes('proximity_not_available') && <p className="text-sm text-muted-foreground">
        {limitationMessage('proximity_not_available')}
      </p>}

      <section aria-labelledby="scheduled-scope" className="space-y-3 rounded-lg border border-border p-4">
        <h3 id="scheduled-scope" className="text-sm font-semibold">Zona y alcance de los datos</h3>
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div className="min-w-0 space-y-1">
            <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
              Zona consultada
            </dt>
            <dd className="break-words">{queriedZone(result)}</dd>
          </div>
          <div className="min-w-0 space-y-1">
            <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
              Granularidad
            </dt>
            <dd>{result.granularity === 'localidad' ? 'Localidad' : 'Partido'}</dd>
          </div>
          {works.length > 0 && <>
            <div className="min-w-0 space-y-1">
              <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                Inicio planificado
              </dt>
              <dd>{plannedStart}</dd>
            </div>
            <div className="min-w-0 space-y-1">
              <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                Fin planificado
              </dt>
              <dd>{plannedEnd}</dd>
            </div>
          </>}
        </dl>
        {works.length > 0 && <p className="text-xs text-muted-foreground">
          El ENRE no publica una agenda con fechas de inicio y fin. El motivo se muestra
          por trabajo cuando la fuente lo informa.
        </p>}
      </section>

      {works.length > 0 && <div className="space-y-3">
        <h3 className="text-sm font-semibold">Listado de trabajos</h3>
        <p className="text-xs text-muted-foreground sm:hidden">
          Desplazá horizontalmente la tabla para ver todas las columnas.
        </p>
        <Table className="min-w-[44rem]">
          <TableHeader><TableRow>
            <TableHead scope="col">Zona</TableHead>
            <TableHead scope="col">Alimentador</TableHead>
            <TableHead scope="col">Usuarios afectados</TableHead>
            <TableHead scope="col">Normalización estimada</TableHead>
            <TableHead scope="col">Motivo</TableHead>
          </TableRow></TableHeader>
          <TableBody>
            {works.map((work, index) => <TableRow key={`${work.partido}-${work.localidad ?? ''}-${index}`}>
              <TableCell>{zoneLabel(work)}</TableCell>
              <TableCell>{work.subestacion_alimentador ?? 'Sin dato'}</TableCell>
              <TableCell>{optionalNumber(work.affected_users)}</TableCell>
              <TableCell>{restorationText(work)}</TableCell>
              <TableCell>{reasonText(work)}</TableCell>
            </TableRow>)}
          </TableBody>
        </Table>
        <p className="text-sm text-muted-foreground">
          La normalización estimada es el texto publicado por el ENRE. No es una fecha de fin
          programada y puede no estar informada.
        </p>
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
