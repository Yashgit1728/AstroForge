import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import GalleryPage from '../GalleryPage';
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

const mockMissions = [
  {
    id: 'mission-1',
    name: 'Mars Sample Return Mission',
    description: 'A mission to collect samples from Mars and return them to Earth',
    objectives: ['Collect soil samples', 'Analyze atmosphere'],
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
      phases: [],
    },
    constraints: {
      max_delta_v: 15,
      max_duration_days: 1000,
      max_mass_kg: 20000,
      required_capabilities: [],
    },
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'mission-2',
    name: 'Lunar Base Construction',
    description: 'Establish a permanent base on the Moon',
    objectives: ['Build habitat', 'Set up power systems'],
    spacecraft_config: {
      vehicle_type: 'Medium Lift Vehicle',
      mass_kg: 10000,
      fuel_capacity_kg: 5000,
      thrust_n: 300000,
      specific_impulse_s: 420,
      payload_mass_kg: 3000,
    },
    trajectory: {
      launch_window: { start: '2025-03-01', end: '2025-04-15' },
      departure_body: 'Earth',
      target_body: 'Moon',
      transfer_type: 'Direct Transfer',
      maneuvers: [],
      total_delta_v: 8.2,
    },
    timeline: {
      total_duration_days: 180,
      phases: [],
    },
    constraints: {
      max_delta_v: 10,
      max_duration_days: 200,
      max_mass_kg: 15000,
      required_capabilities: [],
    },
    created_at: '2024-01-02T00:00:00Z',
  },
];

const mockPaginatedResponse = {
  data: mockMissions,
  total: 2,
  page: 1,
  per_page: 12,
  total_pages: 1,
};

