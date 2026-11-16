import { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert } from '../../components/ui/alert.tsx';
import { Button } from '../../components/ui/button.tsx';
import { errorMessage } from '../../lib/httpError.ts';
import { sessionStore } from '../../stores/session.ts';
import { useRequestScope } from '../../useRequestScope.ts';
import { comparisonsApi } from './comparison.ts';
import type { CandidateSets, ComparisonResult } from './comparison.ts';
import type { Bill } from './api.ts';

function outcomeText(outcome: ComparisonResult['outcome']): string {
  switch (outcome) {
    case 'recorded_higher': return 'El consumo registrado es mayor que el facturado.';
    case 'billed_higher': return 'El consumo facturado es mayor que el registrado.';
    case 'equal': return 'No hay diferencia entre el consumo registrado y el facturado.';
    default: return '';
  }
}

export function BillComparison({ generation, domicileId, meterId, bill, onClose }: {
  generation: number; domicileId: string; meterId: string; bill: Bill; onClose: () => void;
}) {
  const scope = useRequestScope();
  const [sets, setSets] = useState<CandidateSets | null>(null);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [startId, setStartId] = useState('');
  const [endId, setEndId] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const active = useCallback(() => {
    const state = sessionStore.getState();
    return state.generation === generation && state.selectedDomicileId === domicileId;
  }, [generation, domicileId]);
  const failed = useCallback((reason: unknown) => {
    if (active()) setError(errorMessage(reason));
  }, [active]);

  const compare = useCallback(async (start: string, end: string, approximate: boolean) => {
    const request = scope.begin('comparison');
    setBusy(true); setError('');
    try {
      const value = await comparisonsApi.compare(meterId, bill.id, start, end, approximate, request.signal);
      if (request.isCurrent() && active()) setResult(value);
    } catch (reason: unknown) {
      if (request.isCurrent() && active()) failed(reason);
    } finally {
      if (request.isCurrent() && active()) setBusy(false);
    }
  }, [scope, meterId, bill.id, active, failed]);

  useEffect(() => {
    const request = scope.begin('comparison-candidates');
    setLoading(true); setError(''); setResult(null);
    void comparisonsApi.candidates(meterId, bill.id, request.signal).then(value => {
      if (!request.isCurrent() || !active()) return;
      setSets(value);
      setLoading(false);
      const onlyStart = value.start_candidates.length === 1 ? value.start_candidates[0] : undefined;
      const onlyEnd = value.end_candidates.length === 1 ? value.end_candidates[0] : undefined;
      if (onlyStart && onlyEnd && onlyStart.local_date === value.period_start && onlyEnd.local_date === value.period_end) {
        setStartId(onlyStart.reading_id); setEndId(onlyEnd.reading_id);
        void compare(onlyStart.reading_id, onlyEnd.reading_id, false);
        return;
      }
      setStartId(value.start_candidates.length === 1 ? (value.start_candidates[0]?.reading_id ?? '') : '');
      setEndId(value.end_candidates.length === 1 ? (value.end_candidates[0]?.reading_id ?? '') : '');
    }).catch((reason: unknown) => {
      if (request.isCurrent() && active()) { failed(reason); setLoading(false); }
    });
  }, [scope, meterId, bill, active, compare, failed]);

  const startCandidate = useMemo(() => sets?.start_candidates.find(row => row.reading_id === startId) ?? null, [sets, startId]);
  const endCandidate = useMemo(() => sets?.end_candidates.find(row => row.reading_id === endId) ?? null, [sets, endId]);
  const periodStart = sets?.period_start ?? bill.period_start;
  const periodEnd = sets?.period_end ?? bill.period_end;
  const billedKwh = sets?.billed_kwh ?? bill.value_kwh;
  const exact = Boolean(startCandidate && endCandidate &&
    startCandidate.local_date === periodStart && endCandidate.local_date === periodEnd);
  const candidateIds = new Set([
    ...(sets?.start_candidates ?? []).map(row => row.reading_id),
    ...(sets?.end_candidates ?? []).map(row => row.reading_id),
  ]);
  const unavailable = Boolean(sets && (sets.start_candidates.length === 0 ||
    sets.end_candidates.length === 0 || candidateIds.size < 2));

  function submit() {
    if (!startCandidate || !endCandidate) { setError('Elegí una lectura inicial y una final.'); return; }
    if (startId === endId) { setError('Elegí lecturas distintas para el inicio y el fin.'); return; }
    if (!exact && !confirmed) { setError('Confirmá que las fechas de las lecturas difieren del período facturado.'); return; }
    void compare(startId, endId, !exact);
  }

  return <section aria-label="Comparación con la factura" className="space-y-4 rounded-lg border border-border bg-muted/30 p-4 sm:p-5">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h3 className="text-lg font-semibold">Consumo registrado vs. facturado</h3>
        <p className="mt-1 text-sm text-muted-foreground">Factura seleccionada</p>
      </div>
      <Button type="button" variant="outline" size="sm" disabled={busy} onClick={onClose}>Cerrar comparación</Button>
    </div>
    <dl className="grid gap-3 rounded-md border border-border bg-background p-3 text-sm sm:grid-cols-2">
      <div><dt className="text-muted-foreground">Período facturado</dt><dd className="font-medium">{periodStart} — {periodEnd}</dd></div>
      <div><dt className="text-muted-foreground">Consumo facturado</dt><dd className="font-medium">{billedKwh} kWh</dd></div>
    </dl>
    <p className="text-sm text-muted-foreground">Se admiten lecturas hasta 7 días antes o después de cada extremo.</p>
    {error && <Alert>{error}</Alert>}
    {loading && <p role="status">Buscando lecturas compatibles…</p>}
    {!loading && unavailable && <Alert>No hay lecturas compatibles dentro de ±7 días de cada extremo del período. No se puede calcular la comparación.</Alert>}
    {!loading && !unavailable && sets && !result && <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-2">
        <label className="grid min-w-0 gap-1.5 text-sm font-medium">Lectura inicial (candidatas)
          <select className="min-h-10 w-full min-w-0 rounded-md border border-input bg-background px-3 py-2 font-normal focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50" value={startId} disabled={busy}
            onChange={event => { setStartId(event.target.value); setResult(null); setConfirmed(false); setError(''); }}>
            <option value="" disabled>Elegí la lectura inicial</option>
            {sets.start_candidates.map(row => <option key={row.reading_id} value={row.reading_id}>{row.local_date} — {row.value_kwh} kWh</option>)}
          </select>
        </label>
        <label className="grid min-w-0 gap-1.5 text-sm font-medium">Lectura final (candidatas)
          <select className="min-h-10 w-full min-w-0 rounded-md border border-input bg-background px-3 py-2 font-normal focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50" value={endId} disabled={busy}
            onChange={event => { setEndId(event.target.value); setResult(null); setConfirmed(false); setError(''); }}>
            <option value="" disabled>Elegí la lectura final</option>
            {sets.end_candidates.map(row => <option key={row.reading_id} value={row.reading_id}>{row.local_date} — {row.value_kwh} kWh</option>)}
          </select>
        </label>
      </div>
      {startCandidate && endCandidate && !exact && <div className="space-y-2 rounded-md border border-amber-500/50 bg-amber-500/5 p-3">
        <Alert>Las fechas de las lecturas (inicio {startCandidate.local_date}, fin {endCandidate.local_date}) no coinciden exactamente con el período facturado ({periodStart} a {periodEnd}).</Alert>
        <label className="flex items-start gap-2"><input type="checkbox" checked={confirmed} disabled={busy}
          onChange={event => { setConfirmed(event.target.checked); setError(''); }} />Confirmo que quiero comparar con estas fechas aproximadas.</label>
      </div>}
      {startCandidate && endCandidate && exact && <p className="text-sm">Las lecturas coinciden exactamente con los extremos del período facturado.</p>}
      <Button type="button" disabled={busy || !startCandidate || !endCandidate || startId === endId || (!exact && !confirmed)} onClick={submit}>Calcular comparación</Button>
      {busy && <p role="status">Calculando…</p>}
    </div>}
    {result && <div className="space-y-3 rounded-md border border-border bg-background p-4">
      <h4 className="font-semibold">Resultado de la comparación</h4>
      {result.status === 'no_comparison' ? <Alert>No se calculó la comparación porque la lectura final es menor que la lectura inicial.</Alert> : <>
        <div className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
          <p><span className="text-sm text-muted-foreground">Lectura inicial: </span><span className="font-medium">{result.start_reading?.local_date} — {result.start_reading?.value_kwh} kWh</span></p>
          <p><span className="text-sm text-muted-foreground">Lectura final: </span><span className="font-medium">{result.end_reading?.local_date} — {result.end_reading?.value_kwh} kWh</span></p>
          <p className="text-lg font-semibold">Consumo registrado: {result.recorded_kwh} kWh</p>
          <p className="text-lg font-semibold">Consumo facturado: {result.billed_kwh} kWh</p>
          <p className="text-lg font-semibold sm:col-span-2">Diferencia: {result.difference_kwh} kWh</p>
        </div>
        <p className="font-medium">{outcomeText(result.outcome)}</p>
        {!result.exact && <Alert>Comparación aproximada: las fechas de las lecturas no coinciden exactamente con el período facturado.</Alert>}
      </>}
      <Button type="button" variant="outline" size="sm" disabled={busy} onClick={() => { setResult(null); setError(''); }}>Volver a elegir lecturas</Button>
    </div>}
  </section>;
}
