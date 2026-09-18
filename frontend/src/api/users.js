import { requestJson } from './client';

/** Fetch administrator dashboard statistics from the server. */
export function getAdminStats() {
  return requestJson('/api/admin/stats');
}

/** Fetch safe user records for administrator account management. */
export async function listUsers() {
  const payload = await requestJson('/api/users');
  if (!Array.isArray(payload)) throw new Error('The account directory sent an unexpected response.');
  return payload;
}

/** Create an account using administrator-approved fields. */
export function createUser(payload) {
  return requestJson('/api/users', { method: 'POST', body: payload });
}

/** Deactivate an account without deleting its historical content. */
export function deactivateUser(id) {
  return requestJson(`/api/users/${encodeURIComponent(id)}/deactivate`, { method: 'PATCH' });
}

/** Permanently remove an eligible account while preserving post snapshots. */
export function deleteUser(id) {
  return requestJson(`/api/users/${encodeURIComponent(id)}`, { method: 'DELETE' });
}
