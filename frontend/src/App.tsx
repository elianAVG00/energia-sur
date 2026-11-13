import { useEffect, useState } from 'react';
import { diaryApi, DiaryError, errorMessage } from './diaryApi.ts';
import { useRequestScope } from './useRequestScope.ts';
import { sessionStore, useSessionStore } from './stores/session.ts';
import { AppLayout } from './layouts/AppLayout.tsx';
import { Alert } from './components/ui/alert.tsx';
import { Button } from './components/ui/button.tsx';
import { LoginForm } from './features/diary/forms.tsx';
import { Workspace } from './features/diary/Workspace.tsx';
import { OutagesPanel } from './features/outages/OutagesPanel.tsx';
import { ScheduledWorksPanel } from './features/scheduled-works/ScheduledWorksPanel.tsx';
import { AdminPanel } from './features/admin/AdminPanel.tsx';

export default function App() {
  const scope = useRequestScope();
  const [view, setView] = useState<'outages' | 'works' | 'admin' | 'account'>('account');
  const session = useSessionStore(state => state.session);
  const isAdmin = session?.account.role === 'admin';
  const generation = useSessionStore(state => state.generation);
  const expired = useSessionStore(state => state.expired);
  const [pending, setPending] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (view === 'admin' && !isAdmin) setView('account');
  }, [view, isAdmin]);

  useEffect(() => {
    const request = scope.begin('session');
    const expectedGeneration = sessionStore.getState().generation;
    void diaryApi.session(request.signal).then(result => {
      if (request.isCurrent()) sessionStore.getState().setSession(result, expectedGeneration);
    }).catch((reason: unknown) => {
      if (request.isCurrent() && sessionStore.getState().generation === expectedGeneration && !(reason instanceof DiaryError && reason.status === 401)) setError(errorMessage(reason));
    }).finally(() => { if (request.isCurrent()) setPending(false); });
  }, [scope]);

  async function login(values: { username: string; password: string }) {
    const request = scope.begin('session');
    const expectedGeneration = sessionStore.getState().generation;
    setPending(true); setError('');
    try {
      const result = await diaryApi.login(values.username, values.password, request.signal);
      if (request.isCurrent()) sessionStore.getState().setSession(result, expectedGeneration);
    } catch (reason: unknown) {
      if (request.isCurrent() && sessionStore.getState().generation === expectedGeneration) setError(errorMessage(reason));
    } finally { if (request.isCurrent()) setPending(false); }
  }
  async function logout() {
    if (!session) return;
    const csrf = session.csrf_token;
    scope.invalidate();
    sessionStore.getState().clearSession(generation);
    const clearedGeneration = sessionStore.getState().generation;
    setPending(true); setError('');
    const request = scope.begin('session');
    try { await diaryApi.logout(csrf, request.signal); }
    catch (reason: unknown) {
      if (request.isCurrent() && sessionStore.getState().generation === clearedGeneration) setError(`No se confirmó el cierre de sesión: ${errorMessage(reason)}`);
    } finally { if (request.isCurrent()) setPending(false); }
  }

  return <AppLayout title={view === 'outages' ? 'Cortes eléctricos' : view === 'works' ? 'Trabajos programados' : view === 'admin' ? 'Administración de fuentes' : 'Diario de interrupciones'}>
    <nav aria-label="Secciones" className="flex flex-wrap gap-2">
      <Button type="button" variant={view === 'outages' ? 'default' : 'outline'}
        aria-current={view === 'outages' ? 'page' : undefined}
        onClick={() => setView('outages')}>Cortes</Button>
      <Button type="button" variant={view === 'works' ? 'default' : 'outline'}
        aria-current={view === 'works' ? 'page' : undefined}
        onClick={() => setView('works')}>Trabajos</Button>
      {isAdmin && <Button type="button" variant={view === 'admin' ? 'default' : 'outline'}
        aria-current={view === 'admin' ? 'page' : undefined}
        onClick={() => setView('admin')}>Administración</Button>}
      <Button type="button" variant={view === 'account' ? 'default' : 'outline'}
        aria-current={view === 'account' ? 'page' : undefined}
        onClick={() => setView('account')}>Mi cuenta</Button>
    </nav>
    {view === 'outages' && <OutagesPanel />}
    {view === 'works' && <ScheduledWorksPanel />}
    {view === 'admin' && isAdmin && <AdminPanel />}
    {view === 'account' && <>
      {error && <Alert>{error}</Alert>}
      {expired && !session && <Alert>La sesión venció. Ingresá nuevamente.</Alert>}
      {session ? <>
        <div className="flex flex-wrap items-center justify-between gap-3"><p>Cuenta: {session.account.username}</p><Button type="button" variant="outline" disabled={pending} onClick={() => void logout()}>Cerrar sesión</Button></div>
        <Workspace key={`${generation}:${session.account.id}`} session={session} generation={generation} />
      </> : <LoginForm key={generation} pending={pending} login={login} />}
    </>}
    {pending && <p role="status">Comprobando sesión…</p>}
  </AppLayout>;
}
