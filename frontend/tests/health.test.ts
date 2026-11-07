import assert from 'node:assert/strict';
import { test } from 'node:test';
import { fetchHealth, HEALTH_TIMEOUT_MS, HealthError } from '../src/health.ts';

function isHealthError(kind: HealthError['kind']) {
  return (error: unknown): boolean => error instanceof HealthError && error.kind === kind;
}

test('uses the same-origin health URL without caching and validates an injected success', async () => {
  const fetchImpl: typeof fetch = async (input, init) => {
    assert.equal(input, '/api/health');
    assert.equal(init?.cache, 'no-store');
    assert.ok(init?.signal instanceof AbortSignal);
    return Response.json({ status: 'ok' });
  };

  const response = await fetchHealth({ signal: new AbortController().signal, fetchImpl });
  assert.deepEqual(response, { status: 'ok' });
  assert.equal(HEALTH_TIMEOUT_MS, 5_000);
});

for (const status of [201, 204, 404, 500, 502, 503]) {
  test(`rejects HTTP ${status} rather than accepting a body as success`, async () => {
    const fetchImpl: typeof fetch = async () => new Response(null, { status });
    await assert.rejects(
      fetchHealth({ signal: new AbortController().signal, fetchImpl }),
      isHealthError('http'),
    );
  });
}

for (const body of [null, [], {}, { status: 'down' }, { status: true }, { status: 'ok', database: 'ready' }]) {
  test(`rejects an unexpected JSON body: ${JSON.stringify(body)}`, async () => {
    const fetchImpl: typeof fetch = async () => Response.json(body);
    await assert.rejects(
      fetchHealth({ signal: new AbortController().signal, fetchImpl }),
      isHealthError('invalid-response'),
    );
  });
}

test('rejects malformed JSON', async () => {
  const fetchImpl: typeof fetch = async () => new Response('{', {
    headers: { 'Content-Type': 'application/json' },
  });
  await assert.rejects(
    fetchHealth({ signal: new AbortController().signal, fetchImpl }),
    isHealthError('invalid-response'),
  );
});

test('rejects non-JSON responses even with a JSON-shaped body', async () => {
  const fetchImpl: typeof fetch = async () => new Response('{"status":"ok"}', {
    headers: { 'Content-Type': 'text/html' },
  });
  await assert.rejects(
    fetchHealth({ signal: new AbortController().signal, fetchImpl }),
    isHealthError('invalid-response'),
  );
});

test('accepts application/json with a charset parameter', async () => {
  const fetchImpl: typeof fetch = async () => new Response('{"status":"ok"}', {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
  assert.deepEqual(
    await fetchHealth({ signal: new AbortController().signal, fetchImpl }),
    { status: 'ok' },
  );
});

test('reports network failure without supplying a synthetic success', async () => {
  const fetchImpl: typeof fetch = async () => { throw new TypeError('Synthetic connection failure'); };
  await assert.rejects(
    fetchHealth({ signal: new AbortController().signal, fetchImpl }),
    isHealthError('network'),
  );
});

const pendingFetch: typeof fetch = async (_input, init) => new Promise<Response>((_resolve, reject) => {
  const signal = init?.signal;
  assert.ok(signal);
  if (signal.aborted) {
    reject(signal.reason);
    return;
  }
  signal.addEventListener('abort', () => reject(signal.reason), { once: true });
});

test('aborts a pending request when its bounded timeout expires', async () => {
  await assert.rejects(
    fetchHealth({ signal: new AbortController().signal, fetchImpl: pendingFetch, timeoutMs: 10 }),
    isHealthError('timeout'),
  );
});

test('the timeout also covers JSON body consumption after headers arrive', async () => {
  const fetchImpl: typeof fetch = async (_input, init) => {
    const signal = init?.signal;
    assert.ok(signal);
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        signal.addEventListener('abort', () => controller.error(signal.reason), { once: true });
      },
    });
    return new Response(body, { headers: { 'Content-Type': 'application/json' } });
  };
  await assert.rejects(
    fetchHealth({ signal: new AbortController().signal, fetchImpl, timeoutMs: 10 }),
    isHealthError('timeout'),
  );
});

test('forwards cancellation of a superseded or unmounted request', async () => {
  const controller = new AbortController();
  const request = fetchHealth({ signal: controller.signal, fetchImpl: pendingFetch });
  controller.abort();
  await assert.rejects(request, isHealthError('aborted'));
});

test('does not fetch if the caller is already aborted', async () => {
  const controller = new AbortController();
  controller.abort();
  let called = false;
  const fetchImpl: typeof fetch = async () => {
    called = true;
    return Response.json({ status: 'ok' });
  };
  await assert.rejects(fetchHealth({ signal: controller.signal, fetchImpl }), isHealthError('aborted'));
  assert.equal(called, false);
});

test('rejects a late successful response after the caller has cancelled', async () => {
  const controller = new AbortController();
  const fetchImpl: typeof fetch = async () => {
    controller.abort();
    return Response.json({ status: 'ok' });
  };
  await assert.rejects(fetchHealth({ signal: controller.signal, fetchImpl }), isHealthError('aborted'));
});

test('a failed subsequent helper attempt cannot reuse an earlier successful response', async () => {
  let attempts = 0;
  const fetchImpl: typeof fetch = async () => {
    attempts += 1;
    if (attempts === 1) return Response.json({ status: 'ok' });
    throw new TypeError('Synthetic backend unavailable');
  };
  assert.deepEqual(await fetchHealth({ signal: new AbortController().signal, fetchImpl }), { status: 'ok' });
  await assert.rejects(
    fetchHealth({ signal: new AbortController().signal, fetchImpl }),
    isHealthError('network'),
  );
  assert.equal(attempts, 2);
});
