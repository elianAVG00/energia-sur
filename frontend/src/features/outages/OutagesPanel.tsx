import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { Alert } from '../../components/ui/alert.tsx';
import { Button } from '../../components/ui/button.tsx';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card.tsx';
import { Label } from '../../components/ui/label.tsx';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table.tsx';
import { DiaryError, errorMessage } from '../../lib/httpError.ts';
import { useRequestScope } from '../../useRequestScope.ts';
import { outagesApi } from './api.ts';
import type { AreasResult, OutagesResult, ResolveZone } from './api.ts';
import {
  categoryLabel, coverageLabel, formatInstant, formatReportedTime, freshnessLabel,
  retryAfterMessage, stateDetail, stateHeading,
} from './state.ts';

function quiet(reason: unknown): boolean {
  return reason instanceof DiaryError && reason.kind === 'aborted';
}

function messageFor(reason: unknown): string {
  if (reason instanceof DiaryError && reason.status === 429) {
    return retryAfterMessage(reason.retryAfter);
  }
  return errorMessage(reason);
}

function optionalNumber(value: number | null | undefined): string {
  return value === undefined || value === null ? 'Sin dato' : String(value);
}

function normalize(value: string): string {
  return value.normalize('NFC').trim().toLocaleLowerCase('es-AR');
}

function coverageNote(result: OutagesResult): string | null {
  if (result.coverage.status === 'coverage_unverified' && (result.outages?.length ?? 0) > 0) {
    return 'La cobertura de esta zona no está verificada. Los cortes listados son los reportados por el ENRE.';
  }
  return null;
}