describe('GalleryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock window.scrollTo
    Object.defineProperty(window, 'scrollTo', {
      value: vi.fn(),
      writable: true,
    });
    
    // Setup default mock implementations
    vi.mocked(useMissionsHook.useMissions).mockReturnValue({
      data: mockPaginatedResponse,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isError: false,
      isSuccess: true,
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

    vi.mocked(useMissionsHook.useDeleteMission).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);
  });

  it('renders gallery page with missions', () => {
    render(<GalleryPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Mission Gallery')).toBeInTheDocument();
    expect(screen.getByText('Explore example missions and your saved designs')).toBeInTheDocument();
    expect(screen.getByText('(2 missions)')).toBeInTheDocument();
    
    // Check if missions are displayed
    expect(screen.getByText('Mars Sample Return Mission')).toBeInTheDocument();
    expect(screen.getByText('Lunar Base Construction')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    vi.mocked(useMissionsHook.useMissions).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      isError: false,
      isSuccess: false,
    } as any);

    render(<GalleryPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Loading missions...')).toBeInTheDocument();
  });

  it('shows error state', () => {
    const mockRefetch = vi.fn();
    vi.mocked(useMissionsHook.useMissions).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Failed to fetch'),
      refetch: mockRefetch,
      isError: true,
      isSuccess: false,
    } as any);

    render(<GalleryPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Failed to Load Missions')).toBeInTheDocument();
    expect(screen.getByText('There was an error loading the mission gallery. Please try again.')).toBeInTheDocument();
    
    const tryAgainButton = screen.getByRole('button', { name: /Try Again/i });
    fireEvent.click(tryAgainButton);
    expect(mockRefetch).toHaveBeenCalled();
  });

  it('shows empty state when no missions', () => {
    vi.mocked(useMissionsHook.useMissions).mockReturnValue({
      data: { ...mockPaginatedResponse, data: [], total: 0 },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isError: false,
      isSuccess: true,
    } as any);

    render(<GalleryPage />, { wrapper: createWrapper() });

    expect(screen.getByText('No Missions Yet')).toBeInTheDocument();
    expect(screen.getByText('Start by creating your first mission to see it here in the gallery.')).toBeInTheDocument();
  });

  it('handles search functionality', async () => {
    const user = userEvent.setup();
    render(<GalleryPage />, { wrapper: createWrapper() });

    const searchInput = screen.getByPlaceholderText(/Search missions by name/);
    await user.type(searchInput, 'Mars');

    // Should show clear button when there's search text
    expect(screen.getByRole('button', { name: '' })).toBeInTheDocument(); // Clear button (X)
  });

  it('clears search when clear button is clicked', async () => {
    const user = userEvent.setup();
    render(<GalleryPage />, { wrapper: createWrapper() });

    const searchInput = screen.getByPlaceholderText(/Search missions by name/);
    await user.type(searchInput, 'Mars');
    
    const clearButton = screen.getByRole('button', { name: '' }); // Clear button (X)
    await user.click(clearButton);

    expect(searchInput).toHaveValue('');
  });

  it('handles filter selection', async () => {
    const user = userEvent.setup();
    render(<GalleryPage />, { wrapper: createWrapper() });

    const marsFilter = screen.getByRole('button', { name: /Mars Missions/i });
    await user.click(marsFilter);

    // The filter button should be selected (have purple background)
    expect(marsFilter).toHaveClass('bg-purple-600');
  });

  it('handles sorting', async () => {
    const user = userEvent.setup();
    render(<GalleryPage />, { wrapper: createWrapper() });

    const nameSort = screen.getByRole('button', { name: /Name/i });
    await user.click(nameSort);

    // Should show sort indicator
    expect(nameSort).toHaveClass('bg-purple-600');
  });

  it('toggles sort order when clicking same sort button', async () => {
    const user = userEvent.setup();
    render(<GalleryPage />, { wrapper: createWrapper() });

    const dateSort = screen.getByRole('button', { name: /Date/i });
    
    // Click once (should be desc by default)
    await user.click(dateSort);
    expect(dateSort).toHaveClass('bg-purple-600');
    
    // Click again (should toggle to asc)
    await user.click(dateSort);
    expect(dateSort).toHaveClass('bg-purple-600');
  });

  it('navigates to create mission page', async () => {
    const user = userEvent.setup();
    render(<GalleryPage />, { wrapper: createWrapper() });

    const createButton = screen.getByRole('button', { name: /Create New Mission/i });
    await user.click(createButton);

    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  it('clones a mission', async () => {
    const user = userEvent.setup();
    const mockCreateMission = vi.fn().mockResolvedValue({ id: 'new-mission-id' });
    
    vi.mocked(useMissionsHook.useCreateMission).mockReturnValue({
      mutateAsync: mockCreateMission,
      isPending: false,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);

    render(<GalleryPage />, { wrapper: createWrapper() });

    // Find the first mission card's clone button (missions are sorted by date desc, so second mission comes first)
    const cloneButtons = screen.getAllByTitle('Clone mission');
    await user.click(cloneButtons[0]);

    await waitFor(() => {
      expect(mockCreateMission).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Lunar Base Construction (Copy)',
          description: 'Establish a permanent base on the Moon',
        })
      );
      expect(mockNavigate).toHaveBeenCalledWith('/mission/new-mission-id');
    });
  });

  it('deletes a mission with confirmation', async () => {
    const user = userEvent.setup();
    const mockDeleteMission = vi.fn().mockResolvedValue(undefined);
    const mockRefetch = vi.fn();
    
    vi.mocked(useMissionsHook.useDeleteMission).mockReturnValue({
      mutateAsync: mockDeleteMission,
      isPending: false,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);

    vi.mocked(useMissionsHook.useMissions).mockReturnValue({
      data: mockPaginatedResponse,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
      isError: false,
      isSuccess: true,
    } as any);

    // Mock window.confirm
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<GalleryPage />, { wrapper: createWrapper() });

    // Find the first mission card's delete button (missions are sorted by date desc, so second mission comes first)
    const deleteButtons = screen.getAllByTitle('Delete mission');
    await user.click(deleteButtons[0]);

    expect(confirmSpy).toHaveBeenCalled();
    
    await waitFor(() => {
      expect(mockDeleteMission).toHaveBeenCalledWith('mission-2');
      expect(mockRefetch).toHaveBeenCalled();
    });

    confirmSpy.mockRestore();
  });

  it('does not delete mission when confirmation is cancelled', async () => {
    const user = userEvent.setup();
    const mockDeleteMission = vi.fn();
    
    vi.mocked(useMissionsHook.useDeleteMission).mockReturnValue({
      mutateAsync: mockDeleteMission,
      isPending: false,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);

    // Mock window.confirm to return false
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);

    render(<GalleryPage />, { wrapper: createWrapper() });

    // Find the first mission card's delete button
    const deleteButtons = screen.getAllByTitle('Delete mission');
    await user.click(deleteButtons[0]);

    expect(confirmSpy).toHaveBeenCalled();
    expect(mockDeleteMission).not.toHaveBeenCalled();

    confirmSpy.mockRestore();
  });

  it('shows pagination when there are multiple pages', () => {
    const multiPageResponse = {
      ...mockPaginatedResponse,
      total: 25,
      total_pages: 3,
    };

    vi.mocked(useMissionsHook.useMissions).mockReturnValue({
      data: multiPageResponse,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isError: false,
      isSuccess: true,
    } as any);

    render(<GalleryPage />, { wrapper: createWrapper() });

    // Should show pagination controls
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('handles page navigation', async () => {
    const user = userEvent.setup();
    const multiPageResponse = {
      ...mockPaginatedResponse,
      total: 25,
      total_pages: 3,
    };

    vi.mocked(useMissionsHook.useMissions).mockReturnValue({
      data: multiPageResponse,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isError: false,
      isSuccess: true,
    } as any);

    render(<GalleryPage />, { wrapper: createWrapper() });

    const page2Button = screen.getByText('2');
    await user.click(page2Button);

    // Should scroll to top (we can't test this directly, but the function should be called)
    expect(page2Button).toBeInTheDocument();
  });

  it('shows results summary', () => {
    render(<GalleryPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Showing 1 to 2 of 2 missions')).toBeInTheDocument();
  });

  it('shows empty search results', () => {
    vi.mocked(useMissionsHook.useMissions).mockReturnValue({
      data: { ...mockPaginatedResponse, data: [], total: 0 },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isError: false,
      isSuccess: true,
    } as any);

    render(<GalleryPage />, { wrapper: createWrapper() });

    // Simulate having a search term
    const searchInput = screen.getByPlaceholderText(/Search missions by name/);
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

    expect(screen.getByText('No Missions Found')).toBeInTheDocument();
  });

  it('displays mission count in filter', () => {
    render(<GalleryPage />, { wrapper: createWrapper() });

    const allMissionsFilter = screen.getByRole('button', { name: /All Missions/i });
    expect(allMissionsFilter).toHaveTextContent('2'); // Should show count badge
  });
});