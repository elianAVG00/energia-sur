// Presentation-only section wrapper for the authenticated account workspace.
// It adds the section heading and anchor target without another card layer.
import type { ReactNode } from 'react';

export function AccountSection({ id, title, description, children }: {
  id: string; title: string; description?: ReactNode; children: ReactNode;
}) {
  const headingId = `${id}-heading`;
  return <section id={id} aria-labelledby={headingId} className="scroll-mt-24 space-y-4">
    <div className="space-y-1">
      <h2 id={headingId} className="text-2xl font-bold tracking-tight">{title}</h2>
      {description && <p className="max-w-3xl text-sm text-muted-foreground">{description}</p>}
    </div>
    {children}
  </section>;
}
