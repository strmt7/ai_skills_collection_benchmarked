import { useCallback, useEffect, useRef, useState } from 'react';

type State<T> = { key: string; data: T | null; error: unknown; loading: boolean };

// Client-only example, not a cache. The key must encode every request input.
export function useQuery<T>(
  key: string,
  fetcher: (signal: AbortSignal) => Promise<T>,
  options?: { enabled?: boolean },
) {
  const enabled = options?.enabled !== false;
  const [state, setState] = useState<State<T>>({ key, data: null, error: null, loading: false });
  const context = useRef({ key, fetcher, enabled, active: false });
  const generation = useRef(0);
  const controller = useRef<AbortController | null>(null);

  useEffect(() => {
    context.current = { ...context.current, key, fetcher, enabled };
  });

  const refetch = useCallback(async (): Promise<void> => {
    const request = context.current;
    if (!request.active || !request.enabled) return;
    const current = ++generation.current;
    controller.current?.abort();
    const abort = new AbortController();
    controller.current = abort;
    setState({ key: request.key, data: null, error: null, loading: true });
    const valid = () => context.current.active && generation.current === current;
    try {
      const data = await request.fetcher(abort.signal);
      if (valid()) setState({ key: request.key, data, error: null, loading: false });
    } catch (error) {
      if (valid()) setState({ key: request.key, data: null, error, loading: false });
    } finally {
      if (valid()) controller.current = null;
    }
  }, []);

  useEffect(() => {
    context.current.active = true;
    if (enabled) void refetch();
    else setState({ key, data: null, error: null, loading: false });
    return () => {
      context.current.active = false;
      ++generation.current;
      controller.current?.abort();
      controller.current = null;
    };
  }, [key, enabled, refetch]);

  const visible = enabled && state.key === key;
  return {
    data: visible ? state.data : null,
    error: visible ? state.error : null,
    loading: visible ? state.loading : false,
    refetch,
  };
}
