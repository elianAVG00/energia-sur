import axios from 'axios';
import type { AxiosAdapter, AxiosResponse, GenericAbortSignal } from 'axios';
import { sessionStore } from '../stores/session.ts';
import type { SessionStore } from '../stores/session.ts';
import { DiaryError, statusMessage } from './httpError.ts';

type Method = 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';
interface RequestOptions {
  method?: Method;
  data?: unknown;
  responseType?: 'json' | 'blob';
  // Logout alone may use a captured token after immediate local session clearing.
  logoutToken?: string;
}
interface Context {
  generation: number;
  logoutToken: string | undefined;
  caller: AbortSignal;
  deadline: AbortSignal;
  combined: AbortSignal;
}

function cancellation(context: Context): DiaryError {
  return context.caller.aborted || !context.deadline.aborted
    ? new DiaryError('aborted', 'La solicitud fue cancelada.')
    : new DiaryError('timeout', 'La solicitud tardó demasiado. Intentá nuevamente.');
}

function readErrorBlob(blob: Blob, context: Context): Promise<string> {
  return new Promise((resolve, reject) => {
    const abort = () => reject(cancellation(context));
    if (context.combined.aborted) { abort(); return; }
    context.combined.addEventListener('abort', abort, { once: true });
    void blob.text().then(
      text => { context.combined.removeEventListener('abort', abort); resolve(text); },
      error => { context.combined.removeEventListener('abort', abort); reject(error); },
    );
  });
}

function hasControlOrSpace(value: string): boolean {
  return [...value].some(character => character.charCodeAt(0) <= 32);
}

export function apiPath(path: string): string {
  if (!path.startsWith('/') || path.startsWith('//') || path.includes('\\') || path.includes('#') || hasControlOrSpace(path)) {
    throw new DiaryError('invalid-response', 'El destino de la solicitud no está permitido.');
  }
  let pathname = path.split('?')[0] ?? '';
  // Inspect encoded traversal/separators too, not just the URL parser's result.
  for (let depth = 0; depth < 4; depth++) {
    if (pathname.split('/').some(part => part === '.' || part === '..') || pathname.includes('\\') || hasControlOrSpace(pathname)) {
      throw new DiaryError('invalid-response', 'El destino de la solicitud no está permitido.');
    }
    let decoded: string;
    try { decoded = decodeURIComponent(pathname); }
    catch { throw new DiaryError('invalid-response', 'El destino de la solicitud no está permitido.'); }
    if (decoded === pathname) break;
    if (decoded.startsWith('//')) throw new DiaryError('invalid-response', 'El destino de la solicitud no está permitido.');
    pathname = decoded;
    if (depth === 3) throw new DiaryError('invalid-response', 'El destino de la solicitud no está permitido.');
  }
  const url = new URL(`/api${path}`, 'https://same-origin.invalid');
  if (url.origin !== 'https://same-origin.invalid' || !url.pathname.startsWith('/api/')) {
    throw new DiaryError('invalid-response', 'El destino de la solicitud no está permitido.');
  }
  return `/api${path}`;
}

async function errorDetail(response: AxiosResponse<unknown>, context: Context): Promise<string> {
  const contentType: unknown = response.headers['content-type'];
  let body: unknown = response.data;
  if (typeof contentType !== 'string' || !/^application\/json(?:\s*;|$)/i.test(contentType)) return statusMessage(response.status);
  if (body instanceof Blob) {
    if (body.size > 8192) return statusMessage(response.status);
    try { body = JSON.parse(await readErrorBlob(body, context)); }
    catch (error: unknown) {
      if (error instanceof DiaryError) throw error;
      return statusMessage(response.status);
    }
  }
  if (typeof body === 'object' && body !== null && 'detail' in body &&
      typeof body.detail === 'string' && body.detail.trim() && body.detail.length <= 2048) return body.detail;
  return statusMessage(response.status);
}

