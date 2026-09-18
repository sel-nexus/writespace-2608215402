import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import LandingPage from './LandingPage';
import { getPublicPreviews } from '../api/posts';

vi.mock('../api/posts', () => ({ getPublicPreviews: vi.fn() }));

function renderPage() {
  return render(
    <BrowserRouter>
      <LandingPage />
    </BrowserRouter>,
  );
}

describe('LandingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders backend-sourced public preview data', async () => {
    getPublicPreviews.mockResolvedValue([
      { id: 1, title: 'A long walk home', excerpt: 'A note about returning slowly.', created_at: '2025-01-05T00:00:00Z' },
    ]);

    renderPage();

    expect(await screen.findByRole('heading', { name: 'A long walk home' })).toBeInTheDocument();
    expect(screen.getByText('A note about returning slowly.')).toBeInTheDocument();
  });

  it('shows an explicit retry action after the preview request fails', async () => {
    getPublicPreviews.mockRejectedValueOnce(new Error('Network paused.')).mockResolvedValueOnce([]);
    const user = userEvent.setup();

    renderPage();

    expect(await screen.findByRole('alert')).toHaveTextContent('Network paused.');
    await user.click(screen.getByRole('button', { name: 'Try again' }));
    expect(await screen.findByRole('status')).toHaveTextContent('No public notes have been filed yet.');
    expect(getPublicPreviews).toHaveBeenCalledTimes(2);
  });
});
