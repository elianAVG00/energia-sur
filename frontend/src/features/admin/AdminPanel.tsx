import { useEffect, useState } from 'react';
import { Alert } from '../../components/ui/alert.tsx';
import { Button } from '../../components/ui/button.tsx';
import { DiaryError, errorMessage } from '../../lib/httpError.ts';
import { useRequestScope } from '../../useRequestScope.ts';
import { adminApi } from './api.ts';
import type { IntervalSeconds, SourceKey, SourcesResult } from './api.ts';
import { SourceCard } from './SourceCard.tsx';
import type { BusyState, Feedback } from './SourceCard.tsx';
import { INTERVAL_OPTIONS, intervalLabel, isSuccessOutcome, outcomeLabel } from './state.ts';

const KEYS: readonly SourceKey[] = ['outages', 'scheduled_works'];
const EMPTY_BUSY: Record<SourceKey, BusyState> = {
  outages: { retry: false, save: false },
  scheduled_works: { retry: false, save: false },
};
const EMPTY_FEEDBACK: Record<SourceKey, Feedback | null> = {
  outages: null,
  scheduled_works: null,
};

function quiet(reason: unknown): boolean {
  return reason instanceof DiaryError && reason.kind === 'aborted';
}

function messageFor(reason: unknown, context: 'retry' | 'save' = 'retry'): string {
  if (reason instanceof DiaryError) {
    if (reason.code === 'SOURCE_BUSY') {
      return 'La fuente ya se está actualizando. Consultá el estado en unos segundos.';
    }
    if (reason.code === 'VERSION_CONFLICT') {
      return 'La configuración fue modificada por otro administrador. Se recargó el estado; no se sobrescribió el cambio.';
    }
    if (reason.status === 403) return 'No tenés autorización para administrar las fuentes.';
    if (reason.status === 422) return 'El intervalo seleccionado no es válido.';
    if (reason.kind === 'timeout') {
      return context === 'save'
        ? 'No se pudo confirmar si el cambio de intervalo se aplicó. Se consultó el estado real.'
        : 'No se pudo confirmar el resultado de la actualización. La operación puede continuar en el servidor; se consultó el estado real.';
    }
    if (reason.status === 401) return 'La sesión no es válida. Ingresá nuevamente.';
  }
  return errorMessage(reason);
}

function shouldReload(reason: unknown): boolean {
  return reason instanceof DiaryError && (
    reason.kind === 'timeout' || reason.code === 'SOURCE_BUSY' ||
    reason.code === 'VERSION_CONFLICT' || reason.status === 503
  );
}

