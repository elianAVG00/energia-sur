// Local adaptation of shadcn/ui new-york-v4 table (MIT), 2026-11-07.
// https://github.com/shadcn-ui/ui/tree/main/apps/v4/registry/new-york-v4/ui
import type { ComponentProps } from 'react';
import { cn } from '../../lib/utils.ts';

export function Table({ className, ...props }: ComponentProps<'table'>) { return <div data-slot="table-container" className="relative w-full overflow-x-auto rounded-md border border-border" tabIndex={0} role="region" aria-label="Cortes registrados"><table data-slot="table" className={cn('w-full text-left text-sm', className)} {...props} /></div>; }
export function TableHeader(props: ComponentProps<'thead'>) { return <thead data-slot="table-header" {...props} />; }
export function TableBody(props: ComponentProps<'tbody'>) { return <tbody data-slot="table-body" {...props} />; }
export function TableRow({ className, ...props }: ComponentProps<'tr'>) { return <tr data-slot="table-row" className={cn('border-b border-border last:border-0 hover:bg-muted/50', className)} {...props} />; }
export function TableHead({ className, ...props }: ComponentProps<'th'>) { return <th data-slot="table-head" className={cn('h-12 px-3 font-semibold whitespace-nowrap', className)} {...props} />; }
export function TableCell({ className, ...props }: ComponentProps<'td'>) { return <td data-slot="table-cell" className={cn('max-w-80 px-3 py-3 align-top break-words', className)} {...props} />; }
