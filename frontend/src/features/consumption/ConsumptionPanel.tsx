import { useCallback, useEffect, useState } from 'react';
import { Alert } from '../../components/ui/alert.tsx';
import { Button } from '../../components/ui/button.tsx';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card.tsx';
import { Label } from '../../components/ui/label.tsx';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table.tsx';
import { errorMessage } from '../../lib/httpError.ts';
import { sessionStore } from '../../stores/session.ts';
import { useRequestScope } from '../../useRequestScope.ts';
import { consumptionApi } from './api.ts';
import type { ConsumptionEstimate, ConsumptionEvolution } from './api.ts';
import { displayKwh } from './format.ts';

const ORIENTATIVE = 'Estimación orientativa, no facturada.';

function scale(values: (string | null)[]): number {
  let max = 0;
  for (const raw of values) {
    if (raw === null) continue;
    const number = Number(raw);
    if (Number.isFinite(number) && number > max) max = number;
  }
  return max || 1;
}

function Bars({ labels, values, unit }: { labels: string[]; values: (string | null)[]; unit: string }) {
  const maximum = scale(values);
  return <ul aria-label={`Gráfico de ${unit}`} className="space-y-1">
    {labels.map((label, index) => {
      const raw = values[index];
      if (raw === null) {
        return <li key={label} className="text-sm text-muted-foreground">{label}: no calculable</li>;
      }
      const width = Math.min(100, Math.max(2, Math.round((Number(raw) / maximum) * 100)));
      return <li key={label} className="flex items-center gap-2">
        <span className="w-40 shrink-0 text-sm">{label}</span>
        <div className="h-4 rounded-sm bg-primary" style={{ width: `${width}%` }} role="img" aria-label={`${raw} ${unit}`} />
        <span className="text-sm">{raw} {unit}</span>
      </li>;
    })}
  </ul>;
}

