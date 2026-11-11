import { useStore } from 'zustand';
import { createStore } from 'zustand/vanilla';
import type { HistoryTurn, Source } from './api.ts';

export type MessageStatus = 'streaming' | 'done' | 'error' | 'cancelled';
export type ConversationScope = 'temporary' | 'persistent';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: Source[];
  status: MessageStatus;
}

export interface AssistantState {
  messages: ChatMessage[];
  streaming: boolean;
  error: string;
  conversationId: string | null;
  scope: ConversationScope | null;
  updatedAt: number;
  ttlMs: number;
  addUser: (text: string) => void;
  beginAssistant: () => string;
  append: (id: string, text: string) => void;
  setSources: (id: string, sources: Source[]) => void;
  finish: (id: string, ok: boolean) => void;
  fail: (id: string, message: string) => void;
  setConversation: (id: string, scope: ConversationScope) => void;
  isExpired: (now?: number) => boolean;
  setError: (message: string) => void;
  cancel: () => void;
  reset: () => void;
}

function identifier(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

const viteEnv = (import.meta as {
  env?: { VITE_ASSISTANT_TTL_MINUTES?: string };
}).env;
export const HISTORY_MAX_CHARS = 4000;

export function priorHistory(
  messages: ChatMessage[],
  limit = 10,
  maxChars = HISTORY_MAX_CHARS,
): HistoryTurn[] {
  const recent = messages
    .filter(message => message.content.trim().length > 0)
    .slice(-limit)
    .map(message => ({
      role: message.role,
      content: message.content.slice(0, 2000),
    }));
  const kept: HistoryTurn[] = [];
  let total = 0;
  for (let index = recent.length - 1; index >= 0; index -= 1) {
    const turn = recent[index];
    if (!turn) {
      continue;
    }
    if (total + turn.content.length > maxChars) {
      break;
    }
    kept.unshift(turn);
    total += turn.content.length;
  }
  return kept;
}

const configuredTtl = Number(viteEnv?.VITE_ASSISTANT_TTL_MINUTES ?? '30');
const TEMPORARY_TTL_MS = Number.isFinite(configuredTtl) && configuredTtl > 0
  ? configuredTtl * 60_000
  : 30 * 60_000;

// In-memory only: visitor history stays in Zustand and expires after the TTL.
export function createAssistantStore() {
  return createStore<AssistantState>()((set, get) => ({
    messages: [],
    streaming: false,
    error: '',
    conversationId: null,
    scope: null,
    updatedAt: 0,
    ttlMs: TEMPORARY_TTL_MS,
    addUser: text => set(state => ({
      messages: [...state.messages, {
        id: identifier(), role: 'user', content: text, sources: [], status: 'done',
      }],
      streaming: true,
      error: '',
      updatedAt: Date.now(),
    })),
    beginAssistant: () => {
      const id = identifier();
      set(state => ({
        messages: [...state.messages, {
          id, role: 'assistant', content: '', sources: [], status: 'streaming',
        }],
        updatedAt: Date.now(),
      }));
      return id;
    },
    append: (id, text) => set(state => ({
      messages: state.messages.map(message => message.id === id
        ? { ...message, content: message.content + text }
        : message),
      updatedAt: Date.now(),
    })),
    setSources: (id, sources) => set(state => ({
      messages: state.messages.map(message => message.id === id
        ? { ...message, sources }
        : message),
      updatedAt: Date.now(),
    })),
    finish: (id, ok) => set(state => ({
      messages: state.messages.map(message => message.id === id
        ? { ...message, status: ok ? 'done' : 'error' }
        : message),
      streaming: false,
      updatedAt: Date.now(),
    })),
    fail: (id, message) => set(state => ({
      messages: state.messages.map(item => item.id === id
        ? { ...item, status: 'error' }
        : item),
      streaming: false,
      error: message,
      updatedAt: Date.now(),
    })),
    setConversation: (id, scope) => set({
      conversationId: id,
      scope,
      updatedAt: Date.now(),
    }),
    isExpired: (now = Date.now()) => {
      const state = get();
      return state.messages.length > 0
        && state.updatedAt > 0
        && now - state.updatedAt > state.ttlMs;
    },
    setError: message => set({ error: message, updatedAt: Date.now() }),
    cancel: () => set(state => ({
      messages: state.messages.map(message => message.status === 'streaming'
        ? { ...message, status: 'cancelled' }
        : message),
      streaming: false,
      updatedAt: Date.now(),
    })),
    reset: () => set({
      messages: [],
      streaming: false,
      error: '',
      conversationId: null,
      scope: null,
      updatedAt: 0,
    }),
  }));
}

export const assistantStore = createAssistantStore();

export function useAssistantStore<T>(selector: (state: AssistantState) => T): T {
  return useStore(assistantStore, selector);
}
