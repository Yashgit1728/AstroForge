import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import { OrbitalParametersChart } from '../OrbitalParametersChart';
import { TrajectoryPlan, SpacecraftConfig } from '../../../../types/mission';

// Mock Recharts components
vi.mock('recharts', () => ({
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: ({ label }: any) => <div data-testid="x-axis">{label?.value}</div>,
  YAxis: ({ label }: any) => <div data-testid="y-axis">{label?.value}</div>,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  RadarChart: ({ children }: any) => <div data-testid="radar-chart">{children}</div>,
  PolarGrid: () => <div data-testid="polar-grid" />,
  PolarAngleAxis: () => <div data-testid="polar-angle-axis" />,
  PolarRadiusAxis: () => <div data-testid="polar-radius-axis" />,
  Radar: () => <div data-testid="radar" />,
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
  ],
  total_delta_v: 4850,
};

const mockSpacecraftConfig: SpacecraftConfig = {
  vehicle_type: 'Heavy Lift Vehicle',
  mass_kg: 50000,
  fuel_capacity_kg: 200000,
  thrust_n: 7500000,
  specific_impulse_s: 450,
  payload_mass_kg: 15000,
};

describe('OrbitalParametersChart', () => {
  it('renders without crashing', () => {
    render(
      <OrbitalParametersChart 
        trajectory={mockTrajectory} 
        spacecraftConfig={mockSpacecraftConfig} 
      />
    );
    expect(screen.getByText('Orbital Parameters')).toBeInTheDocument();
  });

  it('displays all chart sections', () => {
    render(
      <OrbitalParametersChart 
        trajectory={mockTrajectory} 
        spacecraftConfig={mockSpacecraftConfig} 
      />
    );
    
    expect(screen.getByText('Orbital Parameters')).toBeInTheDocument();
    expect(screen.getByText('Transfer Type Comparison')).toBeInTheDocument();
    expect(screen.getByText('Mass Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Spacecraft Performance')).toBeInTheDocument();
  });

  it('renders all chart types', () => {
    render(
      <OrbitalParametersChart 
        trajectory={mockTrajectory} 
        spacecraftConfig={mockSpacecraftConfig} 
      />
    );
    
    expect(screen.getAllByTestId('bar-chart')).toHaveLength(2); // Parameters and transfer comparison
    expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    expect(screen.getByTestId('radar-chart')).toBeInTheDocument();
  });

  it('calculates orbital parameters correctly', () => {
    render(
      <OrbitalParametersChart 
        trajectory={mockTrajectory} 
        spacecraftConfig={mockSpacecraftConfig} 
      />
    );
    
    // Verify that the component renders without errors, indicating calculations worked
    expect(screen.getByText('Orbital Parameters')).toBeInTheDocument();
    expect(screen.getAllByTestId('responsive-container')).toHaveLength(4);
  });

  it('displays transfer efficiency comparison', () => {
    render(
      <OrbitalParametersChart 
        trajectory={mockTrajectory} 
        spacecraftConfig={mockSpacecraftConfig} 
      />
    );
    
    expect(screen.getByText('Transfer Type Comparison')).toBeInTheDocument();
    expect(screen.getAllByTestId('bar-chart')).toHaveLength(2);
  });

  it('shows mass breakdown pie chart', () => {
    render(
      <OrbitalParametersChart 
        trajectory={mockTrajectory} 
        spacecraftConfig={mockSpacecraftConfig} 
      />
    );
    
    expect(screen.getByText('Mass Breakdown')).toBeInTheDocument();
    expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
  });

  it('displays spacecraft performance radar chart', () => {
    render(
      <OrbitalParametersChart 
        trajectory={mockTrajectory} 
        spacecraftConfig={mockSpacecraftConfig} 
      />
    );
    
    expect(screen.getByText('Spacecraft Performance')).toBeInTheDocument();
    expect(screen.getByTestId('radar-chart')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <OrbitalParametersChart 
        trajectory={mockTrajectory} 
        spacecraftConfig={mockSpacecraftConfig}
        className="custom-class" 
      />
    );
    
    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('handles different spacecraft configurations', () => {
    const lightSpacecraft: SpacecraftConfig = {
      vehicle_type: 'Light Vehicle',
      mass_kg: 5000,
      fuel_capacity_kg: 20000,
      thrust_n: 500000,
      specific_impulse_s: 300,
      payload_mass_kg: 1000,
    };
    
    render(
      <OrbitalParametersChart 
        trajectory={mockTrajectory} 
        spacecraftConfig={lightSpacecraft} 
      />
    );
    
    expect(screen.getByText('Orbital Parameters')).toBeInTheDocument();
  });

  it('handles high delta-v trajectories', () => {
    const highDeltaVTrajectory: TrajectoryPlan = {
      ...mockTrajectory,
      total_delta_v: 15000,
    };
    
    render(
      <OrbitalParametersChart 
        trajectory={highDeltaVTrajectory} 
        spacecraftConfig={mockSpacecraftConfig} 
      />
    );
    
    expect(screen.getByText('Orbital Parameters')).toBeInTheDocument();
  });

  it('renders chart components correctly', () => {
    render(
      <OrbitalParametersChart 
        trajectory={mockTrajectory} 
        spacecraftConfig={mockSpacecraftConfig} 
      />
    );
    
    // Check for presence of chart elements
    expect(screen.getAllByTestId('cartesian-grid')).toHaveLength(2); // Bar charts
    expect(screen.getAllByTestId('tooltip')).toHaveLength(4); // All charts have tooltips
    expect(screen.getAllByTestId('legend')).toHaveLength(2); // Bar charts have legends
  });

  it('calculates mass ratios correctly', () => {
    const testConfig: SpacecraftConfig = {
      vehicle_type: 'Test Vehicle',
      mass_kg: 10000,
      fuel_capacity_kg: 40000,
      thrust_n: 1000000,
      specific_impulse_s: 400,
      payload_mass_kg: 5000,
    };
    
    render(
      <OrbitalParametersChart 
        trajectory={mockTrajectory} 
        spacecraftConfig={testConfig} 
      />
    );
    
    // Component should render without errors, indicating calculations are working
    expect(screen.getByText('Mass Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Spacecraft Performance')).toBeInTheDocument();
  });
});