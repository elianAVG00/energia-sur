import { useStore } from 'zustand';
import { createStore } from 'zustand/vanilla';
import type { Session } from '../diaryApi.ts';

export interface SessionState {
  session: Session | null;
  selectedDomicileId: string;
  generation: number;
  expired: boolean;
  setSession: (session: Session, expectedGeneration?: number) => boolean;
  clearSession: (expectedGeneration?: number, expired?: boolean) => boolean;
  selectDomicile: (id: string) => void;
}

// No persist/devtools middleware: private identity and CSRF exist in memory only.
export function createSessionStore() {
  return createStore<SessionState>()((set, get) => ({
    session: null, selectedDomicileId: '', generation: 0, expired: false,
    setSession: (session, expectedGeneration) => {
      if (expectedGeneration !== undefined && get().generation !== expectedGeneration) return false;
      set(state => ({ session, selectedDomicileId: '', generation: state.generation + 1, expired: false }));
      return true;
    },
    clearSession: (expectedGeneration, expired = false) => {
      if (expectedGeneration !== undefined && get().generation !== expectedGeneration) return false;
      set(state => ({ session: null, selectedDomicileId: '', generation: state.generation + 1, expired }));
      return true;
    },
    selectDomicile: id => set({ selectedDomicileId: get().session ? id : '' }),
  }));
}

export type SessionStore = ReturnType<typeof createSessionStore>;
export const sessionStore = createSessionStore();
export function useSessionStore<T>(selector: (state: SessionState) => T): T {
  return useStore(sessionStore, selector);
}
