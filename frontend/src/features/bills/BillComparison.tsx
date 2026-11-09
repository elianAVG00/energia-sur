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

  return <section aria-label="Comparación con la factura" className="space-y-3 border-t border-border pt-4">
    <div className="flex flex-wrap items-center justify-between gap-2">
      <h3 className="text-lg font-semibold">Consumo registrado vs. facturado</h3>
      <Button type="button" variant="outline" size="sm" disabled={busy} onClick={onClose}>Cerrar comparación</Button>
    </div>
    <p className="text-sm text-muted-foreground">Período facturado: {periodStart} — {periodEnd}. Consumo facturado: {billedKwh} kWh. Se admiten lecturas hasta 7 días antes o después de cada extremo.</p>
    {error && <Alert>{error}</Alert>}
    {loading && <p role="status">Buscando lecturas compatibles…</p>}
    {!loading && unavailable && <Alert>No hay lecturas compatibles dentro de ±7 días de cada extremo del período. No se puede calcular la comparación.</Alert>}
    {!loading && !unavailable && sets && !result && <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-2">
        <label className="space-y-1">Lectura inicial (candidatas)
          <select className="min-h-10 w-full rounded-md border border-input bg-card px-3 py-2" value={startId} disabled={busy}
            onChange={event => { setStartId(event.target.value); setResult(null); setConfirmed(false); setError(''); }}>
            <option value="" disabled>Elegí la lectura inicial</option>
            {sets.start_candidates.map(row => <option key={row.reading_id} value={row.reading_id}>{row.local_date} — {row.value_kwh} kWh</option>)}
          </select>
        </label>
        <label className="space-y-1">Lectura final (candidatas)
          <select className="min-h-10 w-full rounded-md border border-input bg-card px-3 py-2" value={endId} disabled={busy}
            onChange={event => { setEndId(event.target.value); setResult(null); setConfirmed(false); setError(''); }}>
            <option value="" disabled>Elegí la lectura final</option>
            {sets.end_candidates.map(row => <option key={row.reading_id} value={row.reading_id}>{row.local_date} — {row.value_kwh} kWh</option>)}
          </select>
        </label>
      </div>
      {startCandidate && endCandidate && !exact && <div className="space-y-2">
        <Alert>Las fechas de las lecturas (inicio {startCandidate.local_date}, fin {endCandidate.local_date}) no coinciden exactamente con el período facturado ({periodStart} a {periodEnd}).</Alert>
        <label className="flex items-start gap-2"><input type="checkbox" checked={confirmed} disabled={busy}
          onChange={event => { setConfirmed(event.target.checked); setError(''); }} />Confirmo que quiero comparar con estas fechas aproximadas.</label>
      </div>}
      {startCandidate && endCandidate && exact && <p className="text-sm">Las lecturas coinciden exactamente con los extremos del período facturado.</p>}
      <Button type="button" disabled={busy || !startCandidate || !endCandidate || startId === endId || (!exact && !confirmed)} onClick={submit}>Calcular comparación</Button>
      {busy && <p role="status">Calculando…</p>}
    </div>}
    {result && <div className="space-y-2">
      {result.status === 'no_comparison' ? <Alert>No se calculó la comparación porque la lectura final es menor que la lectura inicial.</Alert> : <>
        <p>Lectura inicial: {result.start_reading?.local_date} — {result.start_reading?.value_kwh} kWh</p>
        <p>Lectura final: {result.end_reading?.local_date} — {result.end_reading?.value_kwh} kWh</p>
        <p>Consumo registrado: {result.recorded_kwh} kWh</p>
        <p>Consumo facturado: {result.billed_kwh} kWh</p>
        <p>Diferencia: {result.difference_kwh} kWh</p>
        <p>{outcomeText(result.outcome)}</p>
        {!result.exact && <Alert>Comparación aproximada: las fechas de las lecturas no coinciden exactamente con el período facturado.</Alert>}
      </>}
      <Button type="button" variant="outline" size="sm" disabled={busy} onClick={() => { setResult(null); setError(''); }}>Volver a elegir lecturas</Button>
    </div>}
  </section>;
}
