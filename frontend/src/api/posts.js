import { getJson, requestJson } from './client';

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

/** Fetch a bounded authenticated library through the central token-aware client. */
export async function listPosts() {
  const payload = await requestJson('/api/posts?limit=100');
  if (!Array.isArray(payload)) {
    throw new Error('The library sent an unexpected response.');
  }
  return payload;
}

/** Fetch one authenticated post by its server-issued identifier. */
export async function getPost(id) {
  return requestJson(`/api/posts/${encodeURIComponent(id)}`);
}

/** Create a post using the central token-aware API client. */
export function createPost(input) {
  return requestJson('/api/posts', { method: 'POST', body: input });
}

/** Update a post using the central token-aware API client. */
export function updatePost(id, input) {
  return requestJson(`/api/posts/${encodeURIComponent(id)}`, { method: 'PUT', body: input });
}

/** Delete a post using the central token-aware API client. */
export function deletePost(id) {
  return requestJson(`/api/posts/${encodeURIComponent(id)}`, { method: 'DELETE' });
}
