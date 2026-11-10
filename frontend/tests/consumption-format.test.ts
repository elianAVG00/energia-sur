import assert from 'node:assert/strict';
import test from 'node:test';
import { displayKwh, roundTwoDecimals } from '../src/features/consumption/format.ts';

test('roundTwoDecimals rounds half-up to two decimals', () => {
  assert.equal(roundTwoDecimals('15'), '15.00');
  assert.equal(roundTwoDecimals('10'), '10.00');
  assert.equal(roundTwoDecimals('0'), '0.00');
  assert.equal(roundTwoDecimals('8.571428571428571'), '8.57');
  assert.equal(roundTwoDecimals('2.6666666666666665'), '2.67');
  assert.equal(roundTwoDecimals('105'), '105.00');
  assert.equal(roundTwoDecimals('0.004'), '0.00');
  assert.equal(roundTwoDecimals('0.005'), '0.01');
  assert.equal(roundTwoDecimals('0.009'), '0.01');
  assert.equal(roundTwoDecimals('0.014'), '0.01');
  assert.equal(roundTwoDecimals('0.015'), '0.02');
  assert.equal(roundTwoDecimals('99.999'), '100.00');
});

test('roundTwoDecimals handles arbitrary-size integers without float loss', () => {
  assert.equal(roundTwoDecimals('999999999999999999999999999999'), '999999999999999999999999999999.00');
});

test('displayKwh shows a below-minimum positive value as a less-than indicator', () => {
  assert.equal(displayKwh('0.004', true), '< 0.01');
  assert.equal(displayKwh('15', false), '15.00');
  assert.equal(displayKwh('0', false), '0.00');
  assert.equal(displayKwh('0.005', false), '0.01');
});
