// ISC-licensed adaptation of Varnan-Tech/opendirectory at bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4.
// 25 October 2026: bound downloads, redirects and decoding; validate inputs and redact errors.
// Preserve the accompanying LICENSE and original source provenance.
import sharp from 'sharp';

const MAX_BYTES = 4 * 1024 * 1024;
const MAX_PIXELS = 16 * 1024 * 1024;
const MAX_REDIRECTS = 3;
const REDIRECT_STATUSES = new Set([301, 302, 303, 307, 308]);
const MEDIA_TYPES = new Set(['image/png', 'image/jpeg', 'image/webp', 'image/svg+xml', 'image/avif', 'image/gif', 'image/tiff']);
const HEADERS = { 'User-Agent': 'blog-cover-image-cli', Accept: 'image/*' };

function admittedUrl(value, base) {
  const url = new URL(value, base);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) {
    throw new Error('Unsupported logo URL');
  }
  return url;
}

async function responseFor(url, signal, budget) {
  while (true) {
    signal.throwIfAborted();
    const response = await fetch(url, { headers: HEADERS, signal, redirect: 'manual' });
    if (!REDIRECT_STATUSES.has(response.status)) return response;
    const location = response.headers.get('location');
    await response.body?.cancel();
    if (!location || budget.redirects >= MAX_REDIRECTS) throw new Error('Logo redirect limit');
    budget.redirects++;
    url = admittedUrl(location, url);
  }
}

async function imageBytes(response, signal) {
  const media = response.headers.get('content-type')?.split(';', 1)[0].trim().toLowerCase();
  const length = response.headers.get('content-length');
  if (!response.ok || !MEDIA_TYPES.has(media) || !response.body ||
      (length !== null && (!/^\d+$/.test(length) || Number(length) > MAX_BYTES))) {
    await response.body?.cancel();
    throw new Error('Unsupported logo response');
  }
  const reader = response.body.getReader();
  const chunks = [];
  let bytes = 0;
  try {
    while (true) {
      signal.throwIfAborted();
      const { value, done } = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > MAX_BYTES) throw new Error('Logo byte limit');
      chunks.push(value);
    }
  } catch (error) {
    await reader.cancel();
    throw error;
  } finally {
    reader.releaseLock();
  }
  return Buffer.concat(chunks, bytes);
}

/** Download an explicitly requested logo, with one shared ten-second download deadline. */
export async function fetchLogo(logoInput, clientId) {
  try {
    if (typeof logoInput !== 'string' || !logoInput.trim()) return null;
    let urls;
    if (/^https?:\/\//i.test(logoInput)) {
      urls = [admittedUrl(logoInput)];
    } else {
      const domain = admittedUrl(`https://${logoInput}`);
      if (domain.port || domain.pathname !== '/' || domain.search || domain.hash ||
          !/^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$/i.test(domain.hostname)) return null;
      const brandfetch = new URL(`https://cdn.brandfetch.io/domain/${domain.hostname}/w/820/h/110/theme/dark/logo`);
      if (clientId) brandfetch.searchParams.set('c', clientId);
      urls = [brandfetch, new URL(`https://logos.hunter.io/${domain.hostname}`), new URL(`https://icon.horse/icon/${domain.hostname}`)];
    }
    const signal = AbortSignal.timeout(10000);
    const budget = { redirects: 0 };
    for (const url of urls) {
      try {
        const response = await responseFor(url, signal, budget);
        const input = await imageBytes(response, signal);
        const decoder = sharp(input, { limitInputPixels: MAX_PIXELS, failOn: 'error' });
        const metadata = await decoder.metadata();
        if ((metadata.pages ?? 1) !== 1) throw new Error('Multiple image pages');
        const png = await decoder.png().toBuffer();
        signal.throwIfAborted();
        if (png.length > MAX_BYTES) throw new Error('Encoded logo byte limit');
        return { data: png.toString('base64'), mimeType: 'image/png' };
      } catch {
        if (signal.aborted) break;
      }
    }
  } catch {
    // Input and fetch errors can contain complete URLs, credentials and query values.
  }
  console.error('Logo unavailable: invalid response or resource limit.');
  return null;
}
