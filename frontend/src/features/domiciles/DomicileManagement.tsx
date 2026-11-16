import { useCallback, useEffect, useState } from 'react';
import { DiaryError, errorMessage } from '../../lib/httpError.ts';
import { sessionStore } from '../../stores/session.ts';
import { useRequestScope } from '../../useRequestScope.ts';
import { Alert } from '../../components/ui/alert.tsx';
import { Button } from '../../components/ui/button.tsx';
import { Card, CardContent } from '../../components/ui/card.tsx';
import { domicilesApi } from './api.ts';
import type { Meter, MeterInput } from './api.ts';
import { MeterForm } from './forms.tsx';
import { AccountSection } from '../account/AccountSection.tsx';

export type MeterLoad = { rows: Meter[]; status: 'loading' | 'ready' | 'failed' };

// Meter management for the selected domicile. The active meter is chosen in the
// account context panel; this component reports the loaded list to its owner.
export function DomicileManagement({ selected, generation, onMetersChange }: {
  selected: string; generation: number; onMetersChange: (state: MeterLoad) => void;
}) {
  const scope = useRequestScope();
  const [meters, setMeters] = useState<Meter[]>([]);
  const [editingMeter, setEditingMeter] = useState<Meter | null>(null);
  const [meterRevision, setMeterRevision] = useState(0);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [conflict, setConflict] = useState(false);
  const active = useCallback(() => {
    const state = sessionStore.getState();
    return state.generation === generation && state.selectedDomicileId === selected;
  }, [generation, selected]);

  const failed = useCallback((reason: unknown) => {
    if (!active()) return;
    if (reason instanceof DiaryError && reason.status === 401) {
      sessionStore.getState().clearSession(generation, true);
      return;
    }
    if (reason instanceof DiaryError && reason.status === 409 && reason.code === 'VERSION_CONFLICT') {
      setConflict(true);
      setError('La versión cambió. Descartá el borrador y recargá antes de volver a editar.');
      return;
    }
    if (reason instanceof DiaryError && reason.status === 409 && reason.code === 'DUPLICATE_METER') {
      setError('Ese número de medidor ya está registrado en tu cuenta. Revisá el número antes de guardar.');
      return;
    }
    setError(errorMessage(reason));
  }, [active, generation]);

  const refresh = useCallback(async (discard: boolean) => {
    const request = scope.begin('meters-load');
    setLoading(true); setError('');
    try {
      const list = await domicilesApi.meters(selected, request.signal);
      if (!request.isCurrent() || !active()) return;
      setMeters(list);
      setLoaded(true);
      if (discard) {
        setEditingMeter(null); setMeterRevision(n => n + 1); setConflict(false);
        setNotice('Borrador descartado. Revisá la versión actual antes de guardar.');
      }
    } catch (reason: unknown) {
      if (request.isCurrent() && active()) failed(reason);
    } finally {
      if (request.isCurrent() && active()) setLoading(false);
    }
  }, [scope, selected, active, failed]);
  useEffect(() => { void refresh(false); }, [refresh]);
  useEffect(() => {
    onMetersChange({ rows: meters, status: loading ? 'loading' : loaded ? 'ready' : 'failed' });
  }, [meters, loading, loaded, onMetersChange]);

  async function saveMeter(input: MeterInput) {
    const request = scope.begin('meters-mutation');
    setBusy(true); setError(''); setNotice('');
    try {
      const result = editingMeter
        ? await domicilesApi.correctMeter(editingMeter, input, request.signal)
        : await domicilesApi.createMeter(selected, input, request.signal);
      if (!request.isCurrent() || !active()) return;
      setMeters(current => editingMeter ? current.map(row => row.id === result.id ? result : row) : [...current, result]);
      setEditingMeter(null); setMeterRevision(n => n + 1); setConflict(false); setNotice('Medidor guardado.');
    } catch (reason: unknown) {
      if (request.isCurrent() && active()) failed(reason);
    } finally {
      if (request.isCurrent() && active()) setBusy(false);
    }
  }

  const disabled = busy || loading || conflict;
  return <AccountSection id="medidores" title="Medidores"
    description="Registrá y corregí los medidores del domicilio. El medidor activo se elige en Contexto de trabajo.">
    <Card><CardContent>
      <div className="space-y-4">
        {error && <Alert>{error}</Alert>}
        {notice && <Alert role="status">{notice}</Alert>}
        {loading && <p role="status">Cargando medidores…</p>}
        {!loading && !loaded && <Button type="button" variant="outline" onClick={() => void refresh(false)}>Reintentar administración</Button>}
        {conflict && <Button type="button" variant="outline" disabled={busy || loading} onClick={() => void refresh(true)}>Descartar borrador y recargar administración</Button>}
        {loaded && meters.length === 0 && <p>No hay medidores registrados. El domicilio puede usarse sin medidor.</p>}
        <ul aria-label="Medidores registrados" className="space-y-2">{meters.map(row => <li key={row.id} className="flex flex-wrap items-center gap-2"><span>{row.meter_number}{row.alias ? ` — ${row.alias}` : ''}</span><Button type="button" variant="outline" size="sm" disabled={disabled} onClick={() => { setEditingMeter(row); setMeterRevision(n => n + 1); setError(''); setNotice(''); }}>Corregir medidor</Button></li>)}</ul>
        {loaded && <MeterForm key={`${selected}:${editingMeter?.id ?? 'new'}:${editingMeter?.version ?? 0}:${meterRevision}`} row={editingMeter} busy={disabled} save={saveMeter} cancel={() => { setEditingMeter(null); setMeterRevision(n => n + 1); setError(''); }} />}
      </div>
    </CardContent></Card>
  </AccountSection>;
}
