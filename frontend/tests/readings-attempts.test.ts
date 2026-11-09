import assert from 'node:assert/strict';
import test from 'node:test';
import { newRequestKey } from '../src/features/readings/attempts.ts';

test('idempotency keys are UUID-shaped and unique without relying on secure-context APIs', () => {
  const keys = new Set<string>();
  for (let index = 0; index < 64; index++) {
    const key = newRequestKey();
    assert.match(key, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    keys.add(key);
  }
  assert.equal(keys.size, 64);
});
