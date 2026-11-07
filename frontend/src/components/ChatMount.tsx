import { Button } from './ui/button.tsx';

// CU03 will integrate its runtime here, never inside a keyed feature workspace.
export function ChatMount() {
  return <aside data-chat-mount="cu03" aria-label="Asistente CU03" className="fixed right-3 bottom-3 z-10 max-w-[calc(100vw-1.5rem)] rounded-xl border border-border bg-card p-3 shadow-sm sm:right-6 sm:bottom-6">
    <Button type="button" variant="secondary" disabled aria-describedby="chat-unavailable">Asistente CU03</Button>
    <p id="chat-unavailable" className="mt-1 text-xs text-muted-foreground">No disponible · integración pendiente</p>
  </aside>;
}
