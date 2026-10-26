import { z } from 'zod';
type Principal = { id: string };
export class CredentialError extends Error {}
let verifier: (token: string) => Promise<Principal>;
export function setVerifier(value: typeof verifier) { verifier = value; }
function verifyToken(token: string) { return verifier(token); }
type WireRequest = { headers: Record<string, string | undefined>; user?: Principal };
type WireResponse = { status(code: number): WireResponse; json(value: unknown): Response };
type NextApiHandler = (req: WireRequest, res: WireResponse) => Response | Promise<Response>;
type NextRequest = Request;
const NextResponse = Response;
type CreateInput = { email: string; name: string };
type PublicUser = CreateInput & { id: string };
let createUser: (input: CreateInput) => Promise<PublicUser>;
export function setCreateUser(value: typeof createUser) { createUser = value; }
type RetryOptions = { maxAttempts: number; retryable: (error: unknown) => boolean; signal?: AbortSignal };
