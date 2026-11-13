import assert from 'node:assert/strict';
import test from 'node:test';
import {
  intervalLabel, isSuccessOutcome, outcomeLabel, sourceTitle,
} from '../src/features/admin/state.ts';

test('interval labels cover the five allowed values', () => {
  assert.equal(intervalLabel(300), '5 minutos');
  assert.equal(intervalLabel(600), '10 minutos');
  assert.equal(intervalLabel(900), '15 minutos');
  assert.equal(intervalLabel(1800), '30 minutos');
  assert.equal(intervalLabel(3600), '60 minutos');
});

test('outcome labels distinguish success, failure and no attempt', () => {
  assert.equal(outcomeLabel('ok'), 'Actualización exitosa');
  assert.equal(outcomeLabel('not_modified'), 'Sin cambios');
  assert.equal(outcomeLabel('timeout'), 'Tiempo de espera agotado');
  assert.equal(outcomeLabel('unknown_code'), 'unknown_code');
  assert.equal(outcomeLabel(null), 'Sin intentos registrados');
  assert.equal(isSuccessOutcome('ok'), true);
  assert.equal(isSuccessOutcome('not_modified'), true);
  assert.equal(isSuccessOutcome('timeout'), false);
  assert.equal(isSuccessOutcome('source_degraded'), false);
});

test('source titles name both ENRE cards', () => {
  assert.equal(sourceTitle('outages'), 'ENRE — Cortes actuales');
  assert.equal(sourceTitle('scheduled_works'), 'ENRE — Trabajos programados');
});