export function createHttpClient(options: { store?: SessionStore; adapter?: AxiosAdapter; deadlineSignal?: () => AbortSignal } = {}) {
  const store = options.store ?? sessionStore;
  const contexts = new WeakMap<GenericAbortSignal, Context>();
  const instance = axios.create({
    timeout: 10000, withCredentials: true, withXSRFToken: false,
    xsrfCookieName: '', validateStatus: () => true,
    ...(options.adapter ? { adapter: options.adapter } : {}),
  });

  instance.interceptors.request.use(config => {
    const context = config.signal ? contexts.get(config.signal) : undefined;
    if (!context || context.generation !== store.getState().generation) {
      throw new DiaryError('aborted', 'La solicitud fue cancelada.');
    }
    if (context.combined.aborted) throw cancellation(context);
    // No caller can override URL, adapter, Origin or credentials through this API.
    config.withCredentials = true;
    config.headers.delete('Origin');
    config.headers.delete('Authorization');
    config.headers.delete('X-CSRF-Token');
    const unsafe = !['get', 'head', 'options'].includes(config.method ?? 'get');
    if (unsafe && config.url !== '/api/login') {
      const token = config.url === '/api/logout' ? context.logoutToken : store.getState().session?.csrf_token;
      if (!token) throw new DiaryError('http', 'La solicitud no tiene un token CSRF válido.', 403);
      config.headers.set('X-CSRF-Token', token);
    }
    return config;
  });

  instance.interceptors.response.use(async (response: AxiosResponse<unknown>) => {
    const context = response.config.signal ? contexts.get(response.config.signal) : undefined;
    if (!context || context.generation !== store.getState().generation) {
      throw new DiaryError('aborted', 'La solicitud fue cancelada.');
    }
    if (context.combined.aborted) throw cancellation(context);
    if (response.status < 200 || response.status >= 300) {
      let detail = await errorDetail(response, context);
      // Error-body decoding can be asynchronous (PDF JSON blobs).
      if (context.generation !== store.getState().generation) {
        throw new DiaryError('aborted', 'La solicitud fue cancelada.');
      }
      if (context.combined.aborted) throw cancellation(context);
      if (response.status === 401 && store.getState().session) store.getState().clearSession(context.generation, true);
      if (response.status === 409) detail += ' Usá «Descartar borrador y recargar» para abrir la versión actual; tus cambios no se sobrescribieron.';
      throw new DiaryError('http', detail, response.status);
    }
    return response;
  });

  return {
    async request(path: string, signal: AbortSignal, request: RequestOptions = {}): Promise<AxiosResponse<unknown>> {
      try {
        signal.throwIfAborted();
        const url = apiPath(path);
        if (request.logoutToken !== undefined && (path !== '/logout' || request.method !== 'POST')) {
          throw new DiaryError('invalid-response', 'El destino de la solicitud no está permitido.');
        }
        const deadline = options.deadlineSignal?.() ?? AbortSignal.timeout(10000);
        const combined = AbortSignal.any([signal, deadline]);
        contexts.set(combined, {
          generation: store.getState().generation,
          logoutToken: request.logoutToken ?? store.getState().session?.csrf_token,
          caller: signal, deadline, combined,
        });
        return await instance.request<unknown>({
          url, method: request.method ?? 'GET', data: request.data,
          responseType: request.responseType ?? 'json', signal: combined,
        });
      } catch (error: unknown) {
        if (signal.aborted) throw new DiaryError('aborted', 'La solicitud fue cancelada.');
        if (error instanceof DiaryError) throw error;
        if (axios.isAxiosError(error) && (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT')) {
          throw new DiaryError('timeout', 'La solicitud tardó demasiado. Intentá nuevamente.');
        }
        if (axios.isCancel(error)) throw new DiaryError('timeout', 'La solicitud tardó demasiado. Intentá nuevamente.');
        // Do not retain a raw AxiosError/cause: its config may contain passwords.
        throw new DiaryError('network', 'No se pudo conectar con la API. Comprobá la conexión e intentá nuevamente.');
      }
    },
  };
}

export type HttpClient = ReturnType<typeof createHttpClient>;
export const http = createHttpClient();
