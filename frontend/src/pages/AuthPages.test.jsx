import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { loginAccount, registerAccount } from '../api/auth';

vi.mock('../api/auth', () => ({
  getCurrentUser: vi.fn(),
  loginAccount: vi.fn(),
  registerAccount: vi.fn(),
}));

const session = {
  access_token: 'server-issued-token',
  token_type: 'bearer',
  user: { id: 4, display_name: 'Reader', username: 'reader', role: 'user', created_at: '2026-01-01T00:00:00Z' },
};

beforeEach(() => {
  window.history.pushState({}, '', '/login');
  window.localStorage.clear();
  vi.clearAllMocks();
});

describe('authentication pages', () => {
  it('submits login credentials and persists only the issued session', async () => {
    loginAccount.mockResolvedValue(session);
    render(<App />);
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'reader' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'reader-pass-123' } });
    fireEvent.click(screen.getByRole('button', { name: 'Log in' }));
    await waitFor(() => expect(loginAccount).toHaveBeenCalledWith({ username: 'reader', password: 'reader-pass-123' }));
    expect(window.localStorage.getItem('ws.access_token')).toBe('server-issued-token');
    expect(JSON.parse(window.localStorage.getItem('ws.profile'))).toMatchObject({ username: 'reader' });
  });

  it('shows a login error inline without redirecting', async () => {
    loginAccount.mockRejectedValue(new Error('Invalid username or password.'));
    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: 'Log in' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid username or password.');
    expect(window.location.pathname).toBe('/login');
  });

  it('submits registration values and shows request failures inline', async () => {
    window.history.pushState({}, '', '/register');
    registerAccount.mockRejectedValue(new Error('That username is already in use.'));
    render(<App />);
    fireEvent.change(screen.getByLabelText('Display name'), { target: { value: 'Reader' } });
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'reader' } });
    fireEvent.change(screen.getByLabelText('Password', { exact: true }), { target: { value: 'reader-pass-123' } });
    fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'reader-pass-123' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }));
    await waitFor(() => expect(registerAccount).toHaveBeenCalled());
    expect(await screen.findByRole('alert')).toHaveTextContent('That username is already in use.');
  });

  it('clears an invalid persisted session and leaves the guest on the login route', async () => {
    window.localStorage.setItem('ws.access_token', 'stale-token');
    window.localStorage.setItem('ws.profile', '{bad json');
    render(<App />);
    await waitFor(() => expect(window.localStorage.getItem('ws.access_token')).toBeNull());
    expect(screen.getByRole('heading', { name: 'Log in' })).toBeInTheDocument();
  });
});
