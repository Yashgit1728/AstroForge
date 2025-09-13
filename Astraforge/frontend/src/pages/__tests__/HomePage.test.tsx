import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import HomePage from '../HomePage';
import * as useMissionsHook from '../../hooks/useMissions';

// Mock the hooks
vi.mock('../../hooks/useMissions');

// Mock navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const mockMission = {
  id: 'test-mission-id',
  name: 'Mars Sample Return Mission',
  description: 'A mission to collect samples from Mars and return them to Earth',
  objectives: ['Collect soil samples', 'Analyze atmosphere', 'Search for life'],
  spacecraft_config: {
    vehicle_type: 'Heavy Lift Vehicle',
    mass_kg: 15000,
    fuel_capacity_kg: 8000,
    thrust_n: 500000,
    specific_impulse_s: 450,
    payload_mass_kg: 2000,
  },
  trajectory: {
    launch_window: { start: '2025-07-01', end: '2025-08-15' },
    departure_body: 'Earth',
    target_body: 'Mars',
    transfer_type: 'Hohmann Transfer',
    maneuvers: [],
    total_delta_v: 12.5,
  },
  timeline: {
    total_duration_days: 650,
    phases: [
      { name: 'Launch', start_day: 0, duration_days: 1, description: 'Launch from Earth' },
      { name: 'Transit', start_day: 1, duration_days: 260, description: 'Travel to Mars' },
      { name: 'Operations', start_day: 261, duration_days: 389, description: 'Mars operations' },
    ],
  },
  constraints: {
    max_delta_v: 15,
    max_duration_days: 1000,
    max_mass_kg: 20000,
    required_capabilities: ['Deep Space Communication'],
  },
  created_at: '2024-01-01T00:00:00Z',
};

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mock implementations
    vi.mocked(useMissionsHook.useGenerateMission).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);

    vi.mocked(useMissionsHook.useCreateMission).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);
  });

  it('renders the home page with mission prompt form', () => {
    render(<HomePage />, { wrapper: createWrapper() });

    expect(screen.getByText('AstraForge')).toBeInTheDocument();
    expect(screen.getByText('Describe Your Mission')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Describe your space mission idea/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Generate Mission/i })).toBeInTheDocument();
  });

  it('shows validation error for empty prompt', async () => {
    const user = userEvent.setup();
    render(<HomePage />, { wrapper: createWrapper() });

    const textarea = screen.getByPlaceholderText(/Describe your space mission idea/);
    const submitButton = screen.getByRole('button', { name: /Generate Mission/i });

    // Try to submit empty form
    await user.click(textarea);
    await user.tab(); // Move focus away to trigger validation
    
    expect(submitButton).toBeDisabled();
  });

  it('generates mission successfully', async () => {
    const user = userEvent.setup();
    const mockGenerateMission = vi.fn().mockResolvedValue(mockMission);
    
    vi.mocked(useMissionsHook.useGenerateMission).mockReturnValue({
      mutateAsync: mockGenerateMission,
      isPending: false,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);

    render(<HomePage />, { wrapper: createWrapper() });

    const textarea = screen.getByPlaceholderText(/Describe your space mission idea/);
    const submitButton = screen.getByRole('button', { name: /Generate Mission/i });

    // Fill in the form
    await user.type(textarea, 'Send a probe to Mars to study the atmosphere');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockGenerateMission).toHaveBeenCalledWith('Send a probe to Mars to study the atmosphere');
    });

    // Check if mission is displayed
    await waitFor(() => {
      expect(screen.getByText(/Mars Sample Return Mission/)).toBeInTheDocument();
      expect(screen.getByText('Heavy Lift Vehicle')).toBeInTheDocument();
      expect(screen.getByText('Mars')).toBeInTheDocument();
    });
  });

  it('shows loading state during mission generation', async () => {
    const user = userEvent.setup();
    
    vi.mocked(useMissionsHook.useGenerateMission).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: true,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);

    render(<HomePage />, { wrapper: createWrapper() });

    const textarea = screen.getByPlaceholderText(/Describe your space mission idea/);
    
    await user.type(textarea, 'Send a probe to Mars');
    
    // Button should show loading state
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('handles mission generation error', async () => {
    const user = userEvent.setup();
    const mockGenerateMission = vi.fn().mockRejectedValue(new Error('AI service unavailable'));
    
    vi.mocked(useMissionsHook.useGenerateMission).mockReturnValue({
      mutateAsync: mockGenerateMission,
      isPending: false,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);

    render(<HomePage />, { wrapper: createWrapper() });

    const textarea = screen.getByPlaceholderText(/Describe your space mission idea/);
    const submitButton = screen.getByRole('button', { name: /Generate Mission/i });

    await user.type(textarea, 'Send a probe to Mars');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Generation Failed')).toBeInTheDocument();
      expect(screen.getByText('AI service unavailable')).toBeInTheDocument();
    });
  });

  it('saves mission and navigates to detail page', async () => {
    const user = userEvent.setup();
    const mockCreateMission = vi.fn().mockResolvedValue(mockMission);
    
    // First mock successful generation
    vi.mocked(useMissionsHook.useGenerateMission).mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue(mockMission),
      isPending: false,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);

    vi.mocked(useMissionsHook.useCreateMission).mockReturnValue({
      mutateAsync: mockCreateMission,
      isPending: false,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);

    render(<HomePage />, { wrapper: createWrapper() });

    // Generate mission first
    const textarea = screen.getByPlaceholderText(/Describe your space mission idea/);
    await user.type(textarea, 'Send a probe to Mars');
    await user.click(screen.getByRole('button', { name: /Generate Mission/i }));

    // Wait for mission to be generated and save button to appear
    await waitFor(() => {
      expect(screen.getByText(/Mars Sample Return Mission/)).toBeInTheDocument();
    });

    const saveButton = screen.getByRole('button', { name: /Save & View Details/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockCreateMission).toHaveBeenCalledWith(mockMission);
      expect(mockNavigate).toHaveBeenCalledWith('/mission/test-mission-id');
    });
  });

  it('allows generating a new mission after one is created', async () => {
    const user = userEvent.setup();
    const mockGenerateMission = vi.fn().mockResolvedValue(mockMission);
    
    vi.mocked(useMissionsHook.useGenerateMission).mockReturnValue({
      mutateAsync: mockGenerateMission,
      isPending: false,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);

    render(<HomePage />, { wrapper: createWrapper() });

    // Generate first mission
    const textarea = screen.getByPlaceholderText(/Describe your space mission idea/);
    await user.type(textarea, 'Send a probe to Mars');
    await user.click(screen.getByRole('button', { name: /Generate Mission/i }));

    await waitFor(() => {
      expect(screen.getByText(/Mars Sample Return Mission/)).toBeInTheDocument();
    });

    // Click "Generate New" button
    const generateNewButton = screen.getByRole('button', { name: /Generate New/i });
    await user.click(generateNewButton);

    // Should show the form again
    expect(screen.getByPlaceholderText(/Describe your space mission idea/)).toBeInTheDocument();
    expect(screen.queryByText(/Mars Sample Return Mission/)).not.toBeInTheDocument();
  });

  it('navigates to gallery when browse gallery button is clicked', async () => {
    const user = userEvent.setup();
    
    // Mock successful generation first
    vi.mocked(useMissionsHook.useGenerateMission).mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue(mockMission),
      isPending: false,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);

    render(<HomePage />, { wrapper: createWrapper() });

    // Generate mission first
    const textarea = screen.getByPlaceholderText(/Describe your space mission idea/);
    await user.type(textarea, 'Send a probe to Mars');
    await user.click(screen.getByRole('button', { name: /Generate Mission/i }));

    await waitFor(() => {
      expect(screen.getByText(/Mars Sample Return Mission/)).toBeInTheDocument();
    });

    const browseButton = screen.getByRole('button', { name: /Browse Gallery/i });
    await user.click(browseButton);

    expect(mockNavigate).toHaveBeenCalledWith('/gallery');
  });
});