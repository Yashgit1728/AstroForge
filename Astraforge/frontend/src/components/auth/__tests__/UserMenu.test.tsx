import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UserMenu from '../UserMenu';
import { AuthProvider } from '../../../hooks/useAuth';

// Mock Supabase
const mockSignOut = vi.fn();
vi.mock('../../../lib/supabase', () => ({
  supabase: {
    auth: {
      signOut: mockSignOut,
      getSession: vi.fn().mockResolvedValue({ 
        data: { 
          session: { 
            user: { 
              id: '1', 
              email: 'test@example.com', 
              created_at: '2023-01-01' 
            } 
          } 
        } 
      }),
      onAuthStateChange: vi.fn().mockReturnValue({
        data: { subscription: { unsubscribe: vi.fn() } }
      }),
    },
  },
}));

const MockAuthProvider = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe('UserMenu', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders user menu when user is authenticated', async () => {
    render(
      <MockAuthProvider>
        <UserMenu />
      </MockAuthProvider>
    );

    // Wait for auth state to load
    await screen.findByText('T'); // First letter of email
  });

  it('opens menu when clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <MockAuthProvider>
        <UserMenu />
      </MockAuthProvider>
    );

    const menuButton = await screen.findByText('T');
    await user.click(menuButton);

    expect(screen.getByText('Signed in as')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });

  it('calls signOut when sign out button is clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <MockAuthProvider>
        <UserMenu />
      </MockAuthProvider>
    );

    const menuButton = await screen.findByText('T');
    await user.click(menuButton);

    const signOutButton = screen.getByText('Sign Out');
    await user.click(signOutButton);

    expect(mockSignOut).toHaveBeenCalled();
  });
});