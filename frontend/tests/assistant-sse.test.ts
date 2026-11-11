import assert from 'node:assert/strict';
import test from 'node:test';
import {
  isSafeHttpsUrl, parseFrame, parseSources, parseSseBuffer,
} from '../src/features/assistant/api.ts';

test('parses every assistant event', () => {
  assert.deepEqual(
    parseFrame('event: conversation\ndata: {"conversation_id":"abc","scope":"temporary"}'),
    { type: 'conversation', conversation_id: 'abc', scope: 'temporary' },
  );
  assert.deepEqual(
    parseFrame('event: delta\ndata: {"text":"Hola"}'),
    { type: 'delta', text: 'Hola' },
  );
  assert.deepEqual(
    parseFrame('event: sources\ndata: {"sources":[{"source_name":"Edesur","url":"https://www.edesur.com.ar/"}]}'),
    { type: 'sources', sources: [{ source_name: 'Edesur', url: 'https://www.edesur.com.ar/' }] },
  );
  assert.deepEqual(
    parseFrame('event: error\ndata: {"code":"timeout","message":"Fallback"}'),
    { type: 'error', code: 'timeout', message: 'Fallback' },
  );
  assert.deepEqual(parseFrame('event: done\ndata: {"ok":true}'), { type: 'done', ok: true });
});

test('parses partial frames split across chunks', () => {
  const first = parseSseBuffer('event: delta\ndata: {"text":"Ho');
  assert.equal(first.events.length, 0);
  assert.match(first.rest, /Ho/);
  const second = parseSseBuffer(
    `${first.rest}la"}\n\nevent: done\ndata: {"ok":true}\n\n`,
  );
  assert.deepEqual(second.events, [
    { type: 'delta', text: 'Hola' },
    { type: 'done', ok: true },
  ]);
  assert.equal(second.rest, '');
});

test('ignores invalid JSON and unknown events', () => {
  assert.equal(parseFrame('event: delta\ndata: not-json'), null);
  assert.equal(parseFrame('event: nope\ndata: {}'), null);
  assert.equal(parseFrame('event: done\ndata: {}'), null);
});

test('accepts only HTTPS official sources and drops unsafe links', () => {
  assert.equal(isSafeHttpsUrl('https://www.edesur.com.ar/'), true);
  assert.equal(isSafeHttpsUrl('https://www.enre.gov.ar/paginacorte/'), true);
  assert.equal(isSafeHttpsUrl('https://evil-edesur.com.ar/'), false);
  assert.equal(isSafeHttpsUrl('https://example.com/'), false);
  assert.equal(isSafeHttpsUrl('http://www.edesur.com.ar/'), false);
  assert.equal(isSafeHttpsUrl('javascript:alert(1)'), false);
  assert.deepEqual(
    parseSources([
      { source_name: 'Edesur', url: 'https://www.edesur.com.ar/' },
      { source_name: 'Bad', url: 'javascript:alert(1)' },
      { source_name: 'Bad', url: 'not-a-url' },
    ]),
    [{ source_name: 'Edesur', url: 'https://www.edesur.com.ar/' }],
  );
});
