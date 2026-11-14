import type { ReactNode } from 'react';
import { ChatMount } from '../components/ChatMount.tsx';

export function AppLayout({ children, title = 'Diario de interrupciones' }: {
  children: ReactNode; title?: string;
}) {
  return <>
    <main className="mx-auto w-full max-w-6xl space-y-6 px-4 pt-8 pb-36 sm:px-6">
      <header className="border-b border-border pb-6"><h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{title}</h1></header>
      {children}
    </main>
    <ChatMount />
  </>;
}
