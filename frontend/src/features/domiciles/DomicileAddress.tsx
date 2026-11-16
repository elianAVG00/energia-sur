import { useCallback, useEffect, useState } from 'react';
import type { Domicile } from '../../diaryApi.ts';
import { DiaryError, errorMessage } from '../../lib/httpError.ts';
import { sessionStore } from '../../stores/session.ts';
import { useRequestScope } from '../../useRequestScope.ts';
import { Alert } from '../../components/ui/alert.tsx';
import { Button } from '../../components/ui/button.tsx';
import { Card, CardContent } from '../../components/ui/card.tsx';
import { domicilesApi } from './api.ts';
import type { ManagedDomicile } from './api.ts';
import { AddressForm } from './forms.tsx';

// Address management for the selected domicile. Meter data stays in
// DomicileManagement so each request keeps one owner.
export function DomicileAddress({ selected, generation, rows, updateRow }: {
  selected: string; generation: number; rows: Domicile[]; updateRow: (row: Domicile) => void;
}) {
  const scope = useRequestScope();
  const [domicile, setDomicile] = useState<ManagedDomicile | null>(null);
  const [editing, setEditing] = useState(false);
  const [revision, setRevision] = useState(0);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
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
    setError(errorMessage(reason));
  }, [active, generation]);

  const refresh = useCallback(async (discard: boolean) => {
    const request = scope.begin('address-load');
    setLoading(true); setError('');
    try {
      const home = await domicilesApi.management(selected, request.signal);
      if (!request.isCurrent() || !active()) return;
      setDomicile(home);
      updateRow({ id: home.id, display_address: home.display_address });
      if (discard) {
        setEditing(false); setRevision(n => n + 1); setConflict(false);
        setNotice('Borrador descartado. Revisá la versión actual antes de guardar.');
      }
    } catch (reason: unknown) {
      if (request.isCurrent() && active()) failed(reason);
    } finally {
      if (request.isCurrent() && active()) setLoading(false);
    }
  }, [scope, selected, active, failed, updateRow]);
  useEffect(() => { void refresh(false); }, [refresh]);

  async function save(address: string) {
    if (!domicile) return;
    const request = scope.begin('address-mutation');
    setBusy(true); setError(''); setNotice('');
    try {
      const result = await domicilesApi.correctDomicile(domicile, address, request.signal);
      if (!request.isCurrent() || !active()) return;
      setDomicile(result);
      updateRow({ id: result.id, display_address: result.display_address });
      setEditing(false); setRevision(n => n + 1); setConflict(false);
      setNotice('Domicilio actualizado.');
    } catch (reason: unknown) {
      if (request.isCurrent() && active()) failed(reason);
    } finally {
      if (request.isCurrent() && active()) setBusy(false);
    }
  }

  const disabled = busy || loading || conflict;
  return <Card><CardContent>
    <div className="space-y-4">
      {error && <Alert>{error}</Alert>}
      {notice && <Alert role="status">{notice}</Alert>}
      {loading && <p role="status">Cargando domicilio…</p>}
      {!loading && !domicile && <Button type="button" variant="outline" onClick={() => void refresh(false)}>Reintentar administración</Button>}
      {conflict && <Button type="button" variant="outline" disabled={busy || loading} onClick={() => void refresh(true)}>Descartar borrador y recargar administración</Button>}
      {domicile && (editing
        ? <AddressForm key={`${domicile.id}:${domicile.version}:${revision}`} row={domicile} rows={rows} busy={disabled} save={save} cancel={() => { setEditing(false); setRevision(n => n + 1); setError(''); }} />
        : <Button type="button" variant="outline" disabled={disabled} onClick={() => { setEditing(true); setError(''); setNotice(''); }}>Corregir domicilio</Button>)}
    </div>
  </CardContent></Card>;
}
