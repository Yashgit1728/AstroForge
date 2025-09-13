import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import { TrajectoryChart } from '../TrajectoryChart';
import { TrajectoryPlan } from '../../../../types/mission';

// Mock Recharts components
vi.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: ({ label }: any) => <div data-testid="x-axis">{label?.value}</div>,
  YAxis: ({ label }: any) => <div data-testid="y-axis">{label?.value}</div>,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  ScatterChart: ({ children }: any) => <div data-testid="scatter-chart">{children}</div>,
  Scatter: () => <div data-testid="scatter" />,
}));

const mockTrajectory: TrajectoryPlan = {
  launch_window: {
    start: '2024-01-01T00:00:00Z',
    end: '2024-01-15T00:00:00Z',
  },
  departure_body: 'Earth',
  target_body: 'Mars',
  transfer_type: 'Hohmann Transfer',
  maneuvers: [
    {
      id: '1',
      name: 'Trans-Mars Injection',
      delta_v: 3600,
      timestamp: '2024-01-01T12:00:00Z',
      description: 'Initial burn to leave Earth orbit',
    },
    {
      id: '2',
      name: 'Mid-Course Correction',
      delta_v: 50,
      timestamp: '2024-03-15T06:00:00Z',
      description: 'Trajectory adjustment',
    },
    {
      id: '3',
      name: 'Mars Orbit Insertion',
      delta_v: 1200,
      timestamp: '2024-07-20T18:00:00Z',
      description: 'Burn to enter Mars orbit',
    },
  ],
  total_delta_v: 4850,
};

describe('TrajectoryChart', () => {
  it('renders without crashing', () => {
    render(<TrajectoryChart trajectory={mockTrajectory} />);
    expect(screen.getByText('Orbital Trajectory (2D View)')).toBeInTheDocument();
  });

  it('displays all chart sections', () => {
    render(<TrajectoryChart trajectory={mockTrajectory} />);
    
    expect(screen.getByText('Orbital Trajectory (2D View)')).toBeInTheDocument();
    expect(screen.getByText('Velocity Profile')).toBeInTheDocument();
    expect(screen.getByText('Altitude Profile')).toBeInTheDocument();
    expect(screen.getByText('Delta-V Maneuvers')).toBeInTheDocument();
  });

  it('renders responsive containers for all charts', () => {
    render(<TrajectoryChart trajectory={mockTrajectory} />);
    
    const containers = screen.getAllByTestId('responsive-container');
    expect(containers).toHaveLength(4); // 2D trajectory, velocity, altitude, maneuvers
  });

  it('displays maneuver data when maneuvers are provided', () => {
    render(<TrajectoryChart trajectory={mockTrajectory} />);
    
    expect(screen.getByText('Delta-V Maneuvers')).toBeInTheDocument();
    expect(screen.getAllByTestId('scatter-chart')).toHaveLength(2); // 2D trajectory and maneuvers
  });

  it('handles trajectory with no maneuvers', () => {
    const trajectoryWithoutManeuvers: TrajectoryPlan = {
      ...mockTrajectory,
      maneuvers: [],
    };
    
    render(<TrajectoryChart trajectory={trajectoryWithoutManeuvers} />);
    
    expect(screen.getByText('Orbital Trajectory (2D View)')).toBeInTheDocument();
    expect(screen.getByText('Velocity Profile')).toBeInTheDocument();
    expect(screen.getByText('Altitude Profile')).toBeInTheDocument();
    expect(screen.queryByText('Delta-V Maneuvers')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <TrajectoryChart trajectory={mockTrajectory} className="custom-class" />
    );
    
    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('renders chart axes with correct labels', () => {
    render(<TrajectoryChart trajectory={mockTrajectory} />);
    
    expect(screen.getByText('X Position (km)')).toBeInTheDocument();
    expect(screen.getByText('Y Position (km)')).toBeInTheDocument();
    expect(screen.getAllByText('Time (days)')).toHaveLength(3); // Velocity, altitude, and maneuvers charts
    expect(screen.getByText('Velocity (km/s)')).toBeInTheDocument();
    expect(screen.getByText('Altitude (km)')).toBeInTheDocument();
  });

  it('generates trajectory points correctly', () => {
    render(<TrajectoryChart trajectory={mockTrajectory} />);
    
    // Verify that charts are rendered (indicating data generation worked)
    expect(screen.getAllByTestId('line-chart')).toHaveLength(2); // Velocity and altitude
    expect(screen.getAllByTestId('scatter-chart')).toHaveLength(2); // 2D trajectory and maneuvers
  });

  it('handles different transfer types', () => {
    const biEllipticTrajectory: TrajectoryPlan = {
      ...mockTrajectory,
      transfer_type: 'Bi-elliptic Transfer',
    };
    
    render(<TrajectoryChart trajectory={biEllipticTrajectory} />);
    
    expect(screen.getByText('Orbital Trajectory (2D View)')).toBeInTheDocument();
  });

  it('displays correct chart components', () => {
    render(<TrajectoryChart trajectory={mockTrajectory} />);
    
    // Check for presence of chart elements
    expect(screen.getAllByTestId('cartesian-grid')).toHaveLength(4);
    expect(screen.getAllByTestId('tooltip')).toHaveLength(4);
    expect(screen.getAllByTestId('legend')).toHaveLength(2); // Only velocity and altitude charts have legends
  });
});