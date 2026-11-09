import { useCallback, useEffect, useState } from 'react';
import { Alert } from '../../components/ui/alert.tsx';
import { Button } from '../../components/ui/button.tsx';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card.tsx';
import { DiaryError, errorMessage } from '../../lib/httpError.ts';
import type { BillWarning } from '../../lib/httpError.ts';
import { sessionStore } from '../../stores/session.ts';
import { useRequestScope } from '../../useRequestScope.ts';
import { newRequestKey } from '../readings/attempts.ts';
import { billsApi, validDate, validDecimal } from './api.ts';
import type { Bill, BillEdit, BillInput } from './api.ts';
import { BillComparison } from './BillComparison.tsx';

type CreateAttempt = { input: BillInput; key: string };
type EditAttempt = { id: string; version: number };
const creates = new Map<string, CreateAttempt>();
const edits = new Map<string, EditAttempt>();
let generation = sessionStore.getState().generation;
sessionStore.subscribe(state => {
  if (state.generation !== generation) { generation = state.generation; creates.clear(); edits.clear(); }
});
const empty = (): BillInput => ({ period_start: '', period_end: '', value_kwh: '', amount_ars: null, file_base64: null, overlap_token: null });
function rejected(reason: unknown): boolean {
  return reason instanceof DiaryError && reason.kind === 'http' && reason.status !== null &&
    ([400, 401, 403, 404, 413, 415, 422].includes(reason.status) ||
      (reason.status === 409 && ['DUPLICATE_BILL', 'VERSION_CONFLICT', 'OVERLAP_CONFIRMATION_REQUIRED', 'IDEMPOTENCY_KEY_REUSED'].includes(reason.code ?? '')));
}
async function encodeFile(file: File): Promise<string> {
  const bytes = new Uint8Array(await file.arrayBuffer());
  let binary = '';
  for (let offset = 0; offset < bytes.length; offset += 8192) binary += String.fromCharCode(...bytes.subarray(offset, offset + 8192));
  return btoa(binary);
}

