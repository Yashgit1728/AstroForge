import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginModal from '../LoginModal';
import { AuthProvider } from '../../../hooks/useAuth';

// Mock Supabase
vi.mock('../../../lib/supabase', () => ({
  supabase: {
    auth: {
      signInWithOtp: vi.fn(),
      getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
      onAuthStateChange: vi.fn().mockReturnValue({
        data: { subscription: { unsubscribe: vi.fn() } }
      }),
    },
  },
}));

const MockAuthProvider = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe('LoginModal', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders when open', () => {
    render(
      <MockAuthProvider>
        <LoginModal isOpen={true} onClose={mockOnClose} />
      </MockAuthProvider>
    );

    expect(screen.getByText('Sign In')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your email')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <MockAuthProvider>
        <LoginModal isOpen={false} onClose={mockOnClose} />
      </MockAuthProvider>
    );

    expect(screen.queryByText('Sign In')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <MockAuthProvider>
        <LoginModal isOpen={true} onClose={mockOnClose} />
      </MockAuthProvider>
    );

    const closeButton = screen.getByRole('button', { name: /close/i });
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('validates email input', async () => {
    const user = userEvent.setup();
    
    render(
      <MockAuthProvider>
        <LoginModal isOpen={true} onClose={mockOnClose} />
      </MockAuthProvider>
    );

    const submitButton = screen.getByRole('button', { name: /send magic link/i });
    await user.click(submitButton);

    // Form should not submit without email
    expect(screen.getByText('Sign In')).toBeInTheDocument();
  });

  it('shows success message after email is sent', async () => {
    const user = userEvent.setup();
    
    render(
      <MockAuthProvider>
        <LoginModal isOpen={true} onClose={mockOnClose} />
      </MockAuthProvider>
    );

    const emailInput = screen.getByPlaceholderText('Enter your email');
    const submitButton = screen.getByRole('button', { name: /send magic link/i });

    await user.type(emailInput, 'test@example.com');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Check Your Email')).toBeInTheDocument();
    });
  });
});