export function OutagesPanel() {
  const scope = useRequestScope();
  const [areas, setAreas] = useState<AreasResult | null>(null);
  const [areasLoading, setAreasLoading] = useState(true);
  const [areasError, setAreasError] = useState('');
  const [partido, setPartido] = useState('');
  const [localidad, setLocalidad] = useState('');
  const [areaFilter, setAreaFilter] = useState('');
  const [result, setResult] = useState<OutagesResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [address, setAddress] = useState('');
  const [resolving, setResolving] = useState(false);
  const [candidates, setCandidates] = useState<ResolveZone[] | null>(null);
  const [searchMessage, setSearchMessage] = useState('');
  const [geoMessage, setGeoMessage] = useState('');
  const [geoBusy, setGeoBusy] = useState(false);

  useEffect(() => {
    const request = scope.begin('outage-areas');
    setAreasLoading(true);
    void outagesApi.areas(request.signal).then(data => {
      if (request.isCurrent()) setAreas(data);
    }).catch((reason: unknown) => {
      if (request.isCurrent() && !quiet(reason)) setAreasError(messageFor(reason));
    }).finally(() => {
      if (request.isCurrent()) setAreasLoading(false);
    });
  }, [scope]);

  async function load(partidoValue: string, localidadValue: string): Promise<void> {
    if (!partidoValue) {
      setError('Elegí un partido para consultar.');
      return;
    }
    const request = scope.begin('outage-query');
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const data = await outagesApi.query(partidoValue, localidadValue, request.signal);
      if (request.isCurrent()) setResult(data);
    } catch (reason: unknown) {
      if (request.isCurrent() && !quiet(reason)) setError(messageFor(reason));
    } finally {
      if (request.isCurrent()) setLoading(false);
    }
  }

  function applyZone(zone: ResolveZone): void {
    setPartido(zone.partido);
    setLocalidad(zone.localidad ?? '');
    setCandidates(null);
    setAreas(previous => {
      if (previous === null) return previous;
      let found = false;
      const areas = previous.areas.map(area => {
        if (area.partido !== zone.partido) return area;
        found = true;
        if (zone.localidad === null || zone.localidad === undefined ||
            area.localidades.some(option => option.localidad === zone.localidad)) {
          return area;
        }
        return { ...area, localidades: [...area.localidades, {
          localidad: zone.localidad, coverage: zone.coverage, reported: false,
        }] };
      });
      if (!found) {
        areas.push({ partido: zone.partido, localidades: zone.localidad
          ? [{ localidad: zone.localidad, coverage: zone.coverage, reported: false }]
          : [] });
      }
      return { ...previous, areas };
    });
    setSearchMessage(zone.granularity === 'partido'
      ? `Búsqueda limitada al partido ${zone.partido}: no se pudo determinar una localidad confiable.`
      : `Zona resuelta: ${zone.partido} · ${zone.localidad ?? ''}.`);
    void load(zone.partido, zone.localidad ?? '');
  }

  async function searchAddress(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const value = address.trim();
    if (!value) {
      setSearchMessage('Ingresá una dirección con calle y altura.');
      return;
    }
    const request = scope.begin('outage-resolve');
    setResolving(true);
    setError('');
    setCandidates(null);
    setSearchMessage('');
    try {
      const data = await outagesApi.resolve(value, {
        ...(partido ? { partido } : {}),
        ...(localidad ? { localidad } : {}),
      }, request.signal);
      if (!request.isCurrent()) return;
      if (data.status === 'resolved') {
        applyZone(data.zone);
      } else {
        setCandidates(data.candidates);
        setSearchMessage('La dirección es ambigua. Elegí una de las zonas encontradas.');
      }
    } catch (reason: unknown) {
      if (request.isCurrent() && !quiet(reason)) setError(messageFor(reason));
    } finally {
      if (request.isCurrent()) setResolving(false);
    }
  }

  function useDeviceLocation(): void {
    setGeoMessage('');
    if (typeof navigator === 'undefined' || !('geolocation' in navigator)) {
      setGeoMessage('Tu navegador no permite obtener la ubicación. Usá partido, localidad o dirección.');
      return;
    }
    setGeoBusy(true);
    navigator.geolocation.getCurrentPosition(position => {
      const request = scope.begin('outage-location');
      void outagesApi.resolveLocation(
        position.coords.latitude, position.coords.longitude, request.signal,
      ).then(data => {
        if (!request.isCurrent()) return;
        if (data.status === 'resolved') applyZone(data.zone);
        else setGeoMessage('La ubicación es ambigua. Probá con partido, localidad o dirección.');
      }).catch((reason: unknown) => {
        if (request.isCurrent() && !quiet(reason)) setGeoMessage(messageFor(reason));
      }).finally(() => {
        if (request.isCurrent()) setGeoBusy(false);
      });
    }, failure => {
      setGeoBusy(false);
      setGeoMessage(failure.code === failure.PERMISSION_DENIED
        ? 'No autorizaste la ubicación. Podés consultar por partido, localidad o dirección.'
        : 'No pudimos obtener tu ubicación. Probá nuevamente o usá otra búsqueda.');
    }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 });
  }

  const partidoAreas = areas?.areas ?? [];
  const selectedArea = partidoAreas.find(area => area.partido === partido);
  const localidadOptions = (selectedArea?.localidades ?? []).filter(
    option => option.localidad !== null && option.localidad !== undefined,
  );
  const filter = normalize(areaFilter);
  const visibleAreas = partidoAreas.filter(area => area.partido === partido || !filter ||
    normalize(area.partido).includes(filter) ||
    area.localidades.some(option => option.localidad !== null &&
      option.localidad !== undefined && normalize(option.localidad).includes(filter)));

  return <div className="space-y-6">
    <Card>
      <CardHeader><CardTitle>Consultar cortes</CardTitle></CardHeader>
      <CardContent className="space-y-5">
        {areasError && <Alert>{areasError}</Alert>}
        {areasLoading && <p role="status">Cargando zonas disponibles…</p>}
        <div className="space-y-2">
          <Label htmlFor="outage-filter">Buscar zona</Label>
          <input id="outage-filter" className="min-h-10 w-full rounded-md border border-input bg-background px-3"
            autoComplete="off" value={areaFilter} placeholder="Partido o localidad"
            onChange={event => setAreaFilter(event.target.value)} />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="outage-partido">Partido</Label>
            <select id="outage-partido" className="min-h-10 w-full rounded-md border border-input bg-background px-3"
              value={partido} onChange={event => {
                setPartido(event.target.value);
                setLocalidad('');
                setResult(null);
                setCandidates(null);
                setSearchMessage('');
              }}>
              <option value="">Elegí un partido</option>
              {visibleAreas.map(area => <option key={area.partido} value={area.partido}>{area.partido}</option>)}
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="outage-localidad">Localidad (opcional)</Label>
            <select id="outage-localidad" className="min-h-10 w-full rounded-md border border-input bg-background px-3"
              value={localidad} disabled={localidadOptions.length === 0}
              onChange={event => { setLocalidad(event.target.value); setResult(null); }}>
              <option value="">Todas las localidades del partido</option>
              {localidadOptions.map(option => option.localidad === null || option.localidad === undefined ? null :
                <option key={option.localidad} value={option.localidad}>{option.localidad}</option>)}
            </select>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button type="button" disabled={!partido || loading} onClick={() => {
            setSearchMessage(''); setCandidates(null); void load(partido, localidad);
          }}>Consultar cortes</Button>
          <Button type="button" variant="outline" disabled={geoBusy} onClick={useDeviceLocation}>
            {geoBusy ? 'Obteniendo ubicación…' : 'Usar mi ubicación'}
          </Button>
        </div>

        <form aria-label="Buscar por dirección" className="space-y-2 border-t border-border pt-4"
          onSubmit={event => { void searchAddress(event); }}>
          <Label htmlFor="outage-address">Dirección (calle y altura)</Label>
          <div className="flex flex-wrap gap-3">
            <input id="outage-address" className="min-h-10 min-w-0 flex-1 rounded-md border border-input bg-background px-3"
              autoComplete="off" value={address} onChange={event => setAddress(event.target.value)}
              placeholder="Ej.: Calchaquí 100" />
            <Button type="submit" variant="secondary" disabled={resolving}>
              {resolving ? 'Buscando…' : 'Buscar dirección'}
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            La dirección y tu ubicación se envían solo al backend de Energía Sur para resolver la zona.
            No se guardan en el navegador ni se envían al ENRE.
          </p>
        </form>

        {searchMessage && <p role="status">{searchMessage}</p>}
        {geoMessage && <Alert>{geoMessage}</Alert>}
        {candidates && <ul aria-label="Zonas candidatas" className="space-y-2">
          {candidates.map(candidate => <li key={`${candidate.partido}-${candidate.localidad ?? ''}`}>
            <Button type="button" variant="outline" onClick={() => applyZone(candidate)}>
              {candidate.partido}{candidate.localidad ? ` · ${candidate.localidad}` : ''} — {coverageLabel(candidate.coverage)}
            </Button>
          </li>)}
        </ul>}
        {error && <Alert>{error}</Alert>}
        {loading && <p role="status">Consultando cortes…</p>}
      </CardContent>
    </Card>

    {result && <Card aria-live="polite">
      <CardHeader>
        <CardTitle>{stateHeading(result.state)}</CardTitle>
        <p className="text-sm text-muted-foreground">
          {result.granularity === 'localidad' ? 'Resultado por localidad' : 'Resultado por partido'}
          {' · '}{coverageLabel(result.coverage.status)}
          {' · '}{result.source_status === 'degraded'
            ? 'Fuente degradada' : freshnessLabel(result.freshness)}
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <p>{result.source_status === 'degraded' && result.state === 'unavailable'
          ? 'El ENRE informó que no está actualizando la información. No podemos confirmar cortes ni ausencia de cortes.'
          : stateDetail(result.state)}</p>
        {result.source_status === 'degraded' && <Alert>
          El ENRE informó que no está actualizando la información. Se muestran los últimos datos válidos.
        </Alert>}
        {result.freshness !== 'fresh' && <Alert>
          {freshnessLabel(result.freshness)}: {stateDetail(result.freshness === 'stale' ? 'stale' : 'unavailable')}
        </Alert>}
        {coverageNote(result) !== null && <Alert>{coverageNote(result)}</Alert>}

        <dl className="grid gap-2 text-sm sm:grid-cols-2">
          <div><dt className="font-medium">Fuente</dt>
            <dd><a className="underline" href={result.source_url} target="_blank" rel="noreferrer">{result.source}</a></dd></div>
          <div><dt className="font-medium">Última actualización de la fuente</dt>
            <dd>{formatInstant(result.source_updated_at) || 'No informada'}</dd></div>
          <div><dt className="font-medium">Consultado</dt>
            <dd>{formatInstant(result.fetched_at) || 'No disponible'}</dd></div>
          <div><dt className="font-medium">Hora informada por la fuente</dt>
            <dd>{formatReportedTime(result.source_reported_time) || 'No informada'}</dd></div>
        </dl>

        <section aria-label="Totales oficiales" className="rounded-lg border border-border p-4 text-sm">
          <p className="font-medium">Total Edesur (todos los partidos, no la zona consultada)</p>
          <p>Sin suministro: {optionalNumber(result.total_users_without)} usuarios</p>
          <p>Con suministro: {optionalNumber(result.total_users_with)} usuarios</p>
          <p>Afectados el día anterior: {optionalNumber(result.users_affected_yesterday)} usuarios</p>
        </section>

        {(result.outages?.length ?? 0) > 0 && <Table>
          <TableHeader><TableRow>
            <TableHead>Categoría</TableHead><TableHead>Zona</TableHead>
            <TableHead>Alimentador</TableHead><TableHead>Usuarios afectados</TableHead>
            <TableHead>Normalización</TableHead>
          </TableRow></TableHeader>
          <TableBody>
            {result.outages?.map((outage, index) => <TableRow key={`${outage.category}-${outage.partido}-${outage.localidad ?? ''}-${index}`}>
              <TableCell>{categoryLabel(outage.category)}</TableCell>
              <TableCell>{outage.partido}{outage.localidad ? ` · ${outage.localidad}` : ''}</TableCell>
              <TableCell>{outage.subestacion_alimentador ?? 'Sin dato'}</TableCell>
              <TableCell>{outage.affected_users === null || outage.affected_users === undefined
                ? 'Sin dato' : String(outage.affected_users)}</TableCell>
              <TableCell>{outage.normalizacion ?? 'Sin datos'}</TableCell>
            </TableRow>)}
          </TableBody>
        </Table>}
      </CardContent>
    </Card>}
  </div>;
}
