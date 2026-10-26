
export const post = POST;
export async function auth(request: Request, handler: (request: Request, principal: Principal) => Response | Promise<Response>): Promise<Response> {
 const wire: WireRequest = { headers: { authorization: request.headers.get('authorization') ?? undefined } };
 let status = 200;
 const response: WireResponse = { status(code) { status = code; return this; }, json(value) { return Response.json(value, { status }); } };
 return await withAuth(() => handler(request, wire.user!))(wire, response);
}
export function retryRead<T>(operation: (signal?: AbortSignal) => Promise<T>, options: RetryOptions): Promise<T> {
 return fetchWithRetry(() => operation(options.signal), options.maxAttempts);
}
export function errorResponse(error: unknown): Response { return errorHandler(error, new Request('https://example.invalid/')); }
export function buildRecord(level: 'info' | 'warn' | 'error', message: string, context: Record<string, unknown>): Record<string, unknown> {
 const previous = console.log;
 let record: Record<string, unknown> | undefined;
 console.log = (value: unknown) => { record = JSON.parse(String(value)) as Record<string, unknown>; };
 try { new Logger().log(level, message, context); } finally { console.log = previous; }
 if (!record) throw new Error('Logger produced no record');
 return record;
}
