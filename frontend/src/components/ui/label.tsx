// Local adaptation of shadcn/ui new-york-v4 label (MIT), 2026-11-07.
// https://github.com/shadcn-ui/ui/tree/main/apps/v4/registry/new-york-v4/ui
import type { ComponentProps } from 'react';
import { cn } from '../../lib/utils.ts';

export function Label({ className, ...props }: ComponentProps<'label'>) {
  return <label data-slot="label" className={cn('text-sm font-medium leading-5', className)} {...props} />;
}
