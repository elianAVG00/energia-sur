import type { ReactNode } from 'react';
import { ChatMount } from '../components/ChatMount.tsx';
import { SiteFooter } from '../components/layout/SiteFooter.tsx';
import { SiteHeader } from '../components/layout/SiteHeader.tsx';

export function AppLayout({ children, title = 'Diario de interrupciones', description, nav, showLogout, pending, onLogout }: {
  children: ReactNode;
  title?: string;
  description?: string;
  nav: ReactNode;
  showLogout: boolean;
  pending: boolean;
  onLogout: () => void;
}) {
  return <div className="flex min-h-screen flex-col">
    <a href="#contenido"
      className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-primary-foreground focus:shadow-lg">
      Saltar al contenido
    </a>
    <SiteHeader nav={nav} showLogout={showLogout} pending={pending} onLogout={onLogout} />
    <main id="contenido" tabIndex={-1}
      className="mx-auto w-full max-w-[75rem] flex-1 scroll-mt-24 space-y-6 px-4 pt-8 pb-36 sm:px-6">
      <div className="space-y-2 border-b border-border pb-5">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{title}</h1>
        {description && <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">{description}</p>}
      </div>
      {children}
    </main>
    <SiteFooter />
    <ChatMount />
  </div>;
}
