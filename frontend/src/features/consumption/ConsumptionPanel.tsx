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
const BASE_TIME = new Intl.DateTimeFormat('es-AR', {
  timeZone: 'America/Argentina/Buenos_Aires',
  dateStyle: 'medium',
  timeStyle: 'short',
});

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
  return <ul aria-label={`Gráfico de ${unit}`} className="space-y-2">
    {labels.map((label, index) => {
      const raw = values[index];
      if (raw === null) {
        return <li key={label} className="text-sm text-muted-foreground">{label}: no calculable</li>;
      }
      const width = Math.min(100, Math.max(2, Math.round((Number(raw) / maximum) * 100)));
      return <li key={label} className="grid min-w-0 gap-1.5 sm:grid-cols-[10rem_minmax(0,1fr)_auto] sm:items-center sm:gap-3">
        <span className="break-words text-sm">{label}</span>
        <div className="h-3 w-full overflow-hidden rounded-sm bg-muted" aria-hidden="true">
          <div className="h-full rounded-sm bg-primary" style={{ width: `${width}%` }} />
        </div>
        <span className="text-sm tabular-nums">{raw} {unit}</span>
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

  return <Card><CardHeader><CardTitle>Consumo del medidor</CardTitle></CardHeader><CardContent>
    <div className="space-y-6">
      <section aria-labelledby="consumption-filters-heading" className="space-y-3 border-b border-border pb-5">
        <h3 id="consumption-filters-heading" className="text-lg font-semibold">Período de consulta</h3>
        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] sm:items-end">
          <div className="grid min-w-0 gap-1.5">
            <Label htmlFor="consumption-from">Desde</Label>
            <input id="consumption-from" className="min-h-10 w-full min-w-0 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50" type="date" value={from} onChange={event => setFrom(event.target.value)} />
          </div>
          <div className="grid min-w-0 gap-1.5">
            <Label htmlFor="consumption-to">Hasta</Label>
            <input id="consumption-to" className="min-h-10 w-full min-w-0 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50" type="date" value={to} onChange={event => setTo(event.target.value)} />
          </div>
          <Button type="button" variant="outline" className="w-full sm:w-auto" disabled={loading} onClick={() => void refresh()}>Actualizar consumo</Button>
        </div>
      </section>
      {error && <Alert>{error}</Alert>}
      {loading && <p role="status">Cargando consumo…</p>}
      {!loading && intervals.length === 0 && !error && <p className="rounded-md border border-dashed border-border bg-muted/30 p-4 text-sm text-muted-foreground">No hay suficientes lecturas para mostrar la evolución.</p>}
      {intervals.length > 0 && <>
        <section aria-labelledby="consumption-real-heading" className="space-y-4 border-b border-border pb-5">
          <div>
            <h3 id="consumption-real-heading" className="text-lg font-semibold">Consumo real (kWh)</h3>
            <p className="text-sm text-muted-foreground">Consumo de cada intervalo entre lecturas, en kWh.</p>
          </div>
          <div className="space-y-4 rounded-md border border-border bg-background p-3 sm:p-4">
            <Bars labels={labels} values={consumption} unit="kWh" />
            <Table>
              <TableHeader><TableRow><TableHead>Intervalo</TableHead><TableHead>Consumo</TableHead></TableRow></TableHeader>
              <TableBody>{intervals.map((item, index) => <TableRow key={`${item.start_reading_id}-${item.end_reading_id}`}>
                <TableCell className="whitespace-nowrap">{labels[index]}</TableCell>
                <TableCell>{item.calculable ? `${item.consumption_kwh} kWh` : 'no calculable'}{item.calculable && item.sub_day ? ' — poco representativo' : ''}</TableCell>
              </TableRow>)}</TableBody>
            </Table>
          </div>
        </section>
        <section aria-labelledby="consumption-average-heading" className="space-y-4 border-b border-border pb-5">
          <div>
            <h3 id="consumption-average-heading" className="text-lg font-semibold">Promedio diario (kWh/día)</h3>
            <p className="text-sm text-muted-foreground">Promedio de cada intervalo, en kWh/día.</p>
          </div>
          <div className="space-y-4 rounded-md border border-border bg-background p-3 sm:p-4">
            <Bars labels={labels} values={dailyAverage} unit="kWh/día" />
            <Table>
              <TableHeader><TableRow><TableHead>Intervalo</TableHead><TableHead>Promedio diario</TableHead></TableRow></TableHeader>
              <TableBody>{intervals.map((item, index) => <TableRow key={`${item.start_reading_id}-${item.end_reading_id}`}>
                <TableCell className="whitespace-nowrap">{labels[index]}</TableCell>
                <TableCell>{item.calculable ? `${displayKwh(item.daily_average_kwh_day ?? '0', item.below_minimum)} kWh/día` : 'no calculable'}</TableCell>
              </TableRow>)}</TableBody>
            </Table>
          </div>
        </section>
      </>}
      <section aria-labelledby="consumption-estimate-heading" className="space-y-4 rounded-md border border-primary/20 bg-primary/5 p-4 sm:p-5">
        <div>
          <h3 id="consumption-estimate-heading" className="text-lg font-semibold">Estimación</h3>
          <p className="text-sm text-muted-foreground">Proyección basada en el último intervalo válido.</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
          <div className="grid min-w-0 gap-1.5">
            <Label htmlFor="consumption-days">Días a estimar (1–90)</Label>
            <input id="consumption-days" className="min-h-10 w-full min-w-0 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50" type="number" min={1} max={90} value={days} onChange={event => setDays(event.target.value)} />
          </div>
          <Button type="button" className="w-full sm:w-auto" disabled={busy} onClick={() => void requestEstimate()}>Estimar</Button>
        </div>
        {busy && <p role="status">Calculando estimación…</p>}
        {estimate && (estimate.status === 'base_unavailable'
          ? <p className="rounded-md border border-amber-500/40 bg-amber-500/5 p-3 text-sm" role="status">{estimate.reason === 'decreasing_latest'
            ? 'No se estima porque la última lectura es menor que la anterior.'
            : 'No hay suficientes lecturas para estimar.'}</p>
          : <section aria-label="Resultado de la estimación" className="space-y-3 rounded-md border border-primary/20 bg-background p-4">
            <h4 className="font-semibold">Resultado de la estimación</h4>
            <div className="grid gap-3 sm:grid-cols-2">
              <p className="text-lg font-semibold">Estimación a {estimate.days} días: {displayKwh(estimate.estimate_kwh, estimate.below_minimum)} kWh</p>
              <p className="font-medium">Promedio diario usado: {displayKwh(estimate.daily_average_kwh_day, estimate.daily_average_below_minimum)} kWh/día</p>
              <p className="text-sm sm:col-span-2"><span className="text-muted-foreground">Intervalo considerado: </span><span className="font-medium">{BASE_TIME.format(new Date(estimate.base_start_at))} — {BASE_TIME.format(new Date(estimate.base_end_at))} (Buenos Aires)</span></p>
            </div>
            {estimate.sub_day && <p className="rounded-md border border-amber-500/40 bg-amber-500/5 p-3 text-sm">El intervalo base es menor a 24 horas: poco representativo.</p>}
            <p className="text-sm font-medium">{ORIENTATIVE}</p>
          </section>)}
      </section>
    </div>
  </CardContent></Card>;
}
