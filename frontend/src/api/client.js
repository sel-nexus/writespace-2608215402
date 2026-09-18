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
export async function getJson(path) {
  const response = await fetch(apiUrl(path), { headers: { Accept: 'application/json' } });
  if (!response.ok) {
    throw new Error(`The reading room is unavailable (${response.status}).`);
  }
  return response.json();
}
