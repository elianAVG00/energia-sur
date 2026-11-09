import { sessionStore } from '../../stores/session.ts';
import type { ReadingInput } from './api.ts';

export interface CreateAttempt { key: string; input: ReadingInput }
export interface EditAttempt { readingId: string; version: number }

// Attempts are private, session-scoped and memory-only. Never persist image data or keys.
const creates = new Map<string, CreateAttempt>();
const edits = new Map<string, EditAttempt>();
let generation = sessionStore.getState().generation;
sessionStore.subscribe(state => {
  if (state.generation !== generation) {
    generation = state.generation;
    creates.clear();
    edits.clear();
  }
});

// crypto.randomUUID is only exposed in secure contexts; getRandomValues is not.
export function newRequestKey(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = ((bytes[6] ?? 0) & 0x0f) | 0x40;
  bytes[8] = ((bytes[8] ?? 0) & 0x3f) | 0x80;
  const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function getCreateAttempt(meterId: string): CreateAttempt | undefined { return creates.get(meterId); }
export function setCreateAttempt(meterId: string, attempt: CreateAttempt): void { creates.set(meterId, attempt); }
export function clearCreateAttempt(meterId: string, attempt: CreateAttempt): void {
  if (creates.get(meterId) === attempt) creates.delete(meterId);
}
export function getEditAttempt(meterId: string): EditAttempt | undefined { return edits.get(meterId); }
export function setEditAttempt(meterId: string, attempt: EditAttempt): void { edits.set(meterId, attempt); }
export function clearEditAttempt(meterId: string, attempt: EditAttempt): void {
  if (edits.get(meterId) === attempt) edits.delete(meterId);
}
