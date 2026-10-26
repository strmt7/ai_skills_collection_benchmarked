import { z } from 'zod';

export function sorted<T extends { volume: number }>(items: readonly T[]): T[] {
  return [...items].sort((a, b) => b.volume - a.volume);
}

export async function fetchData(url: string, signal?: AbortSignal): Promise<unknown> {
  const response = await fetch(url, { signal });
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  return response.json();
}

export function invalidIssues() {
  // A small compatibility example; real schemas belong at the caller's boundary.
  const parsed = z.string().safeParse(42);
  return parsed.success ? [] : parsed.error.issues;
}
