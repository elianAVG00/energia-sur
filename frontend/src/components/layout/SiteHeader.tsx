import type { ReactNode } from 'react';
import { Button } from '../ui/button.tsx';

export function SiteHeader({ nav, showLogout, pending, onLogout }: {
  nav: ReactNode;
  showLogout: boolean;
  pending: boolean;
  onLogout: () => void;
}) {
  return <header className="sticky top-0 z-30 border-b border-border bg-card/95 backdrop-blur">
    <div className="mx-auto flex w-full max-w-[75rem] flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3 sm:px-6">
      <div className="flex items-center gap-3">
        <span aria-hidden="true" className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <svg viewBox="0 0 24 24" fill="none" className="size-5" aria-hidden="true">
            <path d="M13 2 4.5 13.5H11l-1 8.5 8.5-11.5H12l1-8.5Z" fill="currentColor" />
          </svg>
        </span>
        <span className="flex flex-col leading-tight">
          <span className="text-lg font-semibold tracking-tight">Energía Sur</span>
          <span className="text-xs text-muted-foreground">Zona Sur · Edesur</span>
        </span>
      </div>
      <div className="order-3 w-full sm:order-none sm:w-auto sm:flex-1">{nav}</div>
      {showLogout && <div className="ms-auto sm:ms-0">
        <Button type="button" variant="outline" size="sm" disabled={pending} onClick={onLogout}>
          Cerrar sesión
        </Button>
      </div>}
    </div>
  </header>;
}
