import assert from 'node:assert/strict';
import test from 'node:test';
import {
  AssistantError, deleteConversation, streamChat,
} from '../src/features/assistant/api.ts';

function responseFrom(chunks: string[]): Response {
  const encoder = new TextEncoder();
  return new Response(new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  }), { status: 200, headers: { 'content-type': 'text/event-stream' } });
}

test('streams partial chunks and forward events', async () => {
  const original = globalThis.fetch;
  const events: unknown[] = [];
  globalThis.fetch = (async () => responseFrom([
    'event: delta\ndata: {"text":"Ho',
    'la"}\n\nevent: sources\ndata: {"sources":[{"source_name":"Edesur","url":"https://www.edesur.com.ar/"}]}\n\n',
    'event: done\ndata: {"ok":true}\n\n',
  ])) as typeof fetch;
  try {
    await streamChat('hola', new AbortController().signal, event => events.push(event));
  } finally {
    globalThis.fetch = original;
  }
  assert.deepEqual(events[0], { type: 'delta', text: 'Hola' });
  assert.deepEqual(events[1], {
    type: 'sources',
    sources: [{ source_name: 'Edesur', url: 'https://www.edesur.com.ar/' }],
  });
  assert.deepEqual(events[2], { type: 'done', ok: true });
});

test('surfaces a controlled HTTP error', async () => {
  const original = globalThis.fetch;
  globalThis.fetch = (async () => new Response(
    JSON.stringify({ detail: 'Demasiadas solicitudes.' }),
    { status: 429, headers: { 'content-type': 'application/json' } },
  )) as typeof fetch;
  try {
    await assert.rejects(
      () => streamChat('hola', new AbortController().signal, () => {}),
      (error: unknown) => error instanceof AssistantError
        && error.status === 429
        && error.message === 'Demasiadas solicitudes.',
    );
  } finally {
    globalThis.fetch = original;
  }
});

test('sends the conversation id for follow-up turns', async () => {
  const original = globalThis.fetch;
  let body: unknown;
  globalThis.fetch = (async (_url: string, init: RequestInit) => {
    body = JSON.parse(init.body as string);
    return responseFrom([
      'event: done\ndata: {"ok":true}\n\n',
    ]);
  }) as typeof fetch;
  try {
    await streamChat(
      'hola',
      new AbortController().signal,
      () => {},
      'conv-12344',
      [{ role: 'user', content: 'antes' }],
    );
  } finally {
    globalThis.fetch = original;
  }
  assert.deepEqual(body, {
    message: 'hola',
    conversation_id: 'conv-12344',
    history: [{ role: 'user', content: 'antes' }],
  });
});

test('rejects an invalid conversation id before delete', async () => {
  await assert.rejects(
    () => deleteConversation('not-a-uuid', new AbortController().signal),
    (error: unknown) => error instanceof AssistantError && error.status === 422,
  );
});

test('propagates a client abort', async () => {
  const original = globalThis.fetch;
  globalThis.fetch = (async () => {
    throw new DOMException('Aborted', 'AbortError');
  }) as typeof fetch;
  try {
    await assert.rejects(
      () => streamChat('hola', new AbortController().signal, () => {}),
      (error: unknown) => error instanceof DOMException && error.name === 'AbortError',
    );
  } finally {
    globalThis.fetch = original;
  }
});
