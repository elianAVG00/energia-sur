import { AssistantPanel } from '../features/assistant/AssistantPanel.tsx';

// CU03 runtime lives inside this single root-layout mount.
export function ChatMount() {
  return <aside data-chat-mount="cu03" aria-label="Asistente CU03" className="fixed right-3 bottom-3 z-10 w-[min(92vw,24rem)] rounded-xl border border-border bg-card p-3 shadow-sm sm:right-6 sm:bottom-6">
    <AssistantPanel />
  </aside>;
}
