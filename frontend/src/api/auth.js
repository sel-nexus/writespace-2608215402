import { requestJson } from './client';

/**
 * Register a new WriteSpace account.
 *
 * @param {{display_name: string, username: string, password: string, confirm_password: string}} payload - Registration values.
 * @returns {Promise<{access_token: string, token_type: string, user: object}>} Issued session payload.
 */
export function registerAccount(payload) {
  return requestJson('/api/auth/register', { method: 'POST', body: payload, auth: false });
}

/**
 * Authenticate an existing WriteSpace account.
 *
 * @param {{username: string, password: string}} payload - Login credentials.
 * @returns {Promise<{access_token: string, token_type: string, user: object}>} Issued session payload.
 */
export function loginAccount(payload) {
  return requestJson('/api/auth/login', { method: 'POST', body: payload, auth: false });
}

/**
 * Fetch the active user's verified profile.
 *
 * @returns {Promise<object>} Safe current-user profile.
 */
export function getCurrentUser() {
  return requestJson('/api/auth/me');
}
