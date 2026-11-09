import { useCallback, useEffect, useState } from 'react';
import type { Domicile } from '../../diaryApi.ts';
import { DiaryError, errorMessage } from '../../lib/httpError.ts';
import { sessionStore } from '../../stores/session.ts';
import { useRequestScope } from '../../useRequestScope.ts';
import { Alert } from '../../components/ui/alert.tsx';
import { Button } from '../../components/ui/button.tsx';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card.tsx';
import { domicilesApi } from './api.ts';
import type { ManagedDomicile, Meter, MeterInput } from './api.ts';
import { AddressForm, MeterForm } from './forms.tsx';
import { ReadingHistory } from '../readings/ReadingHistory.tsx';

export function DomicileManagement({ selected, generation, rows, updateRow }: {
  selected: string; generation: number; rows: Domicile[]; updateRow: (row: Domicile) => void;
}) {
  const scope = useRequestScope();
  const [domicile, setDomicile] = useState<ManagedDomicile | null>(null);
  const [meters, setMeters] = useState<Meter[]>([]);
  const [editingAddress, setEditingAddress] = useState(false);
  const [editingMeter, setEditingMeter] = useState<Meter | null>(null);
  const [readingMeter, setReadingMeter] = useState<string>('');
  const [addressRevision, setAddressRevision] = useState(0);
  const [meterRevision, setMeterRevision] = useState(0);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [conflict, setConflict] = useState<'address' | 'meter' | null>(null);
  const active = useCallback(() => {
    const state = sessionStore.getState();
    return state.generation === generation && state.selectedDomicileId === selected;
  }, [generation, selected]);

  const failed = useCallback((reason: unknown, target: 'address' | 'meter' | null = null) => {
    if (!active()) return;
    if (target && reason instanceof DiaryError && reason.status === 409 && reason.code === 'VERSION_CONFLICT') {
      setConflict(target);
      setError('La versión cambió. Descartá el borrador y recargá antes de volver a editar.');
    } else if (reason instanceof DiaryError && reason.status === 409 && reason.code === 'DUPLICATE_METER') {
      setError('Ese número de medidor ya está registrado en tu cuenta. Revisá el número antes de guardar.');
    } else setError(errorMessage(reason));
  }, [active]);

  const refresh = useCallback(async (discard: 'address' | 'meter' | null) => {
    const request = scope.begin('load');
    setLoading(true); setError('');
    try {
      const [home, list] = await Promise.all([domicilesApi.management(selected, request.signal), domicilesApi.meters(selected, request.signal)]);
      if (!request.isCurrent() || !active()) return;
      if (discard !== 'meter') {
        setDomicile(home);
        updateRow({ id: home.id, display_address: home.display_address });
      }
      if (discard !== 'address') setMeters(list);
      if (discard) {
        if (discard === 'address') { setEditingAddress(false); setAddressRevision(n => n + 1); }
        else { setEditingMeter(null); setMeterRevision(n => n + 1); }
        setConflict(null);
        setNotice('Borrador descartado. Revisá la versión actual antes de guardar.');
      }
    } catch (reason: unknown) { if (request.isCurrent() && active()) failed(reason); }
    finally { if (request.isCurrent() && active()) setLoading(false); }
  }, [scope, selected, active, failed, updateRow]);
  useEffect(() => { void refresh(null); }, [refresh]);

  async function mutate(target: 'address' | 'meter', action: (signal: AbortSignal) => Promise<void>) {
    const request = scope.begin('mutation');
    setBusy(true); setError(''); setNotice('');
    try { await action(request.signal); }
    catch (reason: unknown) { if (request.isCurrent() && active()) failed(reason, target); }
    finally { if (request.isCurrent() && active()) setBusy(false); }
  }

  async function saveAddress(address: string) {
    if (!domicile) return;
    await mutate('address', async signal => {
      const result = await domicilesApi.correctDomicile(domicile, address, signal);
      if (signal.aborted || !active()) return;
      setDomicile(result); updateRow({ id: result.id, display_address: result.display_address });
      setEditingAddress(false); setAddressRevision(n => n + 1); setNotice('Domicilio actualizado.');
    });
  }
  async function saveMeter(input: MeterInput) {
    await mutate('meter', async signal => {
      const result = editingMeter
        ? await domicilesApi.correctMeter(editingMeter, input, signal)
        : await domicilesApi.createMeter(selected, input, signal);
      if (signal.aborted || !active()) return;
      setMeters(current => editingMeter ? current.map(row => row.id === result.id ? result : row) : [...current, result]);
      setEditingMeter(null); setMeterRevision(n => n + 1); setNotice('Medidor guardado.');
    });
  }

  const disabled = busy || loading || conflict !== null;
  return <Card><CardHeader><CardTitle>Administrar domicilio y medidores</CardTitle></CardHeader><CardContent>
    <div className="space-y-4">
      {error && <Alert>{error}</Alert>}
      {notice && <Alert role="status">{notice}</Alert>}
      {loading && <p role="status">Cargando administración…</p>}
      {conflict && <Button type="button" variant="outline" disabled={busy || loading} onClick={() => void refresh(conflict)}>Descartar borrador y recargar administración</Button>}
      {!loading && !domicile && <Button type="button" variant="outline" onClick={() => void refresh(null)}>Reintentar administración</Button>}
      {domicile && <>
        {editingAddress ? <AddressForm key={`${domicile.id}:${domicile.version}:${addressRevision}`} row={domicile} rows={rows} busy={disabled} save={saveAddress} cancel={() => { setEditingAddress(false); setAddressRevision(n => n + 1); setError(''); }} />
          : <Button type="button" variant="outline" disabled={disabled} onClick={() => { setEditingAddress(true); setError(''); setNotice(''); }}>Corregir domicilio</Button>}
        <h3 className="text-lg font-semibold">Medidores</h3>
        {!loading && meters.length === 0 && <p>No hay medidores registrados. El domicilio puede usarse sin medidor.</p>}
        <ul aria-label="Medidores registrados" className="space-y-2">{meters.map(row => <li key={row.id} className="flex flex-wrap items-center gap-2"><span>{row.meter_number}{row.alias ? ` — ${row.alias}` : ''}</span><Button type="button" variant="outline" size="sm" disabled={disabled} onClick={() => { setEditingMeter(row); setMeterRevision(n => n + 1); setError(''); setNotice(''); }}>Corregir medidor</Button></li>)}</ul>
        <MeterForm key={`${selected}:${editingMeter?.id ?? 'new'}:${editingMeter?.version ?? 0}:${meterRevision}`} row={editingMeter} busy={disabled} save={saveMeter} cancel={() => { setEditingMeter(null); setMeterRevision(n => n + 1); setError(''); }} />
        {meters.length > 0 && <div className="space-y-2"><label htmlFor="reading-meter">Medidor para consultar lecturas</label>
          <select id="reading-meter" className="min-h-10 w-full rounded-md border border-input bg-card px-3 py-2" value={readingMeter} onChange={event => setReadingMeter(event.target.value)}>
            <option value="">Elegí un medidor</option>{meters.map(row => <option key={row.id} value={row.id}>{row.meter_number}{row.alias ? ` — ${row.alias}` : ''}</option>)}
          </select>
        </div>}
        {readingMeter && meters.some(row => row.id === readingMeter) && <ReadingHistory key={`${generation}:${selected}:${readingMeter}`} generation={generation} domicileId={selected} meterId={readingMeter} />}
      </>}
    </div>
  </CardContent></Card>;
}
