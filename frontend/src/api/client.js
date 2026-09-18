/**
 * Build a same-origin API URL from the configured public base and request path.
 *
 * @param {string} path - API path beginning with a slash.
 * @returns {string} A resolved API request URL.
 */
export function apiUrl(path) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '';
  return `${baseUrl}${path}`;
}

/**
 * Request JSON and surface safe, human-readable errors for callers.
 *
 * @param {string} path - API path beginning with a slash.
 * @returns {Promise<unknown>} Parsed JSON response body.
 */
export async function requestJson(path, options = {}) {
  const { method = 'GET', body, auth = true } = options;
  const token = auth ? window.localStorage.getItem('ws.access_token') : null;
  const response = await fetch(apiUrl(path), {
    method,
    headers: { Accept: 'application/json', ...(body ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.message || `The request could not be completed (${response.status}).`);
    error.status = response.status;
    if (response.status === 401 && !path.startsWith('/api/auth/login') && !path.startsWith('/api/auth/register')) {
      window.dispatchEvent(new Event('writespace:unauthorized'));
    }
    throw error;
  }
  return payload;
}

export function getJson(path) {
  return requestJson(path, { auth: false });
}
