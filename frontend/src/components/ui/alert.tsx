// Local adaptation of shadcn/ui new-york-v4 alert (MIT), 2026-11-07.
// https://github.com/shadcn-ui/ui/tree/main/apps/v4/registry/new-york-v4/ui
import type { ComponentProps } from 'react';
import { cn } from '../../lib/utils.ts';

export function Alert({ className, role = 'alert', ...props }: ComponentProps<'div'>) { return <div data-slot="alert" role={role} className={cn('rounded-lg border border-border bg-card px-4 py-3 text-sm break-words', role === 'alert' && 'border-destructive/50 text-destructive', className)} {...props} />; }
