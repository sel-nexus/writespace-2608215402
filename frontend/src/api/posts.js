import { getJson } from './client';

/**
 * Fetch up to three current public editorial previews.
 *
 * @returns {Promise<Array<{id: number, title: string, excerpt: string, created_at: string}>>} Safe preview records.
 */
export async function getPublicPreviews() {
  const payload = await getJson('/api/public/posts?limit=3');
  if (!Array.isArray(payload)) {
    throw new Error('The reading room sent an unexpected response.');
  }
  return payload;
}
