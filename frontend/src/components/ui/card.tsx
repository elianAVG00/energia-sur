// Adapted from shadcn/ui new-york-v4 card (MIT), reviewed 2026-11-07.
// https://github.com/shadcn-ui/ui/blob/main/apps/v4/registry/new-york-v4/ui/card.tsx
// Titles use native headings rather than unstructured divs.
import type { ComponentProps } from 'react';
import { cn } from '../../lib/utils.ts';

export function Card({ className, ...props }: ComponentProps<'section'>) { return <section data-slot="card" className={cn('min-w-0 rounded-xl border border-border bg-card py-6 text-card-foreground shadow-sm', className)} {...props} />; }
export function CardHeader({ className, ...props }: ComponentProps<'div'>) { return <div data-slot="card-header" className={cn('mb-5 space-y-2 px-6', className)} {...props} />; }
export function CardTitle({ className, ...props }: ComponentProps<'h2'>) { return <h2 data-slot="card-title" className={cn('text-xl font-semibold leading-tight', className)} {...props} />; }
export function CardContent({ className, ...props }: ComponentProps<'div'>) { return <div data-slot="card-content" className={cn('space-y-4 px-6', className)} {...props} />; }
export function CardFooter({ className, ...props }: ComponentProps<'div'>) { return <div data-slot="card-footer" className={cn('mt-5 flex flex-wrap items-center gap-3 px-6', className)} {...props} />; }
