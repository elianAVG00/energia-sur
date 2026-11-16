import { useCallback, useEffect, useState } from 'react';
import { diaryApi, DiaryError, errorMessage } from '../../diaryApi.ts';
import type { Cut, CutInput, Period, Session, Summary } from '../../diaryApi.ts';
import { displayTimestamp } from '../../diaryState.ts';
import { useRequestScope } from '../../useRequestScope.ts';
import { sessionStore } from '../../stores/session.ts';
import { Alert } from '../../components/ui/alert.tsx';
import { Button } from '../../components/ui/button.tsx';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card.tsx';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../components/ui/table.tsx';
import { CloseForm, CutForm, PeriodForm } from './forms.tsx';
import { AccountSection } from '../account/AccountSection.tsx';

export function DiarySection({ session, generation, selected, onActivity }: {
  session: Session; generation: number; selected: string; onActivity: () => void;
}) {
  const scope = useRequestScope();
  const [cuts, setCuts] = useState<Cut[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [editing, setEditing] = useState<Cut | null>(null);
  const [closing, setClosing] = useState<Cut | null>(null);
  const [formRevision, setFormRevision] = useState(0);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [queriedPeriod, setQueriedPeriod] = useState<Period | null>(null);
  const [conflict, setConflict] = useState(false);
  const active = useCallback(() => {
    const state = sessionStore.getState();
    return state.generation === generation && state.selectedDomicileId === selected;
  }, [generation, selected]);
  const failed = useCallback((reason: unknown) => {
    if (!active()) return;
    if (reason instanceof DiaryError && reason.status === 401) sessionStore.getState().clearSession(generation, true);
    else {
      if (reason instanceof DiaryError && reason.status === 409) {
        setConflict(true);
        setError(errorMessage(reason));
      } else setError(errorMessage(reason));
    }
  }, [active, generation]);

  const refresh = useCallback(async () => {
    const request = scope.begin('cuts');
    setLoading(true);
    try {
      const rows = await diaryApi.cuts(selected, request.signal);
      if (request.isCurrent() && active()) setCuts(rows);
    } catch (reason: unknown) { if (request.isCurrent() && active()) failed(reason); }
    finally { if (request.isCurrent() && active()) setLoading(false); }
  }, [scope, active, failed, selected]);
  useEffect(() => { void refresh(); }, [refresh]);

  async function mutate(task: (signal: AbortSignal, isCurrent: () => boolean) => Promise<void>) {
    onActivity();
    const request = scope.begin('mutation');
    const isCurrent = () => request.isCurrent() && active();
    setBusy(true); setError(''); setNotice(''); setSummary(null);
    try {
      await task(request.signal, isCurrent);
      if (!isCurrent()) return;
      await refresh();
      if (isCurrent()) setNotice('Operación guardada.');
    } catch (reason: unknown) { if (isCurrent()) failed(reason); }
    finally { if (isCurrent()) setBusy(false); }
  }
  async function saveCut(input: CutInput) {
    await mutate(async (signal, isCurrent) => {
      if (editing) await diaryApi.correctCut(editing, input, session.csrf_token, signal);
      else await diaryApi.createCut(selected, input, session.csrf_token, signal);
      if (isCurrent()) { setEditing(null); setFormRevision(n => n + 1); setConflict(false); }
    });
  }
  async function closeCut(end: string) {
    if (!closing) return;
    await mutate(async (signal, isCurrent) => {
      await diaryApi.closeCut(closing, end, session.csrf_token, signal);
      if (isCurrent()) { setClosing(null); setConflict(false); }
    });
  }
  async function query(period: Period) {
    onActivity();
    const request = scope.begin('summary');
    setBusy(true); setError(''); setSummary(null);
    try {
      const result = await diaryApi.summary(selected, period, request.signal);
      if (request.isCurrent() && active()) { setSummary(result); setQueriedPeriod(period); }
    } catch (reason: unknown) { if (request.isCurrent() && active()) failed(reason); }
    finally { if (request.isCurrent() && active()) setBusy(false); }
  }
  async function download() {
    if (!queriedPeriod) return;
    onActivity();
    const request = scope.begin('pdf');
    setBusy(true); setError('');
    try {
      const blob = await diaryApi.pdf(selected, queriedPeriod, request.signal);
      if (!request.isCurrent() || !active()) return;
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url; link.download = 'interruption-diary.pdf'; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (reason: unknown) { if (request.isCurrent() && active()) failed(reason); }
    finally { if (request.isCurrent() && active()) setBusy(false); }
  }
  async function discardConflict() {
    onActivity();
    const request = scope.begin('discard');
    setBusy(true);
    try {
      const rows = await diaryApi.cuts(selected, request.signal);
      if (!request.isCurrent() || !active()) return;
      setCuts(rows);
      if (editing) setEditing(rows.find(row => row.id === editing.id) ?? null);
      if (closing) setClosing(rows.find(row => row.id === closing.id && row.status === 'ongoing') ?? null);
      // Revision must advance even when the server returns the same record version.
      setFormRevision(n => n + 1); setConflict(false); setError('');
      setNotice('Borrador descartado. Revisá la versión actual antes de guardar.');
    } catch (reason: unknown) { if (request.isCurrent() && active()) failed(reason); }
    finally { if (request.isCurrent() && active()) setBusy(false); }
  }

  return <AccountSection id="cortes" title="Cortes e interrupciones"
    description="Registrá tus cortes, corregilos, cerralos y descargá el resumen del período.">
    <Card>
      <CardHeader><CardTitle>Diario personal de interrupciones</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-6">
          {error && <Alert>{error}</Alert>}
          {conflict && <Button type="button" variant="outline" disabled={busy} onClick={() => void discardConflict()}>Descartar borrador y recargar</Button>}
          {notice && <Alert role="status">{notice}</Alert>}
          <section aria-labelledby="diary-register-heading" className="space-y-4 border-b border-border pb-6">
            <div>
              <h3 id="diary-register-heading" className="text-lg font-semibold">{editing ? 'Corregir interrupción' : 'Registrar interrupción'}</h3>
              <p className="text-sm text-muted-foreground">Fechas y horas de Buenos Aires, con precisión de minutos.</p>
            </div>
            <CutForm key={`${selected}:${editing?.id ?? 'new'}:${editing?.version ?? 0}:${formRevision}`} cut={editing} busy={busy} save={saveCut} cancel={() => { setEditing(null); setConflict(false); setFormRevision(n => n + 1); }} />
          </section>
          <section aria-labelledby="diary-history-heading" className="space-y-4 border-b border-border pb-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 id="diary-history-heading" className="text-lg font-semibold">Historial de interrupciones</h3>
                <p className="text-sm text-muted-foreground">Registros del domicilio seleccionado.</p>
              </div>
              <Button type="button" variant="outline" disabled={busy || loading} onClick={() => { setError(''); void refresh(); }}>Actualizar cortes</Button>
            </div>
            {loading && <p role="status">Cargando cortes…</p>}
            {!loading && cuts.length === 0 ? <p className="rounded-md border border-dashed border-border bg-muted/30 p-4 text-sm text-muted-foreground">No hay cortes registrados.</p> : cuts.length > 0 && <Table className="min-w-[58rem]">
              <TableHeader><TableRow><TableHead>Inicio</TableHead><TableHead>Fin</TableHead><TableHead>Estado</TableHead><TableHead>Observaciones</TableHead><TableHead>Reclamo</TableHead><TableHead>Acciones</TableHead></TableRow></TableHeader>
              <TableBody>{cuts.map(cut => <TableRow key={cut.id}>
                <TableCell className="whitespace-nowrap">{displayTimestamp(cut.start_at)}</TableCell><TableCell className="whitespace-nowrap">{cut.end_at ? displayTimestamp(cut.end_at) : 'En curso'}</TableCell><TableCell>{cut.status === 'ongoing' ? 'En curso' : 'Cerrado'}</TableCell><TableCell>{cut.observations}</TableCell><TableCell>{cut.complaint_number}</TableCell>
                <TableCell><div className="flex flex-wrap gap-2"><Button type="button" variant="outline" size="sm" disabled={busy} onClick={() => { setClosing(null); setEditing(cut); setConflict(false); setError(''); setNotice(''); setFormRevision(n => n + 1); }}>Corregir</Button>
                  {cut.status === 'ongoing' && <Button type="button" variant="outline" size="sm" disabled={busy} onClick={() => { setEditing(null); setClosing(cut); setConflict(false); setError(''); setNotice(''); setFormRevision(n => n + 1); }}>Cerrar corte</Button>}
                </div></TableCell>
              </TableRow>)}</TableBody>
            </Table>}
          </section>
          {closing && <section aria-labelledby="diary-close-heading" className="space-y-4 border-b border-border pb-6">
            <h3 id="diary-close-heading" className="text-lg font-semibold">Corregir y cerrar interrupciones</h3>
            <div className="rounded-lg border border-border bg-muted/20 p-4">
              <CloseForm key={`${selected}:${closing.id}:${closing.version}:${formRevision}`} cut={closing} busy={busy} save={closeCut} cancel={() => setClosing(null)} />
            </div>
          </section>}
          <section aria-labelledby="diary-summary-heading" className="space-y-4 rounded-lg border border-primary/20 bg-primary/5 p-4 sm:p-5">
            <div>
              <h3 id="diary-summary-heading" className="text-lg font-semibold">Resumen por período</h3>
              <p className="text-sm text-muted-foreground">Consultá el tiempo sin suministro dentro del intervalo elegido.</p>
            </div>
            <PeriodForm busy={busy} query={query} changed={() => { setSummary(null); setQueriedPeriod(null); }} />
            {summary && <section aria-label="Resultado del resumen" className="space-y-3 rounded-md border border-border bg-background p-4">
              <h4 className="text-lg font-semibold">Total sin servicio: {summary.total_hours} h {summary.remaining_minutes} min</h4>
              <p>{summary.entries.length} registros con duración dentro del período. El tiempo superpuesto se cuenta una sola vez.</p>
              <p>Generado: {displayTimestamp(summary.generated_at)} (Buenos Aires)</p>
              <Button type="button" className="w-full sm:w-auto" disabled={busy} onClick={() => void download()}>Descargar PDF</Button>
            </section>}
          </section>
          {busy && <p role="status">Procesando…</p>}
        </div>
      </CardContent>
    </Card>
  </AccountSection>;
}
