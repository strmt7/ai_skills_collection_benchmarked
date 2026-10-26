import { z } from 'zod';

type Parsed<T> = { ok: true; value: T } | { ok: false; response: Response };

// The framework must enforce media type, body byte limits and deadlines first.
export async function readValidatedJSON<T>(request: Request, schema: z.ZodType<T>): Promise<Parsed<T>> {
  let body: unknown;
  try {
    body = await request.json();
  } catch (error) {
    if (!(error instanceof SyntaxError)) throw error;
    return {
      ok: false,
      response: Response.json({ error: { code: 'invalid_json', message: 'Invalid JSON body' } }, { status: 400 }),
    };
  }
  const parsed = await schema.safeParseAsync(body);
  if (parsed.success) return { ok: true, value: parsed.data };
  return {
    ok: false,
    response: Response.json({
      error: {
        code: 'validation_error',
        message: 'Request validation failed',
        details: parsed.error.issues.map(issue => ({
          field: issue.path.map(String).join('.'), code: issue.code, message: issue.message,
        })),
      },
    }, { status: 422 }),
  };
}
