import assert from 'node:assert/strict';
import test from 'node:test';
import {
  coverageLabel, formatInstant, formatReportedTime, freshnessLabel, limitationMessage,
  reasonText, restorationText, retryAfterMessage, stateDetail, stateHeading,
} from '../src/features/scheduled-works/state.ts';

test('coverage and freshness labels stay explicit', () => {
  assert.equal(coverageLabel('covered'), 'Cobertura verificada');
  assert.equal(coverageLabel('out_of_coverage'), 'Fuera de cobertura');
  assert.equal(coverageLabel('coverage_unverified'), 'Cobertura no verificada');
  assert.equal(freshnessLabel('fresh'), 'Información actualizada');
  assert.equal(freshnessLabel('stale'), 'Información desactualizada');
  assert.equal(freshnessLabel('unavailable'), 'Fuente no disponible');
});

test('every normative state has a heading and a conservative detail', () => {
  for (const state of ['out_of_coverage', 'unavailable', 'stale', 'works_reported',
    'no_works', 'coverage_unverified'] as const) {
    assert.ok(stateHeading(state).length > 0);
    assert.ok(stateDetail(state).length > 0);
  }
  assert.match(stateDetail('no_works'), /no publica una agenda de fechas futuras/i);
  assert.match(stateDetail('works_reported'), /no son una agenda de trabajos futuros/i);
  assert.match(stateDetail('coverage_unverified'), /no podemos confirmar/i);
  assert.doesNotMatch(stateDetail('no_works'), /no hay cortes/i);
});

test('unpublished reason and restoration are labelled, never invented', () => {
  const base = { category: 'maintenance', partido: 'X' } as const;
  assert.equal(reasonText({ ...base }), 'No publicado por la fuente');
  assert.equal(reasonText({ ...base, reason_text: 'Mantenimiento' }), 'Mantenimiento');
  assert.equal(restorationText({ ...base }), 'No publicado por la fuente');
  assert.equal(restorationText({ ...base, restoration_estimate_text: '2026-01-14 15:33' }),
    '2026-01-14 15:33');
});

test('limitations have plain-language messages', () => {
  assert.match(limitationMessage('dates_not_published'), /no publica fecha de inicio ni de fin/i);
  assert.match(limitationMessage('proximity_not_available'), /no publica coordenadas/i);
  assert.match(limitationMessage('announced_works_not_displayed'), /comunicado/i);
});

test('instants render in Buenos Aires time and reported time is optional', () => {
  assert.equal(formatInstant('2026-11-10T14:08:04Z'), '10/11/2026 11:08');
  assert.equal(formatInstant(undefined), '');
  assert.equal(formatReportedTime('11:05'), '11:05 hs');
  assert.equal(formatReportedTime('--:--'), '');
  assert.match(retryAfterMessage(30), /30 segundos/);
  assert.match(retryAfterMessage(null), /Esperá un momento/);
});
