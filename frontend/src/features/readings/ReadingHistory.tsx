import { useCallback, useEffect, useState } from 'react';
import { Alert } from '../../components/ui/alert.tsx';
import { Button } from '../../components/ui/button.tsx';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card.tsx';
import { DiaryError, errorMessage } from '../../lib/httpError.ts';
import { sessionStore } from '../../stores/session.ts';
import { useRequestScope } from '../../useRequestScope.ts';
import { readingsApi } from './api.ts';
import type { PhotoAction, Reading, ReadingInput } from './api.ts';
import { ReadingForm } from './ReadingForm.tsx';
import { clearCreateAttempt, clearEditAttempt, getCreateAttempt, getEditAttempt, newRequestKey, setCreateAttempt, setEditAttempt } from './attempts.ts';
import type { CreateAttempt, EditAttempt } from './attempts.ts';
import { lowerReadingWarning } from './warning.ts';

const timestampFormatter = new Intl.DateTimeFormat('es-AR', {
  timeZone: 'America/Argentina/Buenos_Aires', year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
});

function definitelyRejected(reason: unknown): boolean {
  return reason instanceof DiaryError && reason.kind === 'http' && reason.status !== null &&
    [400, 401, 403, 404, 413, 415, 422].includes(reason.status);
}

export function ReadingHistory({ generation, domicileId, meterId }: {
  generation: number; domicileId: string; meterId: string;
}) {
  const scope = useRequestScope();
  const [rows, setRows] = useState<Reading[]>([]);
  const [loading, setLoading] = useState(true);
  const [historyReady, setHistoryReady] = useState(false);
  const [error, setError] = useState('');
  const [photoUrl, setPhotoUrl] = useState('');
  const [photoLoading, setPhotoLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [editing, setEditing] = useState<Reading | null>(null);
  const [revision, setRevision] = useState(0);
  const [createAttempt, setCreate] = useState(() => getCreateAttempt(meterId));
  const [editAttempt, setEdit] = useState(() => getEditAttempt(meterId));
  const active = useCallback(() => {
    // The parent keys this component by meter; this instance never switches meters.
    // The session store knows generation/domicile only, not the reading-meter selection.
    const state = sessionStore.getState();
    return state.generation === generation && state.selectedDomicileId === domicileId;
  }, [generation, domicileId]);

  const refresh = useCallback(async () => {
    const request = scope.begin('history');
    setLoading(true); setHistoryReady(false); setError('');
    try {
      const result = await readingsApi.list(meterId, request.signal);
      if (request.isCurrent() && active()) { setRows(result); setHistoryReady(true); }
    } catch (reason: unknown) {
      if (request.isCurrent() && active()) setError(errorMessage(reason));
    } finally {
      if (request.isCurrent() && active()) setLoading(false);
    }
  }, [scope, meterId, active]);
  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => () => { if (photoUrl) URL.revokeObjectURL(photoUrl); }, [photoUrl]);

  async function showPhoto(readingId: string) {
    const request = scope.begin('photo');
    setPhotoLoading(true); setError(''); setPhotoUrl('');
    try {
      const blob = await readingsApi.photo(meterId, readingId, request.signal);
      if (request.isCurrent() && active()) setPhotoUrl(URL.createObjectURL(blob));
    } catch (reason: unknown) {
      if (request.isCurrent() && active()) setError(errorMessage(reason));
    } finally {
      if (request.isCurrent() && active()) setPhotoLoading(false);
    }
  }

  async function create(attempt: CreateAttempt) {
    const request = scope.begin('mutation');
    setBusy(true); setError(''); setNotice('');
    try {
      const result = await readingsApi.create(meterId, attempt.input, attempt.key, request.signal);
      if (!request.isCurrent() || !active()) return;
      clearCreateAttempt(meterId, attempt); setCreate(undefined);
      setRows(current => [result, ...current.filter(row => row.id !== result.id)].sort((a, b) => b.recorded_at.localeCompare(a.recorded_at)));
      setRevision(n => n + 1); setNotice('Lectura guardada.');
    } catch (reason: unknown) {
      if (!request.isCurrent() || !active()) return;
      if (definitelyRejected(reason) || (reason instanceof DiaryError && reason.code === 'DUPLICATE_READING')) {
        clearCreateAttempt(meterId, attempt); setCreate(undefined);
        setError(errorMessage(reason));
      } else {
        setError('No se pudo confirmar el resultado. Reintentá exactamente la misma solicitud antes de crear otra lectura.');
      }
    } finally { if (request.isCurrent() && active()) setBusy(false); }
  }

  async function save(input: ReadingInput, photoAction: PhotoAction): Promise<'done' | 'review'> {
    if (busy || createAttempt || editAttempt || !historyReady) return 'review';
    const preflight = scope.begin('preflight');
    setBusy(true); setError(''); setNotice('');
    const shownWarning = lowerReadingWarning(rows, meterId, input.recorded_at, input.value_kwh, editing?.id);
    try {
      const latest = await readingsApi.list(meterId, preflight.signal);
      if (!preflight.isCurrent() || !active()) return 'review';
      setRows(latest); setHistoryReady(true);
      const currentWarning = lowerReadingWarning(latest, meterId, input.recorded_at, input.value_kwh, editing?.id);
      if (shownWarning !== currentWarning) {
        setNotice('El historial cambió y el aviso se actualizó. Revisá los datos y confirmá nuevamente.');
        setBusy(false);
        return 'review';
      }
    } catch {
      if (preflight.isCurrent() && active()) {
        setHistoryReady(false); setBusy(false);
        setError('No se pudo comprobar el historial. Actualizá las lecturas y revisá antes de confirmar.');
      }
      return 'review';
    }
    if (!editing) {
      const attempt: CreateAttempt = { key: newRequestKey(), input };
      setCreateAttempt(meterId, attempt); setCreate(attempt);
      await create(attempt);
      return 'done';
    }
    const attempt: EditAttempt = { readingId: editing.id, version: editing.version };
    setEditAttempt(meterId, attempt); setEdit(attempt);
    const request = scope.begin('mutation');
    setBusy(true); setError(''); setNotice('');
    try {
      const result = await readingsApi.edit(meterId, editing.id, { ...input, version: editing.version, photo_action: photoAction }, request.signal);
      if (!request.isCurrent() || !active()) return 'review';
      clearEditAttempt(meterId, attempt); setEdit(undefined);
      setRows(current => current.map(row => row.id === result.id ? result : row).sort((a, b) => b.recorded_at.localeCompare(a.recorded_at)));
      setEditing(null); setRevision(n => n + 1); setNotice('Lectura corregida.');
    } catch (reason: unknown) {
      if (!request.isCurrent() || !active()) return 'review';
      if (definitelyRejected(reason) || (reason instanceof DiaryError && reason.code === 'DUPLICATE_READING')) {
        clearEditAttempt(meterId, attempt); setEdit(undefined); setError(errorMessage(reason));
      } else setError('La corrección puede haber cambiado. Consultá la versión actual antes de volver a guardar.');
    } finally { if (request.isCurrent() && active()) setBusy(false); }
    return 'done';
  }

  async function reconcile(attempt: EditAttempt) {
    const request = scope.begin('reconcile');
    setBusy(true); setError('');
    try {
      const result = await readingsApi.detail(meterId, attempt.readingId, request.signal);
      if (!request.isCurrent() || !active()) return;
      clearEditAttempt(meterId, attempt); setEdit(undefined);
      setRows(current => [result, ...current.filter(row => row.id !== result.id)].sort((a, b) => b.recorded_at.localeCompare(a.recorded_at)));
      setEditing(result); setRevision(n => n + 1);
      setNotice('Se cargó la versión actual. Revisá los datos antes de confirmar otra corrección.');
    } catch (reason: unknown) {
      if (request.isCurrent() && active()) setError(errorMessage(reason));
    } finally { if (request.isCurrent() && active()) setBusy(false); }
  }

  return <Card><CardHeader><CardTitle>Historial de lecturas</CardTitle></CardHeader><CardContent>
    <div className="space-y-3">
      {error && <Alert>{error}</Alert>}
      {notice && <Alert role="status">{notice}</Alert>}
      {createAttempt && <div className="space-y-2"><p role="status">Hay una creación sin resultado confirmado. El reintento usa los mismos datos y clave. No recargues la página hasta resolverla.</p>
        <Button type="button" disabled={busy} onClick={() => void create(createAttempt)}>Reintentar la misma creación</Button></div>}
      {editAttempt && <div className="space-y-2"><p role="status">Consultá la versión actual antes de volver a corregir. La solicitud anterior podría seguir procesándose.</p>
        <Button type="button" disabled={busy} onClick={() => void reconcile(editAttempt)}>Consultar versión actual</Button></div>}
      {!createAttempt && !editAttempt && <ReadingForm key={`${meterId}:${editing?.id ?? 'new'}:${editing?.version ?? 0}:${revision}`} reading={editing} rows={rows} meterId={meterId} busy={busy || loading || !historyReady} save={save} cancel={() => { setEditing(null); setRevision(n => n + 1); setError(''); }} />}
      <Button type="button" variant="outline" disabled={loading || busy} onClick={() => void refresh()}>Actualizar lecturas</Button>
      {loading && <p role="status">Cargando lecturas…</p>}
      {!loading && rows.length === 0 && !error && <p>No hay lecturas registradas.</p>}
      <p>Fechas y horas de Buenos Aires.</p>
      <ul className="space-y-2">{rows.map(row => <li key={row.id}>
        <span>{timestampFormatter.format(new Date(row.recorded_at))} — {row.value_kwh} kWh</span>
        <Button type="button" variant="outline" size="sm" disabled={busy || Boolean(createAttempt) || Boolean(editAttempt)} onClick={() => { setEditing(row); setRevision(n => n + 1); setError(''); setNotice(''); }}>Corregir lectura</Button>
        {row.has_photo && <Button type="button" variant="outline" size="sm" disabled={photoLoading} onClick={() => void showPhoto(row.id)}>Ver foto</Button>}
      </li>)}</ul>
      {photoLoading && <p role="status">Cargando foto…</p>}
      {photoUrl && <div><img src={photoUrl} alt="Foto de la lectura seleccionada" /><Button type="button" variant="outline" onClick={() => setPhotoUrl('')}>Cerrar foto</Button></div>}
    </div>
  </CardContent></Card>;
}
