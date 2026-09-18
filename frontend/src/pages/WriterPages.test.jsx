import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPost, deletePost, getPost, updatePost } from '../api/posts';
import ReadBlog from './ReadBlog';
import WriteBlog from './WriteBlog';

vi.mock('../api/posts', () => ({ createPost: vi.fn(), deletePost: vi.fn(), getPost: vi.fn(), updatePost: vi.fn() }));

function renderRoute(path, element) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/write" element={element} />
        <Route path="/edit/:id" element={element} />
        <Route path="/blog/:id" element={element} />
        <Route path="/blogs" element={<h1>Reading room</h1>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('writer pages', () => {
  beforeEach(() => vi.clearAllMocks());

  it('validates required fields and creates through the central posts API', async () => {
    const user = userEvent.setup();
    createPost.mockResolvedValue({ id: 7 });
    renderRoute('/write', <WriteBlog />);

    await user.click(screen.getByRole('button', { name: 'Publish note' }));
    expect(screen.getByRole('alert')).toHaveTextContent('A title and note are required.');
    await user.type(screen.getByLabelText('Title'), 'A new note');
    await user.type(screen.getByLabelText('Note'), 'A considered paragraph.');
    await user.click(screen.getByRole('button', { name: 'Publish note' }));

    expect(createPost).toHaveBeenCalledWith({ title: 'A new note', content: 'A considered paragraph.' });
  });

  it('loads an existing note and saves its revision', async () => {
    const user = userEvent.setup();
    getPost.mockResolvedValue({ id: 9, title: 'Before', content: 'Before body' });
    updatePost.mockResolvedValue({ id: 9 });
    renderRoute('/edit/9', <WriteBlog />);

    expect(await screen.findByDisplayValue('Before')).toBeInTheDocument();
    await user.clear(screen.getByLabelText('Title'));
    await user.type(screen.getByLabelText('Title'), 'After');
    await user.click(screen.getByRole('button', { name: 'Save changes' }));

    expect(updatePost).toHaveBeenCalledWith('9', { title: 'After', content: 'Before body' });
  });

  it('shows owner controls, confirms deletion, and returns to the library', async () => {
    const user = userEvent.setup();
    getPost.mockResolvedValue({ id: 11, title: 'Owned note', content: 'Body', author: { id: 4, display_name: 'Owner', role: 'user' }, created_at: '2026-01-01T00:00:00Z' });
    deletePost.mockResolvedValue({});
    renderRoute('/blog/11', <ReadBlog profile={{ id: 4, role: 'user' }} />);

    expect(await screen.findByRole('button', { name: 'Delete note' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Delete note' }));
    expect(screen.getByRole('dialog')).toHaveTextContent('Delete this note?');
    await user.click(screen.getAllByRole('button', { name: 'Delete note' }).at(-1));

    expect(deletePost).toHaveBeenCalledWith('11');
  });

  it('does not expose mutation controls to a nonowner', async () => {
    getPost.mockResolvedValue({ id: 12, title: 'Someone else', content: 'Body', author: { id: 5, display_name: 'Other', role: 'user' }, created_at: '2026-01-01T00:00:00Z' });
    renderRoute('/blog/12', <ReadBlog profile={{ id: 4, role: 'user' }} />);

    await screen.findByRole('heading', { name: 'Someone else' });
    expect(screen.queryByRole('button', { name: 'Delete note' })).not.toBeInTheDocument();
  });
});
