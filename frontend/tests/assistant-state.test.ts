import assert from 'node:assert/strict';
import test from 'node:test';
import { createAssistantStore, priorHistory } from '../src/features/assistant/state.ts';

test('temporary conversation lifecycle accumulates deltas and sources', () => {
  const store = createAssistantStore();
  store.getState().addUser('hola');
  assert.equal(store.getState().messages.length, 1);
  assert.equal(store.getState().streaming, true);
  const id = store.getState().beginAssistant();
  store.getState().append(id, 'Hola');
  store.getState().append(id, ' mundo');
  store.getState().setSources(id, [
    { source_name: 'Edesur', url: 'https://www.edesur.com.ar/' },
  ]);
  store.getState().finish(id, true);
  const assistant = store.getState().messages[1];
  assert.ok(assistant);
  assert.equal(assistant.content, 'Hola mundo');
  assert.equal(assistant.sources.length, 1);
  assert.equal(assistant.status, 'done');
  assert.equal(store.getState().streaming, false);
});

test('cancel and reset clear the temporary state', () => {
  const store = createAssistantStore();
  store.getState().addUser('hola');
  store.getState().beginAssistant();
  store.getState().cancel();
  assert.equal(store.getState().streaming, false);
  const assistant = store.getState().messages[1];
  assert.ok(assistant);
  assert.equal(assistant.status, 'cancelled');
  store.getState().reset();
  assert.deepEqual(store.getState().messages, []);
});

test('conversation scope and TTL metadata are tracked', () => {
  const store = createAssistantStore();
  store.getState().setConversation('conv-123', 'persistent');
  assert.equal(store.getState().conversationId, 'conv-123');
  assert.equal(store.getState().scope, 'persistent');
  store.getState().addUser('hola');
  assert.equal(store.getState().isExpired(), false);
  const ttl = store.getState().ttlMs;
  assert.equal(store.getState().isExpired(Date.now() + ttl + 1), true);
  store.getState().reset();
  assert.equal(store.getState().conversationId, null);
  assert.equal(store.getState().scope, null);
  assert.deepEqual(store.getState().messages, []);
});

test('prior history drops empty turns and caps long content', () => {
  const history = priorHistory([
    { id: '1', role: 'user', content: 'hola', sources: [], status: 'done' },
    { id: '2', role: 'assistant', content: '', sources: [], status: 'cancelled' },
    { id: '3', role: 'assistant', content: 'x'.repeat(2500), sources: [], status: 'done' },
  ]);
  assert.equal(history.length, 2);
  const [first, second] = history;
  assert.ok(first && second);
  assert.equal(first.content, 'hola');
  assert.equal(second.content.length, 2000);
});

test('prior history keeps the newest turns within the character budget', () => {
  const messages = Array.from({ length: 10 }, (_, index) => ({
    id: String(index),
    role: index % 2 === 0 ? 'user' as const : 'assistant' as const,
    content: 'x'.repeat(2000),
    sources: [],
    status: 'done' as const,
  }));
  const history = priorHistory(messages);
  const total = history.reduce((sum, turn) => sum + turn.content.length, 0);
  assert.ok(total <= 4000, `history total ${total}`);
  assert.equal(history.length, 2);
  const body = JSON.stringify({ message: 'consulta', history });
  assert.ok(Buffer.byteLength(body) < 16384, `body ${Buffer.byteLength(body)}`);
});

test('setError shows a safe failure without clearing messages', () => {
  const store = createAssistantStore();
  store.getState().addUser('hola');
  store.getState().setError('No se pudo borrar la conversación.');
  assert.equal(store.getState().error, 'No se pudo borrar la conversación.');
  assert.equal(store.getState().messages.length, 1);
});

test('fail records a safe error without persisting anything', () => {
  const store = createAssistantStore();
  store.getState().addUser('hola');
  const id = store.getState().beginAssistant();
  store.getState().fail(id, 'No se pudo conectar con el asistente.');
  assert.equal(store.getState().error, 'No se pudo conectar con el asistente.');
  const assistant = store.getState().messages[1];
  assert.ok(assistant);
  assert.equal(assistant.status, 'error');
  assert.equal(store.getState().streaming, false);
});
