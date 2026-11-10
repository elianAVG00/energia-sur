import assert from 'node:assert/strict';
import test from 'node:test';
import {
  categoryLabel, coverageLabel, formatInstant, formatReportedTime, freshnessLabel,
  retryAfterMessage, stateDetail, stateHeading,
} from '../src/features/outages/state.ts';

test('labels are human readable and keep coverage distinct from supply', () => {
  assert.equal(categoryLabel('medium_voltage'), 'Media tensión');
  assert.equal(categoryLabel('low_voltage'), 'Baja tensión');
  assert.equal(categoryLabel('preventive'), 'Corte preventivo');
  assert.equal(coverageLabel('covered'), 'Cobertura verificada');
  assert.equal(coverageLabel('out_of_coverage'), 'Fuera de cobertura');
  assert.equal(coverageLabel('coverage_unverified'), 'Cobertura no verificada');
  assert.equal(freshnessLabel('fresh'), 'Información actualizada');
  assert.equal(freshnessLabel('stale'), 'Información desactualizada');
  assert.equal(freshnessLabel('unavailable'), 'Fuente no disponible');
});

test('every normative state has a heading and a conservative detail', () => {
  for (const state of ['geographic_error', 'out_of_coverage', 'unavailable', 'stale',
    'reported', 'no_reports', 'coverage_unverified'] as const) {
    assert.ok(stateHeading(state).length > 0);
    assert.ok(stateDetail(state).length > 0);
  }
  assert.match(stateDetail('no_reports'), /no garantiza el suministro/i);
  assert.match(stateDetail('coverage_unverified'), /no podemos confirmar/i);
  assert.doesNotMatch(stateDetail('coverage_unverified'), /no hay cortes/i);
  assert.match(stateDetail('unavailable'), /no podemos confirmar cortes ni ausencia/i);
  assert.match(stateDetail('stale'), /más de 15 minutos/i);
});

test('instants are rendered in Buenos Aires time, not the host zone', () => {
  assert.equal(formatInstant('2026-11-10T04:53:49Z'), '10/11/2026 01:53');
  assert.equal(formatInstant('2026-01-01T03:00:00Z'), '01/01/2026 00:00');
  assert.equal(formatInstant(undefined), '');
  assert.equal(formatInstant('not-a-date'), '');
});

test('reported time and retry messages are explicit', () => {
  assert.equal(formatReportedTime('0:25'), '0:25 hs');
  assert.equal(formatReportedTime('--:--'), '');
  assert.equal(formatReportedTime(undefined), '');
  assert.match(retryAfterMessage(30), /30 segundos/);
  assert.match(retryAfterMessage(null), /Esperá un momento/);
});
