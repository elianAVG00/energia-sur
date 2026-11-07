import { useEffect, useState } from 'react';
import { RequestScope } from './diaryState.ts';

export function useRequestScope(): RequestScope {
  const [scope] = useState(() => new RequestScope());
  useEffect(() => () => scope.invalidate(), [scope]);
  return scope;
}
