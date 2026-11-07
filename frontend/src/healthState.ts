import type { HealthResponse } from './health.ts';

export type HealthState =
  | { status: 'loading' }
  | { status: 'success'; response: HealthResponse }
  | { status: 'error'; message: string };

export type HealthAction =
  | { type: 'loading' }
  | { type: 'success'; response: HealthResponse }
  | { type: 'error'; message: string };

export function healthReducer(_state: HealthState, action: HealthAction): HealthState {
  switch (action.type) {
    case 'loading':
      return { status: 'loading' };
    case 'success':
      return { status: 'success', response: action.response };
    case 'error':
      return { status: 'error', message: action.message };
  }
}