export function AdminPanel() {
  const scope = useRequestScope();
  const [sources, setSources] = useState<SourcesResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<Record<SourceKey, IntervalSeconds | ''>>({
    outages: '', scheduled_works: '',
  });
  const [busy, setBusy] = useState<Record<SourceKey, BusyState>>(EMPTY_BUSY);
  const [feedback, setFeedback] = useState<Record<SourceKey, Feedback | null>>(EMPTY_FEEDBACK);

  function applyAll(data: SourcesResult): void {
    setSources(data);
    setSelected({
      outages: data.sources.find(source => source.key === 'outages')?.interval_seconds ?? '',
      scheduled_works:
        data.sources.find(source => source.key === 'scheduled_works')?.interval_seconds ?? '',
    });
  }

  function applyOne(data: SourcesResult, key: SourceKey): void {
    setSources(data);
    const source = data.sources.find(item => item.key === key);
    if (source) setSelected(previous => ({ ...previous, [key]: source.interval_seconds }));
  }

  function setFeedbackFor(key: SourceKey, value: Feedback | null): void {
    setFeedback(previous => ({ ...previous, [key]: value }));
  }

  async function loadAll(signal: AbortSignal): Promise<void> {
    setLoading(true);
    setError('');
    try {
      const data = await adminApi.sources(signal);
      if (!signal.aborted) applyAll(data);
    } catch (reason) {
      if (!signal.aborted && !quiet(reason)) setError(messageFor(reason));
    } finally {
      if (!signal.aborted) setLoading(false);
    }
  }

  useEffect(() => {
    const request = scope.begin('admin-sources');
    void loadAll(request.signal);
  }, [scope]);

  async function reloadOne(key: SourceKey, signal: AbortSignal): Promise<void> {
    try {
      const data = await adminApi.sources(signal);
      if (!signal.aborted) applyOne(data, key);
    } catch (reason) {
      if (!signal.aborted && !quiet(reason)) setError(messageFor(reason));
    }
  }

  async function retry(key: SourceKey): Promise<void> {
    const request = scope.begin(`admin-retry-${key}`);
    setBusy(previous => ({ ...previous, [key]: { ...previous[key], retry: true } }));
    setFeedbackFor(key, null);
    try {
      const data = await adminApi.refresh(key, request.signal);
      if (!request.isCurrent()) return;
      if (isSuccessOutcome(data.outcome)) {
        setFeedbackFor(key, {
          kind: 'success', action: 'retry',
          text: `Actualización completada: ${outcomeLabel(data.outcome)}.`,
        });
      } else {
        setFeedbackFor(key, {
          kind: 'warning', action: 'retry',
          text: `La actualización no fue exitosa: ${outcomeLabel(data.outcome)}` +
            `${data.detail_code ? ` (${data.detail_code})` : ''}. Se conserva la última actualización exitosa.`,
        });
      }
      await reloadOne(key, request.signal);
    } catch (reason) {
      if (!request.isCurrent() || quiet(reason)) return;
      setFeedbackFor(key, { kind: 'warning', action: 'retry', text: messageFor(reason) });
      if (shouldReload(reason)) await reloadOne(key, request.signal);
    } finally {
      if (request.isCurrent()) {
        setBusy(previous => ({ ...previous, [key]: { ...previous[key], retry: false } }));
      }
    }
  }

  async function save(key: SourceKey): Promise<void> {
    const current = sources?.sources.find(source => source.key === key);
    const value = selected[key];
    if (!current || value === '' || value === current.interval_seconds) return;
    const request = scope.begin(`admin-save-${key}`);
    setBusy(previous => ({ ...previous, [key]: { ...previous[key], save: true } }));
    setFeedbackFor(key, null);
    try {
      const data = await adminApi.setInterval(key, value, current.version, request.signal);
      if (!request.isCurrent()) return;
      setSources(previous => previous === null ? previous : {
        ...previous,
        sources: previous.sources.map(source => source.key === key
          ? { ...source, interval_seconds: data.interval_seconds, version: data.version }
          : source),
      });
      setSelected(previous => ({ ...previous, [key]: data.interval_seconds }));
      setFeedbackFor(key, {
        kind: 'success', action: 'save',
        text: `Intervalo actualizado a ${intervalLabel(data.interval_seconds)}.`,
      });
    } catch (reason) {
      if (!request.isCurrent() || quiet(reason)) return;
      setFeedbackFor(key, { kind: 'error', action: 'save', text: messageFor(reason, 'save') });
      if (shouldReload(reason)) await reloadOne(key, request.signal);
    } finally {
      if (request.isCurrent()) {
        setBusy(previous => ({ ...previous, [key]: { ...previous[key], save: false } }));
      }
    }
  }

  function select(key: SourceKey, value: string): void {
    const option = INTERVAL_OPTIONS.find(item => String(item.value) === value);
    if (option) setSelected(previous => ({ ...previous, [key]: option.value }));
  }

  return <div className="space-y-6">
    {error && <Alert>{error}</Alert>}
    {error && sources === null && !loading && <Button type="button" variant="outline"
      onClick={() => { const request = scope.begin('admin-sources'); void loadAll(request.signal); }}>
      Volver a intentar
    </Button>}
    {loading && <p role="status" className="text-sm text-muted-foreground">
      Cargando estado de las fuentes…
    </p>}
    {sources && <div className="grid items-start gap-6 lg:grid-cols-2">
      {KEYS.map(key => {
        const source = sources.sources.find(item => item.key === key);
        if (!source) return null;
        return <SourceCard key={key} source={source} selected={selected[key]}
          busy={busy[key] ?? EMPTY_BUSY[key]} feedback={feedback[key]}
          onSelect={value => select(key, value)}
          onSave={() => { void save(key); }}
          onRetry={() => { void retry(key); }} />;
      })}
    </div>}
  </div>;
}
