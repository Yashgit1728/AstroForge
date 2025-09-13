import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import MissionDetailPage from '../MissionDetailPage';
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
    useParams: () => ({ id: 'test-mission-id' }),
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
    maneuvers: [
      {
        id: 'maneuver-1',
        name: 'Trans-Mars Injection',
        delta_v: 3.6,
        timestamp: '2025-07-15T10:00:00Z',
        description: 'Burn to leave Earth orbit',
      },
    ],
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

describe('MissionDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mock implementations
    vi.mocked(useMissionsHook.useMission).mockReturnValue({
      data: mockMission,
      isLoading: false,
      error: null,
      isError: false,
      isSuccess: true,
    } as any);

    vi.mocked(useMissionsHook.useUpdateMission).mockReturnValue({
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

  it('renders mission details correctly', () => {
    render(<MissionDetailPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Mars Sample Return Mission')).toBeInTheDocument();
    expect(screen.getByText('A mission to collect samples from Mars and return them to Earth')).toBeInTheDocument();
    expect(screen.getByText('Back to Gallery')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    vi.mocked(useMissionsHook.useMission).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      isError: false,
      isSuccess: false,
    } as any);

    render(<MissionDetailPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Loading mission details...')).toBeInTheDocument();
  });

  it('shows error state when mission not found', () => {
    vi.mocked(useMissionsHook.useMission).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Mission not found'),
      isError: true,
      isSuccess: false,
    } as any);

    render(<MissionDetailPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Mission Not Found')).toBeInTheDocument();
    expect(screen.getByText("The mission you're looking for doesn't exist or has been deleted.")).toBeInTheDocument();
  });

  it('displays mission specifications in default tab', () => {
    render(<MissionDetailPage />, { wrapper: createWrapper() });

    // Check if specifications tab is active by default
    expect(screen.getByText('🎯 Mission Objectives')).toBeInTheDocument();
    expect(screen.getByText('🚀 Spacecraft Configuration')).toBeInTheDocument();
    expect(screen.getByText('🛰️ Trajectory Plan')).toBeInTheDocument();
    
    // Check mission objectives
    expect(screen.getByText('Collect soil samples')).toBeInTheDocument();
    expect(screen.getByText('Analyze atmosphere')).toBeInTheDocument();
    expect(screen.getByText('Search for life')).toBeInTheDocument();
    
    // Check spacecraft config
    expect(screen.getByText('Heavy Lift Vehicle')).toBeInTheDocument();
    expect(screen.getByText('15,000 kg')).toBeInTheDocument();
    
    // Check trajectory
    expect(screen.getByText('Earth')).toBeInTheDocument();
    expect(screen.getByText('Mars')).toBeInTheDocument();
    expect(screen.getAllByText('12.50 km/s')).toHaveLength(2); // One in trajectory, one in performance metrics
  });

  it('switches between tabs correctly', async () => {
    const user = userEvent.setup();
    render(<MissionDetailPage />, { wrapper: createWrapper() });

    // Click on Charts tab
    const chartsTab = screen.getByRole('button', { name: /Charts & Analytics/i });
    await user.click(chartsTab);

    expect(screen.getByText('Mission Analytics')).toBeInTheDocument();
    expect(screen.getByText('Trajectory Chart')).toBeInTheDocument();

    // Click on 3D tab
    const threeDTab = screen.getByRole('button', { name: /3D Visualization/i });
    await user.click(threeDTab);

    expect(screen.getByText('3D Mission Visualization')).toBeInTheDocument();
    expect(screen.getByText('3D Scene Viewer')).toBeInTheDocument();

    // Click back to Specifications tab
    const specsTab = screen.getByRole('button', { name: /Specifications/i });
    await user.click(specsTab);

    expect(screen.getByText('🎯 Mission Objectives')).toBeInTheDocument();
  });

  it('enters edit mode when edit button is clicked', async () => {
    const user = userEvent.setup();
    render(<MissionDetailPage />, { wrapper: createWrapper() });

    const editButton = screen.getByRole('button', { name: /Edit/i });
    await user.click(editButton);

    // Should show save and cancel buttons
    expect(screen.getByRole('button', { name: /Save Changes/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();

    // Mission name should be editable
    const nameInput = screen.getByDisplayValue('Mars Sample Return Mission');
    expect(nameInput).toBeInTheDocument();
    expect(nameInput.tagName).toBe('INPUT');
  });

  it('allows editing mission fields', async () => {
    const user = userEvent.setup();
    render(<MissionDetailPage />, { wrapper: createWrapper() });

    // Enter edit mode
    const editButton = screen.getByRole('button', { name: /Edit/i });
    await user.click(editButton);

    // Edit mission name
    const nameInput = screen.getByDisplayValue('Mars Sample Return Mission');
    await user.clear(nameInput);
    await user.type(nameInput, 'Updated Mars Mission');

    // Edit description
    const descriptionTextarea = screen.getByDisplayValue('A mission to collect samples from Mars and return them to Earth');
    await user.clear(descriptionTextarea);
    await user.type(descriptionTextarea, 'Updated mission description');

    // Edit spacecraft mass
    const massInput = screen.getByDisplayValue('15000');
    await user.clear(massInput);
    await user.type(massInput, '16000');

    expect(screen.getByDisplayValue('Updated Mars Mission')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Updated mission description')).toBeInTheDocument();
    expect(screen.getByDisplayValue('16000')).toBeInTheDocument();
  });

  it('saves mission changes', async () => {
    const user = userEvent.setup();
    const mockUpdateMission = vi.fn().mockResolvedValue(mockMission);
    
    vi.mocked(useMissionsHook.useUpdateMission).mockReturnValue({
      mutateAsync: mockUpdateMission,
      isPending: false,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);

    render(<MissionDetailPage />, { wrapper: createWrapper() });

    // Enter edit mode
    const editButton = screen.getByRole('button', { name: /Edit/i });
    await user.click(editButton);

    // Edit mission name
    const nameInput = screen.getByDisplayValue('Mars Sample Return Mission');
    await user.clear(nameInput);
    await user.type(nameInput, 'Updated Mars Mission');

    // Save changes
    const saveButton = screen.getByRole('button', { name: /Save Changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockUpdateMission).toHaveBeenCalledWith({
        id: 'test-mission-id',
        data: expect.objectContaining({
          name: 'Updated Mars Mission',
        }),
      });
    });
  });

  it('cancels editing without saving', async () => {
    const user = userEvent.setup();
    render(<MissionDetailPage />, { wrapper: createWrapper() });

    // Enter edit mode
    const editButton = screen.getByRole('button', { name: /Edit/i });
    await user.click(editButton);

    // Edit mission name
    const nameInput = screen.getByDisplayValue('Mars Sample Return Mission');
    await user.clear(nameInput);
    await user.type(nameInput, 'Updated Mars Mission');

    // Cancel changes
    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    await user.click(cancelButton);

    // Should show original name and edit button again
    expect(screen.getByText('Mars Sample Return Mission')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Edit/i })).toBeInTheDocument();
    expect(screen.queryByDisplayValue('Updated Mars Mission')).not.toBeInTheDocument();
  });

  it('deletes mission with confirmation', async () => {
    const user = userEvent.setup();
    const mockDeleteMission = vi.fn().mockResolvedValue(undefined);
    
    vi.mocked(useMissionsHook.useDeleteMission).mockReturnValue({
      mutateAsync: mockDeleteMission,
      isPending: false,
      error: null,
      data: undefined,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    } as any);

    // Mock window.confirm
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<MissionDetailPage />, { wrapper: createWrapper() });

    const deleteButton = screen.getByRole('button', { name: /Delete/i });
    await user.click(deleteButton);

    expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete this mission? This action cannot be undone.');
    
    await waitFor(() => {
      expect(mockDeleteMission).toHaveBeenCalledWith('test-mission-id');
      expect(mockNavigate).toHaveBeenCalledWith('/gallery');
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

    render(<MissionDetailPage />, { wrapper: createWrapper() });

    const deleteButton = screen.getByRole('button', { name: /Delete/i });
    await user.click(deleteButton);

    expect(confirmSpy).toHaveBeenCalled();
    expect(mockDeleteMission).not.toHaveBeenCalled();
    expect(mockNavigate).not.toHaveBeenCalled();

    confirmSpy.mockRestore();
  });

  it('navigates back to gallery when back button is clicked', async () => {
    const user = userEvent.setup();
    render(<MissionDetailPage />, { wrapper: createWrapper() });

    const backButton = screen.getByRole('button', { name: /Back to Gallery/i });
    await user.click(backButton);

    expect(mockNavigate).toHaveBeenCalledWith('/gallery');
  });

  it('displays performance metrics correctly', () => {
    render(<MissionDetailPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    expect(screen.getAllByText('12.50 km/s')).toHaveLength(2); // Total ΔV appears in both trajectory and performance metrics
    expect(screen.getAllByText('650 days')).toHaveLength(2); // Duration appears in both timeline and performance metrics
    expect(screen.getByText('15.0 tons')).toBeInTheDocument(); // Spacecraft Mass
    expect(screen.getByText('8.0 tons')).toBeInTheDocument(); // Fuel Capacity
  });

  it('displays mission actions', () => {
    render(<MissionDetailPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Mission Actions')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Run Simulation/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Optimize Mission/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Clone Mission/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Export Data/i })).toBeInTheDocument();
  });

  it('displays trajectory maneuvers when available', () => {
    render(<MissionDetailPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Planned Maneuvers')).toBeInTheDocument();
    expect(screen.getByText('Trans-Mars Injection')).toBeInTheDocument();
    expect(screen.getByText('Burn to leave Earth orbit')).toBeInTheDocument();
    expect(screen.getByText('3.60 km/s')).toBeInTheDocument();
  });

  it('displays mission timeline phases', () => {
    render(<MissionDetailPage />, { wrapper: createWrapper() });

    expect(screen.getByText('⏱️ Mission Timeline')).toBeInTheDocument();
    expect(screen.getByText('Launch')).toBeInTheDocument();
    expect(screen.getByText('Transit')).toBeInTheDocument();
    expect(screen.getByText('Operations')).toBeInTheDocument();
    expect(screen.getByText('Launch from Earth')).toBeInTheDocument();
  });
});