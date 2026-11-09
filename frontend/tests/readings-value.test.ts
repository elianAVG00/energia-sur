import assert from 'node:assert/strict';
import test from 'node:test';
import { canonicalReading, MAX_READING_DIGITS, readingIsLower } from '../src/features/readings/value.ts';

test('keeps decimal readings exact without numeric conversion', () => {
  assert.equal(canonicalReading('00056538'), '56538');
  assert.equal(canonicalReading('000'), '0');
  assert.equal(canonicalReading('9'.repeat(MAX_READING_DIGITS)), '9'.repeat(MAX_READING_DIGITS));
  for (const value of ['', '-1', '1.0', ' 1', '１', '9'.repeat(MAX_READING_DIGITS + 1)]) {
    assert.equal(canonicalReading(value), null);
  }
});

test('compares large readings for a warning without precision loss', () => {
  assert.equal(readingIsLower('9'.repeat(5000), `1${'0'.repeat(5000)}`), true);
  assert.equal(readingIsLower('0001', '1'), false);
  assert.equal(readingIsLower('10', '9'), false);
  assert.equal(readingIsLower('bad', '9'), null);
});
