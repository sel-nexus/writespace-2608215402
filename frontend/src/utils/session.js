export const ACCESS_TOKEN_KEY = 'ws.access_token';
export const PROFILE_KEY = 'ws.profile';

/**
 * Return a valid persisted bearer token if one exists.
 *
 * @returns {string|null} Persisted access token or null.
 */
export function getAccessToken() {
  const token = window.localStorage.getItem(ACCESS_TOKEN_KEY);
  return token && token.trim() ? token : null;
}

/**
 * Return a safely parsed profile or clear malformed session storage.
 *
 * @returns {object|null} Safe persisted profile or null.
 */
export function getProfile() {
  try {
    const value = window.localStorage.getItem(PROFILE_KEY);
    const parsed = value ? JSON.parse(value) : null;
    if (!parsed || typeof parsed !== 'object' || typeof parsed.id !== 'number' || typeof parsed.username !== 'string') {
      throw new Error('Invalid profile');
    }
    return parsed;
  } catch {
    clearSession();
    return null;
  }
}

/**
 * Persist only a token and safe profile from a server response.
 *
 * @param {{access_token: string, user: object}} session - Server-issued session data.
 * @returns {void}
 */
export function saveSession(session) {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, session.access_token);
  window.localStorage.setItem(PROFILE_KEY, JSON.stringify(session.user));
}

/**
 * Clear all WriteSpace session storage.
 *
 * @returns {void}
 */
export function clearSession() {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(PROFILE_KEY);
}
