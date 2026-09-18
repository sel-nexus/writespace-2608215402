import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getPost, listPosts } from '../api/posts';
import Home from './Home';
import ReadBlog from './ReadBlog';

vi.mock('../api/posts', () => ({ getPost: vi.fn(), listPosts: vi.fn() }));

function renderAt(path, element) {
  return render(<MemoryRouter initialEntries={[path]}><Routes><Route path="*" element={element} /></Routes></MemoryRouter>);
}

describe('authenticated reading pages', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders loaded library cards from the API', async () => {
    listPosts.mockResolvedValue([{ id: 8, title: 'Server library note', excerpt: 'A safe excerpt.', content: 'Hidden here', author: null, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' }]);
    renderAt('/blogs', <Home />);
    expect(await screen.findByRole('heading', { name: 'Server library note' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Read Server library note' })).toHaveAttribute('href', '/blog/8');
  });

  it('shows an error and retries the library request', async () => {
    listPosts.mockRejectedValueOnce(new Error('Network paused.')).mockResolvedValueOnce([]);
    const user = userEvent.setup();
    renderAt('/blogs', <Home />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Network paused.');
    await user.click(screen.getByRole('button', { name: 'Try again' }));
    expect(await screen.findByRole('status')).toHaveTextContent('Your library is quiet.');
  });

  it('renders detail as plain text with safe author attribution', async () => {
    getPost.mockResolvedValue({ id: 9, title: 'A server detail', content: 'First line.\nSecond line.', excerpt: 'First line.', author: { id: 2, display_name: 'Ada Reader', role: 'user' }, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' });
    renderAt('/blog/9', <ReadBlog />);
    expect(await screen.findByRole('heading', { name: 'A server detail' })).toBeInTheDocument();
    expect(screen.getByText('First line. Second line.', { exact: false })).toHaveClass('post-content');
    expect(screen.getByRole('img', { name: 'Ada Reader avatar' })).toBeInTheDocument();
  });

  it('distinguishes a missing note', async () => {
    const missing = new Error('The requested post was not found.'); missing.status = 404;
    getPost.mockRejectedValueOnce(missing);
    renderAt('/blog/404', <ReadBlog />);
    expect(await screen.findByRole('heading', { name: 'That note is no longer here.' })).toBeInTheDocument();
  });

  it('retries a transient detail failure', async () => {
    getPost.mockRejectedValueOnce(new Error('Network paused.')).mockResolvedValueOnce({ id: 10, title: 'Recovered note', content: 'Recovered text.', excerpt: 'Recovered text.', author: null, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' });
    const user = userEvent.setup();
    renderAt('/blog/10', <ReadBlog />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Network paused.');
    await user.click(screen.getByRole('button', { name: 'Try again' }));
    expect(await screen.findByRole('heading', { name: 'Recovered note' })).toBeInTheDocument();
  });
});
