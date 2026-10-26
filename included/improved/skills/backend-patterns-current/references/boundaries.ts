import { z } from 'zod';

export class CredentialError extends Error {}

export function withBearerAuth<P>(
  verify: (credential: string) => Promise<P>,
  handler: (request: Request, principal: P) => Response | Promise<Response>,
) {
  return async (request: Request): Promise<Response> => {
    const matched = request.headers.get('authorization')?.match(/^Bearer +([A-Za-z0-9._~+\/-]+=*)$/i);
    const unauthorized = () => Response.json({ error: 'Unauthorized' }, {
      status: 401, headers: { 'WWW-Authenticate': 'Bearer', 'Cache-Control': 'no-store' },
    });
    if (!matched) return unauthorized();
    let principal: P;
    try {
      principal = await verify(matched[1]);
    } catch (error) {
      if (error instanceof CredentialError) return unauthorized();
      throw error;
    }
    return handler(request, principal);
  };
}

type RetryOptions = {
  maxAttempts: number;
  retryable: (error: unknown) => boolean;
  signal?: AbortSignal;
};

function pause(milliseconds: number, signal?: AbortSignal): Promise<void> {
  signal?.throwIfAborted();
  return new Promise((resolve, reject) => {
    const finished = () => { signal?.removeEventListener('abort', cancelled); resolve(); };
    const timer = setTimeout(finished, milliseconds);
    const cancelled = () => {
      clearTimeout(timer);
      signal?.removeEventListener('abort', cancelled);
      reject(signal?.reason);
    };
    signal?.addEventListener('abort', cancelled, { once: true });
  });
}

// Caller must classify replay safety and supply an end-to-end deadline signal.
export async function retryRead<T>(operation: (signal?: AbortSignal) => Promise<T>, options: RetryOptions): Promise<T> {
  const { maxAttempts, retryable, signal } = options;
  if (!Number.isSafeInteger(maxAttempts) || maxAttempts < 1) throw new RangeError('maxAttempts must be a positive safe integer');
  for (let attempt = 0; ; attempt++) {
    signal?.throwIfAborted();
    try {
      const result = await operation(signal);
      signal?.throwIfAborted();
      return result;
    } catch (error) {
      signal?.throwIfAborted();
      const aborted = typeof error === 'object' && error !== null && 'name' in error && error.name === 'AbortError';
      if (aborted || attempt + 1 >= maxAttempts || !retryable(error)) throw error;
      await pause(Math.min(30_000, 1000 * 2 ** attempt), signal);
    }
  }
}

export function validationErrorResponse(error: unknown): Response {
  if (error instanceof z.ZodError) {
    return Response.json({ error: 'Validation failed', details: error.issues }, { status: 400 });
  }
  return Response.json({ error: 'Internal server error' }, { status: 500 });
}

export function buildLogRecord(level: 'info' | 'warn' | 'error', message: string, context: Record<string, unknown> = {}) {
  const record: Record<string, unknown> = { timestamp: new Date().toISOString(), level, message };
  for (const field of ['requestId', 'method', 'route']) {
    const value = context[field];
    if (typeof value === 'string' && value.length <= 256) record[field] = value;
  }
  return record;
}