export function BillHistory({ generation: sessionGeneration, domicileId, meterId }: { generation: number; domicileId: string; meterId: string }) {
  const scope = useRequestScope();
  const [rows, setRows] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [editing, setEditing] = useState<Bill | null>(null);
  const [detail, setDetail] = useState<Bill | null>(null);
  const [comparing, setComparing] = useState<Bill | null>(null);
  const [draft, setDraft] = useState<BillInput>(empty);
  const [fileName, setFileName] = useState('');
  const [fileProblem, setFileProblem] = useState(false);
  const [warning, setWarning] = useState<BillWarning | null>(null);
  const [createAttempt, setCreateAttempt] = useState(() => creates.get(meterId));
  const [editAttempt, setEditAttempt] = useState(() => edits.get(meterId));
  const active = useCallback(() => {
    const state = sessionStore.getState();
    return state.generation === sessionGeneration && state.selectedDomicileId === domicileId;
  }, [sessionGeneration, domicileId]);
  const refresh = useCallback(async () => {
    const request = scope.begin('bills');
    setLoading(true);
    try { const result = await billsApi.list(meterId, request.signal); if (request.isCurrent() && active()) setRows(result); }
    catch (reason: unknown) { if (request.isCurrent() && active()) setError(errorMessage(reason)); }
    finally { if (request.isCurrent() && active()) setLoading(false); }
  }, [scope, meterId, active]);
  useEffect(() => { void refresh(); }, [refresh]);

  function change(patch: Partial<BillInput>) { setDraft(current => ({ ...current, ...patch, overlap_token: null })); setWarning(null); setError(''); }
  async function selectFile(file: File | undefined) {
    const request = scope.begin('file-input');
    change({ file_base64: null }); setFileName(''); setFileProblem(false);
    if (!file) return;
    if (file.size === 0 || file.size > 5_000_000 || !['application/pdf', 'image/jpeg', 'image/png'].includes(file.type)) {
      setFileProblem(true); setError('Elegí un archivo PDF, JPG o PNG de hasta 5 MB.'); return;
    }
    setBusy(true);
    try {
      const data = await encodeFile(file);
      if (request.isCurrent() && active()) { change({ file_base64: data }); setFileName(file.name); }
    } catch { if (request.isCurrent() && active()) { setFileProblem(true); setError('No se pudo leer el archivo.'); } }
    finally { if (request.isCurrent() && active()) setBusy(false); }
  }
  function handleWarning(reason: unknown): boolean {
    if (!(reason instanceof DiaryError) || reason.code !== 'OVERLAP_CONFIRMATION_REQUIRED' || !reason.billWarning) return false;
    setWarning(reason.billWarning); setDraft(current => ({ ...current, overlap_token: reason.billWarning?.overlap_token ?? null }));
    setError('Revisá los períodos superpuestos antes de confirmar.'); return true;
  }
  async function create(attempt: CreateAttempt) {
    scope.begin('bills'); setLoading(false);
    const request = scope.begin('bill-mutation'); setBusy(true); setError(''); setNotice('');
    try {
      const row = await billsApi.create(meterId, attempt.input, attempt.key, request.signal);
      if (!request.isCurrent() || !active()) return;
      creates.delete(meterId); setCreateAttempt(undefined); setRows(current => [row, ...current.filter(item => item.id !== row.id)]);
      setDraft(empty()); setFileName(''); setFileProblem(false); setWarning(null); setNotice('Factura guardada.');
    } catch (reason: unknown) {
      if (!request.isCurrent() || !active()) return;
      if (rejected(reason)) {
        creates.delete(meterId); setCreateAttempt(undefined);
        if (!handleWarning(reason)) setError(errorMessage(reason));
      } else setError('No se confirmó la creación. Reintentá la misma solicitud con la misma clave antes de crear otra.');
    } finally { if (request.isCurrent() && active()) setBusy(false); }
  }
  async function save(confirmed: boolean) {
    if (busy || createAttempt || editAttempt) return;
    if (fileProblem || !validDate(draft.period_start) || !validDate(draft.period_end) || draft.period_start > draft.period_end || !validDecimal(draft.value_kwh, 3) || (draft.amount_ars !== null && !validDecimal(draft.amount_ars, 2)) || (!editing && !draft.file_base64)) {
      setError('Revisá las fechas, los valores y el archivo obligatorio.'); return;
    }
    if (warning && !confirmed) { setError('Confirmá explícitamente los períodos superpuestos.'); return; }
    const input = { ...draft, overlap_token: confirmed ? draft.overlap_token : null };
    if (!editing) {
      const attempt = { input, key: newRequestKey() }; creates.set(meterId, attempt); setCreateAttempt(attempt); await create(attempt); return;
    }
    const attempt = { id: editing.id, version: editing.version }; edits.set(meterId, attempt); setEditAttempt(attempt);
    const edit: BillEdit = { ...input, version: editing.version, file_action: input.file_base64 ? 'replace' : 'keep' };
    scope.begin('bills'); setLoading(false);
    const request = scope.begin('bill-mutation'); setBusy(true); setError(''); setNotice('');
    try {
      const row = await billsApi.edit(meterId, editing.id, edit, request.signal);
      if (!request.isCurrent() || !active()) return;
      edits.delete(meterId); setEditAttempt(undefined); setRows(current => current.map(item => item.id === row.id ? row : item));
      setEditing(null); setDraft(empty()); setFileName(''); setFileProblem(false); setWarning(null); setNotice('Factura corregida.');
    } catch (reason: unknown) {
      if (!request.isCurrent() || !active()) return;
      if (rejected(reason)) {
        edits.delete(meterId); setEditAttempt(undefined);
        if (reason instanceof DiaryError && reason.code === 'VERSION_CONFLICT') {
          edits.set(meterId, attempt); setEditAttempt(attempt); setError('La versión cambió. Consultá la versión actual antes de volver a guardar.');
        } else if (!handleWarning(reason)) setError(errorMessage(reason));
      } else setError('La corrección podría haberse guardado. Consultá la versión actual antes de volver a guardar.');
    } finally { if (request.isCurrent() && active()) setBusy(false); }
  }
  async function reconcile(attempt: EditAttempt) {
    const request = scope.begin('bill-reconcile'); setBusy(true); setError('');
    try {
      const row = await billsApi.detail(meterId, attempt.id, request.signal);
      if (!request.isCurrent() || !active()) return;
      edits.delete(meterId); setEditAttempt(undefined); setRows(current => [row, ...current.filter(item => item.id !== row.id)]);
      if (editing?.id !== row.id) {
        setDraft({ period_start: row.period_start, period_end: row.period_end, value_kwh: row.value_kwh, amount_ars: row.amount_ars, file_base64: null, overlap_token: null });
        setFileName(''); setFileProblem(false);
      } else setDraft(current => ({ ...current, overlap_token: null }));
      setEditing(row); setWarning(null); setNotice('Versión actual cargada. Revisá los datos antes de corregir. La solicitud anterior aún podría estar procesándose.');
    } catch (reason: unknown) { if (request.isCurrent() && active()) setError(errorMessage(reason)); }
    finally { if (request.isCurrent() && active()) setBusy(false); }
  }
  async function download(row: Bill) {
    const request = scope.begin('bill-file'); setBusy(true); setError('');
    try {
      const blob = await billsApi.file(meterId, row.id, request.signal);
      if (!request.isCurrent() || !active()) return;
      const url = URL.createObjectURL(blob);
      try { const link = document.createElement('a'); link.href = url; link.download = row.file_type === 'application/pdf' ? 'factura.pdf' : row.file_type === 'image/png' ? 'factura.png' : 'factura.jpg'; link.click(); }
      finally { URL.revokeObjectURL(url); }
    } catch (reason: unknown) { if (request.isCurrent() && active()) setError(errorMessage(reason)); }
    finally { if (request.isCurrent() && active()) setBusy(false); }
  }
  async function showDetail(row: Bill) {
    const request = scope.begin('bill-detail'); setBusy(true); setError(''); setDetail(null);
    try {
      const result = await billsApi.detail(meterId, row.id, request.signal);
      if (request.isCurrent() && active()) setDetail(result);
    } catch (reason: unknown) { if (request.isCurrent() && active()) setError(errorMessage(reason)); }
    finally { if (request.isCurrent() && active()) setBusy(false); }
  }
  function startEdit(row: Bill) {
    setEditing(row); setDraft({ period_start: row.period_start, period_end: row.period_end, value_kwh: row.value_kwh, amount_ars: row.amount_ars, file_base64: null, overlap_token: null });
    setFileName(''); setFileProblem(false); setWarning(null); setError(''); setNotice(''); setComparing(null);
  }
  const disabled = busy || Boolean(createAttempt) || Boolean(editAttempt);
  return <Card><CardHeader><CardTitle>Facturas del medidor</CardTitle></CardHeader><CardContent><div className="space-y-3">
    {error && <Alert>{error}</Alert>}{notice && <Alert role="status">{notice}</Alert>}
    {createAttempt && <div><p>Creación sin resultado confirmado. No recargues la página hasta resolverla.</p><Button type="button" disabled={busy} onClick={() => void create(createAttempt)}>Reintentar la misma creación</Button></div>}
    {editAttempt && <div><p>La corrección anterior podría seguir procesándose.</p><Button type="button" disabled={busy} onClick={() => void reconcile(editAttempt)}>Consultar versión actual</Button></div>}
    {!createAttempt && !editAttempt && <form className="space-y-2" onSubmit={event => { event.preventDefault(); void save(false); }}>
      <h3>{editing ? 'Corregir factura' : 'Registrar factura'}</h3>
      <label>Inicio del período <input type="date" required value={draft.period_start} disabled={disabled} onChange={event => change({ period_start: event.target.value })} /></label>{' '}
      <label>Fin del período <input type="date" required value={draft.period_end} disabled={disabled} onChange={event => change({ period_end: event.target.value })} /></label>{' '}
      <label>Consumo facturado (kWh) <input type="text" inputMode="decimal" required value={draft.value_kwh} disabled={disabled} onChange={event => change({ value_kwh: event.target.value })} /></label>{' '}
      <label>Importe (ARS, opcional) <input type="text" inputMode="decimal" value={draft.amount_ars ?? ''} disabled={disabled} onChange={event => change({ amount_ars: event.target.value || null })} /></label>{' '}
      <label>{editing ? 'Reemplazar archivo (opcional)' : 'Archivo obligatorio'} <input type="file" accept="application/pdf,image/jpeg,image/png" disabled={disabled} onChange={event => void selectFile(event.target.files?.[0])} /></label>
      {fileName && <p>Archivo seleccionado: {fileName}</p>}
      {editing && <p>Si no seleccionás otro archivo, se conserva el actual.</p>}
      <div><Button type="submit" disabled={disabled}>Guardar factura</Button>{editing && <Button type="button" variant="outline" disabled={disabled} onClick={() => { setEditing(null); setDraft(empty()); setFileName(''); setFileProblem(false); setWarning(null); }}>Cancelar corrección</Button>}</div>
      {warning && <div><p>{warning.overlaps.length ? 'Los siguientes períodos se superponen:' : 'Los períodos ya no se superponen. Revisá y confirmá el estado actual.'}</p><ul>{warning.overlaps.map(row => <li key={row.id}>{row.period_start} — {row.period_end} (versión {row.version})</li>)}</ul><Button type="button" disabled={disabled} onClick={() => void save(true)}>Confirmar superposición y guardar</Button></div>}
    </form>}
    <Button type="button" variant="outline" disabled={busy || loading} onClick={() => void refresh()}>Actualizar facturas</Button>
    {loading && <p role="status">Cargando facturas…</p>}
    {!loading && !rows.length && <p>No hay facturas registradas.</p>}
    <ul>{rows.map(row => <li key={row.id}><span>{row.period_start} — {row.period_end}: {row.value_kwh} kWh{row.amount_ars === null ? '' : ` — ARS ${row.amount_ars}`} (versión {row.version})</span>{' '}
      <Button type="button" variant="outline" size="sm" disabled={disabled} onClick={() => void showDetail(row)}>Ver detalle</Button>{' '}
      <Button type="button" variant="outline" size="sm" disabled={disabled} onClick={() => { setComparing(row); setError(''); setNotice(''); }}>Comparar</Button>{' '}
      <Button type="button" variant="outline" size="sm" disabled={disabled} onClick={() => startEdit(row)}>Corregir factura</Button>{' '}
      <Button type="button" variant="outline" size="sm" disabled={disabled} onClick={() => void download(row)}>Descargar archivo</Button></li>)}</ul>
    {comparing && <BillComparison key={`${meterId}:${comparing.id}`} generation={sessionGeneration} domicileId={domicileId} meterId={meterId} bill={comparing} onClose={() => setComparing(null)} />}
    {detail && <section aria-label="Detalle de factura"><p>Período: {detail.period_start} — {detail.period_end}</p><p>Consumo: {detail.value_kwh} kWh</p><p>Importe: {detail.amount_ars === null ? 'No informado' : `ARS ${detail.amount_ars}`}</p><p>Archivo: {detail.file_type} — versión {detail.version}</p><Button type="button" variant="outline" onClick={() => setDetail(null)}>Cerrar detalle</Button></section>}
  </div></CardContent></Card>;
}
