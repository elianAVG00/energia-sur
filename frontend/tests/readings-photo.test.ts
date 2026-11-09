import assert from 'node:assert/strict';
import test from 'node:test';
import { EMPTY_CROP, MAX_PHOTO_BYTES, editPhotoAction, photoProblem, resolveCrop, stripDataUrl } from '../src/features/readings/photo.ts';

test('photo selection rejects empty, unsupported and oversized files', () => {
  assert.equal(photoProblem({ type: 'image/png', size: 10 }), null);
  assert.equal(photoProblem({ type: 'image/jpeg', size: MAX_PHOTO_BYTES }), null);
  assert.match(photoProblem({ type: 'image/gif', size: 10 }) ?? '', /JPG, PNG o WebP/);
  assert.match(photoProblem({ type: 'image/png', size: MAX_PHOTO_BYTES + 1 }) ?? '', /5 MB/);
  assert.match(photoProblem({ type: 'image/png', size: 0 }) ?? '', /vacía/);
});

test('only data URLs with a supported media type become API payloads', () => {
  assert.equal(stripDataUrl('data:image/png;base64,c3ludGhldGlj'), 'c3ludGhldGlj');
  assert.equal(stripDataUrl('data:image/webp;base64,aGVsbG8='), 'aGVsbG8=');
  assert.equal(stripDataUrl('c3ludGhldGlj'), null);
  assert.equal(stripDataUrl('data:text/plain;base64,aGVsbG8='), null);
  assert.equal(stripDataUrl('data:image/png;base64,'), null);
});

test('edits keep, remove or replace the photo explicitly', () => {
  assert.equal(editPhotoAction(false, false), 'keep');
  assert.equal(editPhotoAction(false, true), 'remove');
  assert.equal(editPhotoAction(true, false), 'replace');
  assert.equal(editPhotoAction(true, true), 'replace');
});

test('empty crop fields cover the whole original image', () => {
  assert.deepEqual(resolveCrop(EMPTY_CROP, 640, 480), { x: 0, y: 0, width: 640, height: 480 });
});

test('explicit crops stay inside the decoded original bounds', () => {
  assert.deepEqual(resolveCrop({ x: '10', y: '20', width: '30', height: '40' }, 640, 480),
    { x: 10, y: 20, width: 30, height: 40 });
  assert.deepEqual(resolveCrop({ x: '600', y: '440', width: '', height: '' }, 640, 480),
    { x: 600, y: 440, width: 40, height: 40 });
  assert.equal(resolveCrop({ x: '600', y: '0', width: '100', height: '10' }, 640, 480), null);
  assert.equal(resolveCrop({ x: '0', y: '0', width: '0', height: '10' }, 640, 480), null);
  assert.equal(resolveCrop({ x: '-1', y: '0', width: '10', height: '10' }, 640, 480), null);
  assert.equal(resolveCrop({ x: 'a', y: '0', width: '10', height: '10' }, 640, 480), null);
  assert.equal(resolveCrop({ x: '700', y: '0', width: '', height: '10' }, 640, 480), null);
  assert.equal(resolveCrop(EMPTY_CROP, 0, 0), null);
});