export function ConsumptionPanel({ generation, domicileId, meterId }: {
  generation: number; domicileId: string; meterId: string;
}) {
  const scope = useRequestScope();
  const [evolution, setEvolution] = useState<ConsumptionEvolution | null>(null);
  const [estimate, setEstimate] = useState<ConsumptionEstimate | null>(null);
  const [days, setDays] = useState('30');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const active = useCallback(() => {
    const state = sessionStore.getState();
    return state.generation === generation && state.selectedDomicileId === domicileId;
  }, [generation, domicileId]);

  const refresh = useCallback(async () => {
    const request = scope.begin('consumption-evolution');
    setLoading(true); setError('');
    try {
      const result = await consumptionApi.evolution(meterId, from, to, request.signal);
      if (request.isCurrent() && active()) setEvolution(result);
    } catch (reason: unknown) {
      if (request.isCurrent() && active()) setError(errorMessage(reason));
    } finally {
      if (request.isCurrent() && active()) setLoading(false);
    }
  }, [scope, meterId, from, to, active]);
  useEffect(() => { void refresh(); }, [refresh]);

  async function requestEstimate() {
    const parsed = Number(days);
    if (!Number.isInteger(parsed) || parsed < 1 || parsed > 90) {
      setError('Elegí un horizonte de 1 a 90 días.'); return;
    }
    const request = scope.begin('consumption-estimate');
    setBusy(true); setError(''); setEstimate(null);
    try {
      const result = await consumptionApi.estimate(meterId, parsed, request.signal);
      if (request.isCurrent() && active()) setEstimate(result);
    } catch (reason: unknown) {
      if (request.isCurrent() && active()) setError(errorMessage(reason));
    } finally {
      if (request.isCurrent() && active()) setBusy(false);
    }
  }

  const intervals = evolution?.intervals ?? [];
  const labels = intervals.map(item => `${item.start_local_date} → ${item.end_local_date}`);
  const consumption = intervals.map(item => item.calculable ? item.consumption_kwh : null);
  const dailyAverage = intervals.map(item => item.calculable ? displayKwh(item.daily_average_kwh_day ?? '0', item.below_minimum) : null);

  return <Card><CardHeader><CardTitle>Consumo y estimación</CardTitle></CardHeader><CardContent>
    <div className="space-y-4">
      {error && <Alert>{error}</Alert>}
      <div className="flex flex-wrap items-end gap-3">
        <div><Label htmlFor="consumption-from">Desde</Label>{' '}
          <input id="consumption-from" type="date" value={from} onChange={event => setFrom(event.target.value)} /></div>
        <div><Label htmlFor="consumption-to">Hasta</Label>{' '}
          <input id="consumption-to" type="date" value={to} onChange={event => setTo(event.target.value)} /></div>
        <Button type="button" variant="outline" disabled={loading} onClick={() => void refresh()}>Actualizar consumo</Button>
      </div>
      {loading && <p role="status">Cargando consumo…</p>}
      {!loading && intervals.length === 0 && !error && <p>No hay suficientes lecturas para mostrar la evolución.</p>}
      {intervals.length > 0 && <>
        <Card><CardHeader><CardTitle>Consumo real (kWh)</CardTitle></CardHeader><CardContent className="space-y-3">
          <Bars labels={labels} values={consumption} unit="kWh" />
          <Table>
            <TableHeader><TableRow><TableHead>Intervalo</TableHead><TableHead>Consumo</TableHead></TableRow></TableHeader>
            <TableBody>{intervals.map((item, index) => <TableRow key={`${item.start_reading_id}-${item.end_reading_id}`}>
              <TableCell className="whitespace-nowrap">{labels[index]}</TableCell>
              <TableCell>{item.calculable ? `${item.consumption_kwh} kWh` : 'no calculable'}{item.calculable && item.sub_day ? ' — poco representativo' : ''}</TableCell>
            </TableRow>)}</TableBody>
          </Table>
        </CardContent></Card>
        <Card><CardHeader><CardTitle>Promedio diario (kWh/día)</CardTitle></CardHeader><CardContent className="space-y-3">
          <Bars labels={labels} values={dailyAverage} unit="kWh/día" />
          <Table>
            <TableHeader><TableRow><TableHead>Intervalo</TableHead><TableHead>Promedio diario</TableHead></TableRow></TableHeader>
            <TableBody>{intervals.map((item, index) => <TableRow key={`${item.start_reading_id}-${item.end_reading_id}`}>
              <TableCell className="whitespace-nowrap">{labels[index]}</TableCell>
              <TableCell>{item.calculable ? `${displayKwh(item.daily_average_kwh_day ?? '0', item.below_minimum)} kWh/día` : 'no calculable'}</TableCell>
            </TableRow>)}</TableBody>
          </Table>
        </CardContent></Card>
      </>}
      <Card><CardHeader><CardTitle>Estimación</CardTitle></CardHeader><CardContent className="space-y-3">
        <div className="flex flex-wrap items-end gap-3">
          <div><Label htmlFor="consumption-days">Días a estimar (1–90)</Label>{' '}
            <input id="consumption-days" type="number" min={1} max={90} value={days} onChange={event => setDays(event.target.value)} /></div>
          <Button type="button" disabled={busy} onClick={() => void requestEstimate()}>Estimar</Button>
        </div>
        {estimate && (estimate.status === 'base_unavailable'
          ? <p>{estimate.reason === 'decreasing_latest'
            ? 'No se estima porque la última lectura es menor que la anterior.'
            : 'No hay suficientes lecturas para estimar.'}</p>
          : <section aria-label="Resultado de la estimación" className="space-y-1 border-t border-border pt-3">
            <p>Estimación a {estimate.days} días: {displayKwh(estimate.estimate_kwh, estimate.below_minimum)} kWh</p>
            <p>Promedio diario usado: {displayKwh(estimate.daily_average_kwh_day, estimate.daily_average_below_minimum)} kWh/día</p>
            {estimate.sub_day && <p>El intervalo base es menor a 24 horas: poco representativo.</p>}
            <p className="font-medium">{ORIENTATIVE}</p>
          </section>)}
      </CardContent></Card>
    </div>
  </CardContent></Card>;
}
