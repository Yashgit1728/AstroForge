import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import MissionCard from '../MissionCard';
import { Mission } from '../../../types';

const mockMission: Mission = {
  id: '1',
  name: 'Mars Sample Return',
  description: 'A mission to collect samples from Mars and return them to Earth',
  objectives: ['Collect soil samples', 'Study atmosphere', 'Search for life'],
  spacecraft_config: {
    vehicle_type: 'Heavy Lift',
    mass_kg: 5000,
    fuel_capacity_kg: 2000,
    thrust_n: 100000,
    specific_impulse_s: 450,
    payload_mass_kg: 1000,
  },
  trajectory: {
    launch_window: { start: '2025-01-01', end: '2025-02-01' },
    departure_body: 'Earth',
    target_body: 'Mars',
    transfer_type: 'Hohmann',
    maneuvers: [],
    total_delta_v: 8.5,
  },
  timeline: {
    total_duration_days: 365,
    phases: [],
  },
  constraints: {
    max_delta_v: 10,
    max_duration_days: 400,
    max_mass_kg: 6000,
    required_capabilities: [],
  },
  created_at: '2023-01-01T00:00:00Z',
  user_id: 'user1',
};

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('MissionCard', () => {
  it('renders mission information correctly', () => {
    renderWithRouter(<MissionCard mission={mockMission} />);

    expect(screen.getByText('Mars Sample Return')).toBeInTheDocument();
    expect(screen.getByText('A mission to collect samples from Mars and return them to Earth')).toBeInTheDocument();
    expect(screen.getByText('Mars')).toBeInTheDocument();
    expect(screen.getByText('ΔV:')).toBeInTheDocument();
    expect(screen.getByText('8.5 km/s')).toBeInTheDocument();
    expect(screen.getByText('Duration:')).toBeInTheDocument();
    expect(screen.getByText('365d')).toBeInTheDocument();
  });

  it('displays objectives correctly', () => {
    renderWithRouter(<MissionCard mission={mockMission} />);

    expect(screen.getByText('Collect soil samples')).toBeInTheDocument();
    expect(screen.getByText('Study atmosphere')).toBeInTheDocument();
    expect(screen.getByText('+1 more')).toBeInTheDocument();
  });

  it('calls onClone when clone button is clicked', async () => {
    const user = userEvent.setup();
    const mockOnClone = vi.fn();

    renderWithRouter(
      <MissionCard mission={mockMission} onClone={mockOnClone} />
    );

    const cloneButton = screen.getByTitle('Clone mission');
    await user.click(cloneButton);

    expect(mockOnClone).toHaveBeenCalledWith(mockMission);
  });

  it('calls onDelete when delete button is clicked and confirmed', async () => {
    const user = userEvent.setup();
    const mockOnDelete = vi.fn();
    
    // Mock window.confirm
    vi.stubGlobal('confirm', vi.fn(() => true));

    renderWithRouter(
      <MissionCard mission={mockMission} onDelete={mockOnDelete} />
    );

    const deleteButton = screen.getByTitle('Delete mission');
    await user.click(deleteButton);

    expect(mockOnDelete).toHaveBeenCalledWith(mockMission.id);
  });

  it('does not call onDelete when delete is cancelled', async () => {
    const user = userEvent.setup();
    const mockOnDelete = vi.fn();
    
    // Mock window.confirm to return false
    vi.stubGlobal('confirm', vi.fn(() => false));

    renderWithRouter(
      <MissionCard mission={mockMission} onDelete={mockOnDelete} />
    );

    const deleteButton = screen.getByTitle('Delete mission');
    await user.click(deleteButton);

    expect(mockOnDelete).not.toHaveBeenCalled();
  });

  it('hides actions when showActions is false', () => {
    renderWithRouter(
      <MissionCard 
        mission={mockMission} 
        onClone={vi.fn()} 
        onDelete={vi.fn()} 
        showActions={false} 
      />
    );

    expect(screen.queryByTitle('Clone mission')).not.toBeInTheDocument();
    expect(screen.queryByTitle('Delete mission')).not.toBeInTheDocument();
  });
});