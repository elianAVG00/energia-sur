import { useCallback, useEffect, useReducer, useRef } from 'react';
import { fetchHealth, HealthError } from './health.ts';
import { healthReducer } from './healthState.ts';

export default function App() {
  const [state, dispatch] = useReducer(healthReducer, { status: 'loading' });
  const activeRequest = useRef<AbortController | null>(null);

  const checkHealth = useCallback(() => {
    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;
    dispatch({ type: 'loading' });

    void fetchHealth({ signal: controller.signal }).then(
      (response) => {
        if (activeRequest.current === controller && !controller.signal.aborted) {
          dispatch({ type: 'success', response });
        }
      },
      (error: unknown) => {
        if (activeRequest.current === controller && !controller.signal.aborted) {
          dispatch({
            type: 'error',
            message: error instanceof HealthError ? error.message : 'No se pudo comprobar la API.',
          });
        }
      },
    );
  }, []);

  useEffect(() => {
    checkHealth();
    return () => {
      activeRequest.current?.abort();
      activeRequest.current = null;
    };
  }, [checkHealth]);

  return (
    <main>
      <p className="eyebrow">Energia Sur · Desarrollo local</p>
      <h1>Conexión con la API</h1>
      <p>Esta pantalla comprueba únicamente que el servicio HTTP responde.</p>
      <section className={`health health--${state.status}`} aria-live="polite" aria-atomic="true">
        {state.status === 'loading' && <p role="status">Comprobando la API…</p>}
        {state.status === 'success' && (
          <>
            <h2>API disponible</h2>
            <p>Respuesta verificada de la última comprobación:</p>
            <pre>{JSON.stringify(state.response, null, 2)}</pre>
          </>
        )}
        {state.status === 'error' && (
          <div role="alert">
            <h2>No se pudo verificar la conexión</h2>
            <p>{state.message}</p>
          </div>
        )}
      </section>
      <button type="button" onClick={checkHealth}>Volver a comprobar</button>
      <p className="note">Tiempo límite: 5 segundos. No verifica la base de datos ni servicios externos.</p>
    </main>
  );
}
