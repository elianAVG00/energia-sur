export class DiaryError extends Error {
  readonly status: number | null;
  readonly kind: 'http' | 'network' | 'invalid-response' | 'aborted' | 'timeout';
  readonly code: 'DUPLICATE_METER' | 'VERSION_CONFLICT' | null;

  constructor(kind: DiaryError['kind'], message: string, status: number | null = null, code: DiaryError['code'] = null) {
    super(message);
    this.name = 'DiaryError';
    this.kind = kind;
    this.status = status;
    this.code = code;
  }
}

export function errorMessage(error: unknown): string {
  return error instanceof DiaryError ? error.message : 'No se pudo completar la operación. Intentá nuevamente.';
}

export function invalidResponse(): DiaryError {
  return new DiaryError('invalid-response', 'La API devolvió una respuesta con formato inesperado. Intentá actualizar.');
}

export function statusMessage(status: number): string {
  switch (status) {
    case 401: return 'La sesión venció. Ingresá nuevamente.';
    case 403: return 'No se pudo autorizar la solicitud. Cerrá la sesión e ingresá nuevamente.';
    case 404: return 'El recurso no está disponible.';
    case 409: return 'El registro fue modificado.';
    case 422: return 'Revisá los datos ingresados.';
    case 503: return 'El servicio no está disponible temporalmente. Intentá nuevamente.';
    default: return `No se pudo completar la solicitud (HTTP ${status}).`;
  }
}
