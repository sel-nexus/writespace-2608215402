import { rm } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const frontendDir = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const rootDir = resolve(frontendDir, '..');
const backendDir = resolve(rootDir, 'backend');
const databasePath = '/tmp/writespace-playwright.db';
const python = `${process.env.HOME}/venvs/writespace/bin/python`;
const backendEnv = {
  ...process.env,
  DATABASE_URL: `sqlite:///${databasePath}`,
  CORS_ORIGINS: 'http://127.0.0.1:5173',
  JWT_SECRET: 'writespace-playwright-secret',
  SEED_ON_STARTUP: 'true',
};

await rm(databasePath, { force: true });
await rm(`${databasePath}-journal`, { force: true });
await rm(`${databasePath}-shm`, { force: true });
await rm(`${databasePath}-wal`, { force: true });

const backend = spawn(python, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], {
  cwd: backendDir,
  env: backendEnv,
  stdio: 'inherit',
});

function stopBackend() {
  if (!backend.killed) backend.kill('SIGTERM');
}

for (const signal of ['SIGINT', 'SIGTERM', 'exit']) process.on(signal, stopBackend);

for (let attempt = 0; attempt < 60; attempt += 1) {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/health');
    if (response.ok) break;
  } catch {
    // FastAPI is still starting.
  }
  if (attempt === 59) throw new Error('FastAPI did not become healthy at /api/health.');
  await new Promise((resolveDelay) => setTimeout(resolveDelay, 250));
}

const vite = spawn(process.execPath, ['node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', '5173', '--strictPort'], {
  cwd: frontendDir,
  env: { ...process.env, VITE_DEV_API_TARGET: 'http://127.0.0.1:8000' },
  stdio: 'inherit',
});
vite.on('exit', (code) => {
  stopBackend();
  process.exit(code ?? 1);
});
