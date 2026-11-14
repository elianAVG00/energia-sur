import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { Alert } from '../../components/ui/alert.tsx';
import { Button } from '../../components/ui/button.tsx';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card.tsx';
import { Input } from '../../components/ui/input.tsx';
import { Label } from '../../components/ui/label.tsx';
import { DiaryError, errorMessage } from '../../lib/httpError.ts';
import { useRequestScope } from '../../useRequestScope.ts';
import { outagesApi } from './api.ts';
import type { AreasResult, OutagesResult, ResolveZone } from './api.ts';
import { OutagesResultCard } from './OutagesResultCard.tsx';
import { coverageLabel, retryAfterMessage } from './state.ts';

// Native selects mirror the local Input styling so both fields share one language.
const SELECT_CLASS = 'min-h-10 w-full min-w-0 rounded-md border border-input bg-card px-3 text-base shadow-xs outline-none transition-colors focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50';

function quiet(reason: unknown): boolean {
  return reason instanceof DiaryError && reason.kind === 'aborted';
}

function messageFor(reason: unknown): string {
  if (reason instanceof DiaryError && reason.status === 429) {
    return retryAfterMessage(reason.retryAfter);
  }
  return errorMessage(reason);
}

function normalize(value: string): string {
  return value.normalize('NFC').trim().toLocaleLowerCase('es-AR');
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
  // Presentation-only routing: the same messages are shown next to the flow that
  // produced them, so a sighted user does not have to scroll back up to read them.
  const [errorScope, setErrorScope] = useState<'query' | 'address'>('query');
  const [messageScope, setMessageScope] = useState<'zone' | 'address'>('zone');
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
      setErrorScope('query');
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
      if (request.isCurrent() && !quiet(reason)) {
        setErrorScope('query');
        setError(messageFor(reason));
      }
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
    setMessageScope('zone');
    setSearchMessage(zone.granularity === 'partido'
      ? `Búsqueda limitada al partido ${zone.partido}: no se pudo determinar una localidad confiable.`
      : `Zona resuelta: ${zone.partido} · ${zone.localidad ?? ''}.`);
    void load(zone.partido, zone.localidad ?? '');
  }

  async function searchAddress(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const value = address.trim();
    if (!value) {
      setMessageScope('address');
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
        setMessageScope('address');
        setSearchMessage('La dirección es ambigua. Elegí una de las zonas encontradas.');
      }
    } catch (reason: unknown) {
      if (request.isCurrent() && !quiet(reason)) {
        setErrorScope('address');
        setError(messageFor(reason));
      }
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
    {error && errorScope === 'query' && <Alert>{error}</Alert>}

    <Card>
      <CardHeader>
        <CardTitle>Consultar cortes</CardTitle>
        <p className="text-sm text-muted-foreground">
          Elegí un partido y, si querés, una localidad para consultar los cortes informados por el ENRE.
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {areasError && <Alert>{areasError}</Alert>}
        {areasLoading && <p role="status" className="text-sm text-muted-foreground">Cargando zonas disponibles…</p>}

        <div className="space-y-2">
          <Label htmlFor="outage-filter">Buscar zona</Label>
          <Input id="outage-filter" className="bg-card" autoComplete="off" value={areaFilter}
            placeholder="Partido o localidad" aria-describedby="outage-filter-help"
            onChange={event => setAreaFilter(event.target.value)} />
          <p id="outage-filter-help" className="text-sm text-muted-foreground">
            Filtrá la lista de partidos y localidades.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="outage-partido">Partido</Label>
            <select id="outage-partido" className={SELECT_CLASS} value={partido} onChange={event => {
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
            <select id="outage-localidad" className={SELECT_CLASS} value={localidad}
              disabled={localidadOptions.length === 0}
              onChange={event => { setLocalidad(event.target.value); setResult(null); }}>
              <option value="">Todas las localidades del partido</option>
              {localidadOptions.map(option => option.localidad === null || option.localidad === undefined ? null :
                <option key={option.localidad} value={option.localidad}>{option.localidad}</option>)}
            </select>
          </div>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
          <Button type="button" className="min-h-11 w-full sm:w-auto" disabled={!partido || loading} onClick={() => {
            setSearchMessage(''); setCandidates(null); void load(partido, localidad);
          }}>Consultar cortes</Button>
          <Button type="button" variant="outline" className="min-h-11 w-full sm:w-auto"
            disabled={geoBusy} onClick={useDeviceLocation}>
            {geoBusy ? 'Obteniendo ubicación…' : 'Usar mi ubicación'}
          </Button>
        </div>

        {loading && <div role="status" className="rounded-lg border border-border bg-muted px-4 py-3">
          <p className="text-sm font-medium">Consultando cortes…</p>
          <p className="text-xs text-muted-foreground">Buscando los últimos datos disponibles para la zona elegida.</p>
        </div>}
        {geoMessage && <Alert>{geoMessage}</Alert>}
        {searchMessage && messageScope === 'zone' && <p role="status"
          className="rounded-lg border border-border bg-accent px-4 py-3 text-sm text-accent-foreground">
          {searchMessage}
        </p>}
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Buscar por dirección</CardTitle>
        <p className="text-sm text-muted-foreground">
          Resolvé la zona a partir de una calle y altura.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <form aria-label="Buscar por dirección" className="space-y-3"
          onSubmit={event => { void searchAddress(event); }}>
          <div className="space-y-2">
            <Label htmlFor="outage-address">Dirección (calle y altura)</Label>
            <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
              <Input id="outage-address" className="min-w-0 bg-card" autoComplete="off" value={address}
                placeholder="Ej.: Calchaquí 100" aria-describedby="outage-address-privacy"
                onChange={event => setAddress(event.target.value)} />
              <Button type="submit" variant="secondary" className="min-h-11 w-full sm:w-auto" disabled={resolving}>
                {resolving ? 'Buscando…' : 'Buscar dirección'}
              </Button>
            </div>
          </div>
          <p id="outage-address-privacy" className="text-sm text-muted-foreground">
            La dirección y tu ubicación se envían solo al backend de Energía Sur para resolver la zona.
            No se guardan en el navegador ni se envían al ENRE.
          </p>
        </form>

        {error && errorScope === 'address' && <Alert>{error}</Alert>}
        {searchMessage && messageScope === 'address' && <p role="status"
          className="rounded-lg border border-border bg-accent px-4 py-3 text-sm text-accent-foreground">
          {searchMessage}
        </p>}

        {candidates && <div className="space-y-3 border-t border-border pt-4">
          <p id="outage-candidates" className="text-sm font-medium">Zonas candidatas</p>
          <ul aria-labelledby="outage-candidates" className="grid gap-2 sm:grid-cols-2">
            {candidates.map(candidate => <li key={`${candidate.partido}-${candidate.localidad ?? ''}`} className="min-w-0">
              <Button type="button" variant="outline"
                className="h-auto min-h-11 w-full justify-start py-2 text-left whitespace-normal"
                onClick={() => applyZone(candidate)}>
                {candidate.partido}{candidate.localidad ? ` · ${candidate.localidad}` : ''} — {coverageLabel(candidate.coverage)}
              </Button>
            </li>)}
          </ul>
        </div>}
      </CardContent>
    </Card>

    {!loading && !result && !error && !candidates && <div
      className="rounded-xl border border-dashed border-border bg-card px-6 py-8 text-center shadow-sm">
      <p className="font-medium">Elegí una zona para consultar</p>
      <p className="mx-auto mt-2 max-w-xl text-sm text-muted-foreground">
        Usá el partido y la localidad, buscá una dirección o usá tu ubicación. Los resultados muestran
        los cortes informados por el ENRE para la zona, no el estado de un domicilio en particular.
      </p>
    </div>}

    {result && <OutagesResultCard result={result} />}
  </div>;
}
