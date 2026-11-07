import assert from 'node:assert/strict';
import { test } from 'node:test';
import { healthReducer } from '../src/healthState.ts';
import type { HealthState } from '../src/healthState.ts';

test('starting a retry immediately removes the previous successful JSON', () => {
  const success: HealthState = { status: 'success', response: { status: 'ok' } };
  const loading = healthReducer(success, { type: 'loading' });
  assert.deepEqual(loading, { status: 'loading' });
  assert.equal('response' in loading, false);

  const failure = healthReducer(loading, { type: 'error', message: 'Synthetic network failure' });
  assert.deepEqual(failure, { status: 'error', message: 'Synthetic network failure' });
  assert.equal('response' in failure, false);
});

test('an error can recover only after a subsequent success action', () => {
  const error: HealthState = { status: 'error', message: 'Synthetic timeout' };
  const loading = healthReducer(error, { type: 'loading' });
  assert.deepEqual(loading, { status: 'loading' });
  const success = healthReducer(loading, { type: 'success', response: { status: 'ok' } });
  assert.deepEqual(success, { status: 'success', response: { status: 'ok' } });
  assert.equal('message' in success, false);
});
