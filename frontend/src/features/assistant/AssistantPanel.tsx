import { useEffect, useRef, useState } from 'react';
import { Button } from '../../components/ui/button.tsx';
import { Label } from '../../components/ui/label.tsx';
import { Textarea } from '../../components/ui/textarea.tsx';
import { DiaryError } from '../../lib/httpError.ts';
import { sessionStore, useSessionStore } from '../../stores/session.ts';
import { deleteConversation, isSafeHttpsUrl, streamChat } from './api.ts';
import { assistantStore, priorHistory, useAssistantStore } from './state.ts';

export function AssistantPanel() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const messages = useAssistantStore(state => state.messages);
  const streaming = useAssistantStore(state => state.streaming);
  const error = useAssistantStore(state => state.error);
  const generation = useSessionStore(state => state.generation);
  const controller = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);
  const lastGeneration = useRef(generation);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);
  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end' });
  }, [messages, streaming]);
  useEffect(() => () => {
    controller.current?.abort();
  }, []);
  useEffect(() => {
    if (lastGeneration.current === generation) return;
    lastGeneration.current = generation;
    controller.current?.abort();
    assistantStore.getState().reset();
  }, [generation]);
  useEffect(() => {
    const interval = setInterval(() => {
      if (assistantStore.getState().isExpired()) {
        controller.current?.abort();
        assistantStore.getState().reset();
      }
    }, 60_000);
    return () => clearInterval(interval);
  }, []);

  async function send() {
    const text = input.trim();
    if (!text || streaming) return;
    setInput('');
    const store = assistantStore.getState();
    const conversationId = store.conversationId;
    const activeGeneration = sessionStore.getState().generation;
    const prior = priorHistory(store.messages);
    store.addUser(text);
    const assistantId = store.beginAssistant();
    const aborter = new AbortController();
    controller.current = aborter;
    try {
      await streamChat(text, aborter.signal, event => {
        if (sessionStore.getState().generation !== activeGeneration) return;
        const current = assistantStore.getState();
        if (event.type === 'conversation') {
          current.setConversation(
            event.conversation_id,
            event.scope === 'persistent' ? 'persistent' : 'temporary',
          );
        } else if (event.type === 'delta') current.append(assistantId, event.text);
        else if (event.type === 'sources') current.setSources(assistantId, event.sources);
        else if (event.type === 'done') current.finish(assistantId, event.ok);
        // The backend follows an `error` event with the static fallback delta and
        // `done`; the fallback text is shown once, without duplicating an alert.
      }, conversationId, prior);
      const after = assistantStore.getState();
      const message = after.messages.find(item => item.id === assistantId);
      if (message?.status === 'streaming') after.finish(assistantId, false);
    } catch (reason: unknown) {
      const current = assistantStore.getState();
      if (aborter.signal.aborted) current.cancel();
      else current.fail(
        assistantId,
        reason instanceof Error ? reason.message : 'No se pudo conectar con el asistente.',
      );
    } finally {
      if (controller.current === aborter) controller.current = null;
    }
  }

  function cancel() {
    controller.current?.abort();
    assistantStore.getState().cancel();
  }

  async function clearConversation() {
    const state = assistantStore.getState();
    const conversationId = state.conversationId;
    const persistent = state.scope === 'persistent';
    controller.current?.abort();
    if (persistent && conversationId) {
      const aborter = new AbortController();
      try {
        await deleteConversation(conversationId, aborter.signal);
      } catch (reason: unknown) {
        if (reason instanceof DiaryError && reason.status === 404) {
          // The server already removed it; clearing the local panel is accurate.
          assistantStore.getState().reset();
          return;
        }
        assistantStore.getState().setError(
          'No se pudo borrar la conversación en el servidor. Intentá nuevamente.',
        );
        return;
      }
    }
    assistantStore.getState().reset();
  }

  if (!open) {
    return (
      <Button
        type="button"
        variant="secondary"
        aria-expanded={false}
        onClick={() => setOpen(true)}
      >
        Abrir asistente
      </Button>
    );
  }

  return (
    <section id="assistant-panel" aria-label="Conversación del asistente" className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-semibold">Asistente Energía Sur</p>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          aria-expanded
          aria-controls="assistant-panel"
          onClick={() => setOpen(false)}
        >
          Cerrar
        </Button>
      </div>
      <p className="text-[11px] leading-4 text-muted-foreground">
        Las preguntas pueden procesarse con OpenAI. Si iniciás sesión, tus mensajes se
        guardan para continuar la conversación; podés borrarlos con Limpiar. No compartas
        datos personales sensibles.
      </p>
      <div
        role="log"
        aria-live="polite"
        aria-label="Mensajes"
        className="max-h-[45vh] space-y-2 overflow-y-auto pr-1"
      >
        {messages.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Preguntá sobre cortes, trabajos o trámites de Edesur.
          </p>
        )}
        {messages.map(message => (
          <div key={message.id} className={message.role === 'user' ? 'text-right' : ''}>
            <p className={[
              'inline-block max-w-full whitespace-pre-wrap break-words rounded-md px-3 py-2 text-left text-sm',
              message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted',
            ].join(' ')}>
              {message.content || (message.status === 'streaming' ? '\u2026' : '')}
            </p>
            {message.status === 'cancelled' && (
              <p className="text-xs text-muted-foreground">Respuesta interrumpida.</p>
            )}
            {message.sources.length > 0 && (
              <ul className="mt-1 space-y-1 text-xs" aria-label="Fuentes oficiales">
                {message.sources
                  .filter(source => isSafeHttpsUrl(source.url))
                  .map(source => (
                    <li key={`${source.source_name}:${source.url}`}>
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="underline underline-offset-2"
                      >
                        {source.source_name}
                      </a>
                    </li>
                  ))}
              </ul>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>
      {streaming && (
        <p role="status" className="text-xs text-muted-foreground">
          El asistente está respondiendo.
        </p>
      )}
      {error && <p role="alert" className="text-xs text-destructive">{error}</p>}
      <Label htmlFor="assistant-input" className="sr-only">Consulta</Label>
      <Textarea
        id="assistant-input"
        ref={inputRef}
        value={input}
        rows={2}
        maxLength={2000}
        placeholder="¿Cómo pago la factura?"
        aria-label="Consulta al asistente"
        onChange={event => setInput(event.target.value)}
        onKeyDown={event => {
          if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            void send();
          }
        }}
      />
      <div className="flex flex-wrap gap-2">
        <Button type="button" size="sm" disabled={streaming || !input.trim()} onClick={() => void send()}>
          Enviar
        </Button>
        {streaming && (
          <Button type="button" size="sm" variant="outline" onClick={cancel}>
            Cancelar
          </Button>
        )}
        {messages.length > 0 && (
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={() => void clearConversation()}
          >
            Limpiar
          </Button>
        )}
      </div>
    </section>
  );
}
