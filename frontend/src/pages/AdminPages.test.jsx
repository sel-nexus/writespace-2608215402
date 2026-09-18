import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createUser, deactivateUser, deleteUser, getAdminStats, listUsers } from '../api/users';
import { ProtectedRoute } from '../components/ProtectedRoute';
import AdminDashboard from './AdminDashboard';
import UserManagement from './UserManagement';

vi.mock('../api/users', () => ({ createUser: vi.fn(), deactivateUser: vi.fn(), deleteUser: vi.fn(), getAdminStats: vi.fn(), listUsers: vi.fn() }));

function renderAdmin(path, profile, element) {
  return render(<MemoryRouter initialEntries={[path]}><Routes><Route path="/blogs" element={<h1>Library</h1>} /><Route path="/admin" element={<ProtectedRoute profile={profile}>{element}</ProtectedRoute>} /><Route path="/users" element={<ProtectedRoute profile={profile}>{element}</ProtectedRoute>} /></Routes></MemoryRouter>);
}

describe('administration pages', () => {
  beforeEach(() => vi.clearAllMocks());

  it('guards a non-administrator from administration routes', () => {
    renderAdmin('/admin', { id: 2, role: 'user' }, <AdminDashboard />);
    expect(screen.getByRole('heading', { name: 'Library' })).toBeInTheDocument();
  });

  it('renders loaded server statistics and recent post data', async () => {
    getAdminStats.mockResolvedValue({ user_count: 3, active_user_count: 2, post_count: 1, recent_posts: [{ id: 8, title: 'Server note', author: { display_name: 'Writer' } }] });
    renderAdmin('/admin', { id: 1, role: 'admin' }, <AdminDashboard />);
    expect(await screen.findByLabelText('Total accounts: 3')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Server note' })).toBeInTheDocument();
  });

  it('shows a safe forbidden error from the dashboard API', async () => {
    getAdminStats.mockRejectedValue(new Error('Administrator access is required.'));
    renderAdmin('/admin', { id: 1, role: 'admin' }, <AdminDashboard />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Administrator access is required.');
  });

  it('creates a user then deactivates it through the users helper', async () => {
    const user = userEvent.setup();
    const account = { id: 7, display_name: 'Managed User', username: 'managed', role: 'user', created_at: '2026-01-01T00:00:00Z' };
    listUsers.mockResolvedValue([account]); createUser.mockResolvedValue({ id: 8, display_name: 'New User', username: 'newuser', role: 'user', created_at: '2026-01-02T00:00:00Z' }); deactivateUser.mockResolvedValue(account);
    renderAdmin('/users', { id: 1, role: 'admin' }, <UserManagement />);
    await screen.findByText('Managed User');
    await user.type(screen.getByLabelText('Display name'), 'New User'); await user.type(screen.getByLabelText('Username'), 'newuser'); await user.type(screen.getByLabelText('Password'), 'password8'); await user.click(screen.getByRole('button', { name: 'Create account' }));
    expect(await screen.findByRole('status')).toHaveTextContent('New User was created.');
    await user.click(screen.getByRole('button', { name: 'Deactivate managed' }));
    expect(deactivateUser).toHaveBeenCalledWith(7);
  });

  it('confirms deletion and surfaces a users helper error', async () => {
    const user = userEvent.setup();
    const account = { id: 7, display_name: 'Managed User', username: 'managed', role: 'user', created_at: '2026-01-01T00:00:00Z' };
    listUsers.mockResolvedValue([account]); deleteUser.mockRejectedValue(new Error('This account cannot be managed.'));
    renderAdmin('/users', { id: 1, role: 'admin' }, <UserManagement />);
    await screen.findByText('Managed User'); await user.click(screen.getByRole('button', { name: 'Delete managed' }));
    expect(screen.getByRole('dialog')).toHaveTextContent('Delete Managed User?'); await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Delete account' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('This account cannot be managed.');
  });
});
