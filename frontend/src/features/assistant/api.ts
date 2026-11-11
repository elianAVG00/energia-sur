import { apiPath, http } from '../../lib/http.ts';

export interface Source {
  source_name: string;
  url: string;
}

export interface HistoryTurn {
  role: 'user' | 'assistant';
  content: string;
}

export type AssistantEvent =
  | { type: 'conversation'; conversation_id: string; scope: string }
  | { type: 'delta'; text: string }
  | { type: 'tool'; name: string; status: string; sources: Source[] }
  | { type: 'sources'; sources: Source[] }
  | { type: 'error'; code: string; message: string }
  | { type: 'done'; ok: boolean };

export class AssistantError extends Error {
  readonly status: number | null;

  constructor(message: string, status: number | null = null) {
    super(message);
    this.name = 'AssistantError';
    this.status = status;
  }
}

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function text(value: unknown): string | null {
  return typeof value === 'string' && value.length > 0 ? value : null;
}

const ALLOWED_HOSTS = [
  'edesur.com.ar', 'ov.edesur.com.ar', 'argentina.gob.ar', 'www.enre.gov.ar',
];

export function isSafeHttpsUrl(value: string): boolean {
  try {
    const url = new URL(value);
    if (url.protocol !== 'https:') return false;
    const host = url.hostname.toLowerCase();
    return ALLOWED_HOSTS.some(allowed => host === allowed || host.endsWith(`.${allowed}`));
  } catch {
    return false;
  }
}

export function parseSources(value: unknown): Source[] {
  if (!Array.isArray(value)) return [];
  const sources: Source[] = [];
  for (const item of value) {
    if (!record(item)) continue;
    const name = text(item.source_name);
    const url = text(item.url);
    if (name && url && isSafeHttpsUrl(url)) sources.push({ source_name: name, url });
  }
  return sources;
}

export function parseFrame(frame: string): AssistantEvent | null {
  let name = 'message';
  const data: string[] = [];
  for (const line of frame.replace(/\r\n/g, '\n').split('\n')) {
    if (line.startsWith('event:')) name = line.slice(6).trim();
    else if (line.startsWith('data:')) data.push(line.slice(5).trimStart());
  }
  if (data.length === 0) return null;
  let payload: unknown;
  try {
    payload = JSON.parse(data.join('\n'));
  } catch {
    return null;
  }
  if (!record(payload)) return null;
  if (name === 'conversation') {
    const id = text(payload.conversation_id);
    const scope = text(payload.scope);
    return id && scope ? { type: 'conversation', conversation_id: id, scope } : null;
  }
  if (name === 'delta') {
    const value = text(payload.text);
    return value === null ? null : { type: 'delta', text: value };
  }
  if (name === 'tool') {
    const tool = text(payload.name);
    const status = text(payload.status);
    return tool && status
      ? { type: 'tool', name: tool, status, sources: parseSources(payload.sources) }
      : null;
  }
  if (name === 'sources') {
    return { type: 'sources', sources: parseSources(payload.sources) };
  }
  if (name === 'error') {
    const code = text(payload.code);
    const message = text(payload.message);
    return code && message ? { type: 'error', code, message } : null;
  }
  if (name === 'done') {
    return typeof payload.ok === 'boolean' ? { type: 'done', ok: payload.ok } : null;
  }
  return null;
}

export function parseSseBuffer(buffer: string): { events: AssistantEvent[]; rest: string } {
  const events: AssistantEvent[] = [];
  let rest = buffer.replace(/\r\n/g, '\n');
  let index = rest.indexOf('\n\n');
  while (index !== -1) {
    const frame = rest.slice(0, index);
    rest = rest.slice(index + 2);
    const event = parseFrame(frame);
    if (event) events.push(event);
    index = rest.indexOf('\n\n');
  }
  return { events, rest };
}

function statusMessage(status: number): string {
  if (status === 413) return 'La consulta es demasiado grande.';
  if (status === 422) return 'Revisá los datos ingresados.';
  if (status === 429) return 'Demasiadas solicitudes. Esperá un momento e intentá nuevamente.';
  if (status === 403) return 'El origen de la solicitud no está autorizado.';
  if (status === 503) return 'El asistente no está disponible en este momento.';
  return 'No se pudo conectar con el asistente.';
}

export async function streamChat(
  message: string,
  signal: AbortSignal,
  onEvent: (event: AssistantEvent) => void,
  conversationId: string | null = null,
  history: HistoryTurn[] = [],
): Promise<void> {
  const response = await fetch(apiPath('/assistant/chat'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      history,
    }),
    credentials: 'include',
    signal,
  });
  if (!response.ok) {
    let detail = statusMessage(response.status);
    try {
      const body = (await response.json()) as unknown;
      if (record(body) && typeof body.detail === 'string' && body.detail.trim()) {
        detail = body.detail;
      }
    } catch {
      // Keep the status message when the error body is not JSON.
    }
    throw new AssistantError(detail, response.status);
  }
  if (!response.body) throw new AssistantError('No se pudo abrir el stream.', response.status);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) {
        buffer += decoder.decode();
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const parsed = parseSseBuffer(buffer);
      buffer = parsed.rest;
      for (const event of parsed.events) onEvent(event);
    }
    if (buffer.trim()) {
      for (const event of parseSseBuffer(`${buffer}\n\n`).events) onEvent(event);
    }
  } finally {
    reader.releaseLock();
  }
}

export async function deleteConversation(
  conversationId: string,
  signal: AbortSignal,
): Promise<void> {
  if (!/^[0-9a-fA-F-]{36}$/.test(conversationId)) {
    throw new AssistantError('El identificador de la conversación no es válido.', 422);
  }
  await http.request(
    `/assistant/conversations/${encodeURIComponent(conversationId)}`,
    signal,
    { method: 'DELETE' },
  );
}
