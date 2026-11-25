import { randomUUID } from 'node:crypto';
import { once } from 'node:events';
import { createServer, request } from 'node:http';

export async function withFixtureHttp(handler, run) {
  const endpointId = 'ai-skills-' + randomUUID();
  const socketPath = process.platform === 'win32' ? '\\\\.\\pipe\\' + endpointId : '\0' + endpointId;
  const server = createServer(handler);
  try {
    await once(server.listen(socketPath), 'listening');
    return await run((path, method = 'GET') => new Promise((resolve, reject) => {
      const call = request({ socketPath, path, method, agent: false, headers: { host: 'localhost' } }, response => {
        response.once('error', reject);
        response.once('end', () => resolve(response.statusCode));
        response.resume();
      });
      call.once('error', reject);
      call.setTimeout(30000, () => call.destroy(new Error('Fixture HTTP request timed out')));
      call.end();
    }));
  } finally {
    if (server.listening) {
      await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
    }
  }
}
