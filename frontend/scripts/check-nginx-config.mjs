import { readFile } from 'node:fs/promises';

const config = await readFile(new URL('../nginx.conf', import.meta.url), 'utf8');

if (!/location\s+\/api\/\s*\{[\s\S]*proxy_pass\s+http:\/\/backend:8000\s*;/.test(config)) {
  throw new Error('Nginx must proxy /api/ requests to the backend service on port 8000.');
}
if (!/location\s+\/\s*\{[\s\S]*try_files\s+\$uri\s+\$uri\/\s+\/index\.html\s*;/.test(config)) {
  throw new Error('Nginx must retain the SPA fallback route.');
}
