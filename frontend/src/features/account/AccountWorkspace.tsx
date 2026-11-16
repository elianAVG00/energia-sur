import { useCallback, useEffect, useState } from 'react';
import { diaryApi, DiaryError, errorMessage } from '../../diaryApi.ts';
import type { Domicile, Session } from '../../diaryApi.ts';
import { useRequestScope } from '../../useRequestScope.ts';
import { sessionStore, useSessionStore } from '../../stores/session.ts';
import { Alert } from '../../components/ui/alert.tsx';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card.tsx';
import { Label } from '../../components/ui/label.tsx';
import { DomicileForm } from '../diary/forms.tsx';
import { DiarySection } from '../diary/DiarySection.tsx';
import { DomicileAddress } from '../domiciles/DomicileAddress.tsx';
import { DomicileManagement } from '../domiciles/DomicileManagement.tsx';
import type { MeterLoad } from '../domiciles/DomicileManagement.tsx';
import { ReadingHistory } from '../readings/ReadingHistory.tsx';
import { BillHistory } from '../bills/BillHistory.tsx';
import { ConsumptionPanel } from '../consumption/ConsumptionPanel.tsx';
import { AccountSection } from './AccountSection.tsx';

const SECTIONS = [
  { id: 'domicilios', label: 'Domicilios' },
  { id: 'medidores', label: 'Medidores' },
  { id: 'cortes', label: 'Cortes e interrupciones' },
  { id: 'lecturas', label: 'Lecturas' },
  { id: 'facturas', label: 'Facturas' },
  { id: 'consumo', label: 'Consumo y estimación' },
] as const;

