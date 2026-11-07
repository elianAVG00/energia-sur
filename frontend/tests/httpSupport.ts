import { AxiosHeaders } from 'axios';
import type { AxiosAdapter, InternalAxiosRequestConfig } from 'axios';
import { createHttpClient } from '../src/lib/http.ts';
import { createSessionStore } from '../src/stores/session.ts';

export const session = { account: { id: 'account-a', username: 'synthetic' }, csrf_token: 'current-csrf' };
export function mockHttp(
  data: unknown, status = 200, contentType = 'application/json',
  inspect?: (config: InternalAxiosRequestConfig) => void,
) {
  const store = createSessionStore();
  store.getState().setSession(session);
  const adapter: AxiosAdapter = async config => {
    inspect?.(config);
    return { data, status, statusText: String(status), headers: new AxiosHeaders({ 'content-type': contentType }), config };
  };
  return { http: createHttpClient({ store, adapter }), store };
}
