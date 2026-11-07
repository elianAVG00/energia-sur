export const HEALTH_TIMEOUT_MS = 5_000;

export interface HealthResponse {
  status: 'ok';
}

type HealthErrorKind = 'http' | 'invalid-response' | 'network' | 'timeout' | 'aborted';

export class HealthError extends Error {
  readonly kind: HealthErrorKind;

  constructor(kind: HealthErrorKind, message: string, cause?: unknown) {
    super(message, { cause });
    this.name = 'HealthError';
    this.kind = kind;
  }
}

interface HealthRequestOptions {
  signal: AbortSignal;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
}

function isHealthResponse(body: unknown): body is HealthResponse {
  return (
    typeof body === 'object' &&
    body !== null &&
    'status' in body &&
    body.status === 'ok' &&
    Object.keys(body).length === 1
  );
}

export async function fetchHealth({
  signal,
  fetchImpl = fetch,
  timeoutMs = HEALTH_TIMEOUT_MS,
}: HealthRequestOptions): Promise<HealthResponse> {
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort();

  signal.addEventListener('abort', abort, { once: true });
  if (signal.aborted) controller.abort();

  const timeout = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);

  try {
    controller.signal.throwIfAborted();
    const response = await fetchImpl('/api/health', {
      cache: 'no-store',
      signal: controller.signal,
    });

    if (response.status !== 200) {
      throw new HealthError('http', `La API respondió con HTTP ${response.status}.`);
    }

    if (!/^application\/json(?:\s*;|$)/i.test(response.headers.get('content-type') ?? '')) {
      throw new HealthError('invalid-response', 'La API no devolvió una respuesta JSON.');
    }

    let body: unknown;
    try {
      body = await response.json();
    } catch (error: unknown) {
      throw new HealthError('invalid-response', 'La API devolvió un JSON inválido.', error);
    }

    controller.signal.throwIfAborted();
    if (!isHealthResponse(body)) {
      throw new HealthError('invalid-response', 'La respuesta de la API no tiene el formato esperado.');
    }

    return body;
  } catch (error: unknown) {
    if (signal.aborted) {
      throw new HealthError('aborted', 'La comprobación fue cancelada.', error);
    }
    if (timedOut) {
      throw new HealthError('timeout', 'La API no respondió dentro del tiempo límite.', error);
    }
    if (error instanceof HealthError) throw error;
    throw new HealthError('network', 'No se pudo conectar con la API.', error);
  } finally {
    clearTimeout(timeout);
    signal.removeEventListener('abort', abort);
  }
}