export function AccountWorkspace({ session, generation }: { session: Session; generation: number }) {
  const scope = useRequestScope();
  const selected = useSessionStore(state => state.selectedDomicileId);
  const [domiciles, setDomiciles] = useState<Domicile[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  // Scope-tagged UI state resets synchronously when the account or domicile changes,
  // so a previous meter can never be rendered for the new domicile.
  const [meterChoice, setMeterChoice] = useState<{ scope: string; id: string }>({ scope: '', id: '' });
  const [meterSource, setMeterSource] = useState<{ scope: string; state: MeterLoad }>({
    scope: '', state: { rows: [], status: 'loading' },
  });
  const clearFeedback = useCallback(() => { setNotice(''); setError(''); }, []);
  const updateDomicile = useCallback((row: Domicile) => setDomiciles(current => current.map(existing => existing.id === row.id ? row : existing)), []);
  const active = useCallback(() => sessionStore.getState().generation === generation, [generation]);
  const failed = useCallback((reason: unknown) => {
    if (!active()) return;
    if (reason instanceof DiaryError && reason.status === 401) sessionStore.getState().clearSession(generation, true);
    else setError(errorMessage(reason));
  }, [active, generation]);

  useEffect(() => {
    const request = scope.begin('domiciles');
    void diaryApi.domiciles(request.signal).then(rows => {
      if (!request.isCurrent() || !active()) return;
      setDomiciles(rows);
      const selection = sessionStore.getState().selectedDomicileId;
      if (!rows.some(row => row.id === selection)) sessionStore.getState().selectDomicile(rows[0]?.id ?? '');
      setLoaded(true);
    }).catch((reason: unknown) => { if (request.isCurrent() && active()) { failed(reason); setLoaded(true); } });
  }, [scope, active, failed]);

  async function createDomicile(address: string): Promise<boolean> {
    const request = scope.begin('domicile-mutation');
    setBusy(true); setError(''); setNotice('');
    try {
      const domicile = await diaryApi.createDomicile(address, session.csrf_token, request.signal);
      if (!request.isCurrent() || !active()) return false;
      setDomiciles(rows => [...rows, domicile]);
      sessionStore.getState().selectDomicile(domicile.id);
      setNotice('Operación guardada.');
      return true;
    } catch (reason: unknown) { if (request.isCurrent() && active()) failed(reason); return false; }
    finally { if (request.isCurrent() && active()) setBusy(false); }
  }

  const scopeKey = `${generation}:${selected}`;
  const activeDomicile = domiciles.find(row => row.id === selected) ?? null;
  const meterLoad = meterSource.scope === scopeKey
    ? meterSource.state
    : { rows: [], status: 'loading' as const };
  const meters = meterLoad.rows;
  const meterId = meterChoice.scope === scopeKey && meters.some(row => row.id === meterChoice.id) ? meterChoice.id : '';
  const activeMeter = meters.find(row => row.id === meterId) ?? null;
  const onMetersChange = useCallback((state: MeterLoad) => setMeterSource({ scope: scopeKey, state }), [scopeKey]);
  const meterHint = (action: string): string => meterLoad.status === 'loading'
    ? 'Cargando medidores…'
    : meterLoad.status === 'failed'
      ? 'No se pudo cargar la lista de medidores. Reintentá en la sección Medidores.'
      : meters.length === 0
        ? 'Este domicilio no tiene medidores registrados. El diario sigue disponible sin medidor.'
        : `Elegí un medidor en Contexto de trabajo para ${action}.`;
  const sections = selected ? SECTIONS : SECTIONS.slice(0, 1);

  return <div className="space-y-8">
    {error && <Alert>{error}</Alert>}
    {notice && <Alert role="status">{notice}</Alert>}
    {!loaded && <p role="status">Cargando domicilios…</p>}
    <nav aria-label="Índice de Mi cuenta" className="rounded-xl border border-border bg-card px-4 py-3">
      <ul className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
        {sections.map(section => <li key={section.id}>
          <a href={`#${section.id}`} className="font-medium text-primary underline-offset-4 hover:underline">{section.label}</a>
        </li>)}
      </ul>
    </nav>
    <Card aria-labelledby="account-context-heading">
      <CardHeader><CardTitle id="account-context-heading">Contexto de trabajo</CardTitle></CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">Elegí el domicilio y, si corresponde, el medidor sobre los que trabajás.</p>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="selected-domicile">Domicilio seleccionado</Label>
            {loaded && domiciles.length > 0
              ? <select id="selected-domicile" className="min-h-10 w-full min-w-0 rounded-md border border-input bg-card px-3 py-2 text-base focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:opacity-50" value={selected} disabled={busy} onChange={event => {
                sessionStore.getState().selectDomicile(event.target.value); setError(''); setNotice('');
              }}><option value="" disabled>Elegí un domicilio</option>{domiciles.map(d => <option key={d.id} value={d.id}>{d.display_address}</option>)}</select>
              : <p className="text-sm text-muted-foreground">{loaded ? 'Todavía no hay un domicilio registrado. Usá la sección Domicilios para crear el primero.' : 'Sin domicilio seleccionado.'}</p>}
            <p className="text-sm text-muted-foreground">Domicilio activo: {activeDomicile?.display_address ?? 'sin seleccionar'}</p>
          </div>
          <div className="space-y-2">
            {meters.length > 0
              ? <><Label htmlFor="reading-meter">Medidor para consultar lecturas</Label><select id="reading-meter" className="min-h-10 w-full min-w-0 rounded-md border border-input bg-card px-3 py-2 text-base focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:opacity-50" value={meterId} onChange={event => setMeterChoice({ scope: scopeKey, id: event.target.value })}>
                <option value="">Elegí un medidor</option>{meters.map(row => <option key={row.id} value={row.id}>{row.meter_number}{row.alias ? ` — ${row.alias}` : ''}</option>)}
              </select></>
              : <p className="text-sm text-muted-foreground">{meterLoad.status === 'loading' ? 'Cargando medidores…' : meterLoad.status === 'failed' ? 'No se pudo cargar la lista de medidores. Reintentá en la sección Medidores.' : 'Los medidores se administran en la sección Medidores.'}</p>}
            <p className="text-sm text-muted-foreground">{activeMeter ? `Medidor activo: ${activeMeter.meter_number}${activeMeter.alias ? ` — ${activeMeter.alias}` : ''}` : 'Sin medidor seleccionado.'}</p>
          </div>
        </div>
      </CardContent>
    </Card>
    <AccountSection id="domicilios" title="Domicilios"
      description="Registrá un domicilio y corregí su dirección. El domicilio activo se elige en Contexto de trabajo.">
      <Card><CardContent>
        <DomicileForm busy={busy || !loaded} save={createDomicile} addresses={domiciles} />
        {loaded && domiciles.length === 0 && <p>Registrá un domicilio para empezar. No se necesita medidor.</p>}
      </CardContent></Card>
      {selected && <DomicileAddress key={scopeKey} selected={selected} generation={generation} rows={domiciles} updateRow={updateDomicile} />}
    </AccountSection>
    {selected && <DomicileManagement key={scopeKey} selected={selected} generation={generation} onMetersChange={onMetersChange} />}
    {selected && <DiarySection key={selected} session={session} generation={generation} selected={selected} onActivity={clearFeedback} />}
    {selected && <AccountSection id="lecturas" title="Lecturas"
      description="Registrá la lectura del medidor, adjuntá una fotografía y consultá el historial.">
      {meterId
        ? <ReadingHistory key={`readings:${generation}:${selected}:${meterId}`} generation={generation} domicileId={selected} meterId={meterId} />
        : <p className="text-sm text-muted-foreground">{meterHint('registrar y consultar lecturas')}</p>}
    </AccountSection>}
    {selected && <AccountSection id="facturas" title="Facturas"
      description="Registrá tus facturas, consultá su detalle y compará el consumo facturado con el registrado.">
      {meterId
        ? <BillHistory key={`bills:${generation}:${selected}:${meterId}`} generation={generation} domicileId={selected} meterId={meterId} />
        : <p className="text-sm text-muted-foreground">{meterHint('registrar y consultar facturas')}</p>}
    </AccountSection>}
    {selected && <AccountSection id="consumo" title="Consumo y estimación"
      description="Consultá la evolución del consumo y obtené una estimación orientativa.">
      {meterId
        ? <ConsumptionPanel key={`consumption:${generation}:${selected}:${meterId}`} generation={generation} domicileId={selected} meterId={meterId} />
        : <p className="text-sm text-muted-foreground">{meterHint('ver la evolución y la estimación del consumo')}</p>}
    </AccountSection>}
  </div>;
}
