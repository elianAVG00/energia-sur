// Local adaptation of shadcn/ui new-york-v4 textarea (MIT), 2026-11-07.
// https://github.com/shadcn-ui/ui/tree/main/apps/v4/registry/new-york-v4/ui
import type { ComponentProps } from 'react';
import { cn } from '../../lib/utils.ts';

export function Textarea({ className, ...props }: ComponentProps<'textarea'>) {
  return <textarea data-slot="textarea" className={cn('flex min-h-24 w-full min-w-0 rounded-md border border-input bg-transparent px-3 py-2 text-base shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 aria-invalid:border-destructive disabled:cursor-not-allowed disabled:opacity-50', className)} {...props} />;
}
