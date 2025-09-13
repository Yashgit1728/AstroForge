import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import { TimelineChart } from '../TimelineChart';
import { MissionTimeline, Maneuver } from '../../../../types/mission';

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
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  AreaChart: ({ children }: any) => <div data-testid="area-chart">{children}</div>,
  Area: () => <div data-testid="area" />,
}));

const mockTimeline: MissionTimeline = {
  total_duration_days: 365,
  phases: [
    {
      name: 'Launch Preparation',
      start_day: 0,
      duration_days: 30,
      description: 'Pre-launch activities and final checks',
    },
    {
      name: 'Earth Departure',
      start_day: 30,
      duration_days: 5,
      description: 'Launch and initial trajectory correction',
    },
    {
      name: 'Cruise Phase',
      start_day: 35,
      duration_days: 280,
      description: 'Interplanetary transit',
    },
    {
      name: 'Mars Arrival',
      start_day: 315,
      duration_days: 50,
      description: 'Orbital insertion and mission operations',
    },
  ],
};

const mockManeuvers: Maneuver[] = [
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
];

describe('TimelineChart', () => {
  it('renders without crashing', () => {
    render(<TimelineChart timeline={mockTimeline} />);
    expect(screen.getByText('Mission Progress Timeline')).toBeInTheDocument();
  });

  it('displays all chart sections', () => {
    render(<TimelineChart timeline={mockTimeline} maneuvers={mockManeuvers} />);

    expect(screen.getByText('Mission Progress Timeline')).toBeInTheDocument();
    expect(screen.getByText('Mission Phases')).toBeInTheDocument();
    expect(screen.getByText('Mission Events')).toBeInTheDocument();
    expect(screen.getByText('Phase Summary')).toBeInTheDocument();
  });

  it('renders all chart types', () => {
    render(<TimelineChart timeline={mockTimeline} maneuvers={mockManeuvers} />);

    expect(screen.getByTestId('area-chart')).toBeInTheDocument(); // Progress timeline
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument(); // Phase durations
    expect(screen.getByTestId('line-chart')).toBeInTheDocument(); // Events
  });

  it('displays phase summary table', () => {
    render(<TimelineChart timeline={mockTimeline} />);

    expect(screen.getByText('Phase Summary')).toBeInTheDocument();
    expect(screen.getByText('Launch Preparation')).toBeInTheDocument();
    expect(screen.getByText('Earth Departure')).toBeInTheDocument();
    expect(screen.getByText('Cruise Phase')).toBeInTheDocument();
    expect(screen.getByText('Mars Arrival')).toBeInTheDocument();
  });

  it('shows phase details in table', () => {
    render(<TimelineChart timeline={mockTimeline} />);

    // Check for table headers
    expect(screen.getByText('Phase')).toBeInTheDocument();
    expect(screen.getByText('Start Day')).toBeInTheDocument();
    expect(screen.getByText('Duration')).toBeInTheDocument();
    expect(screen.getByText('End Day')).toBeInTheDocument();
    expect(screen.getByText('Description')).toBeInTheDocument();

    // Check for phase data
    expect(screen.getByText('30 days')).toBeInTheDocument();
    expect(screen.getByText('5 days')).toBeInTheDocument();
    expect(screen.getByText('280 days')).toBeInTheDocument();
    expect(screen.getByText('50 days')).toBeInTheDocument();
  });

  it('handles timeline without maneuvers', () => {
    render(<TimelineChart timeline={mockTimeline} />);

    expect(screen.getByText('Mission Progress Timeline')).toBeInTheDocument();
    expect(screen.getByText('Mission Phases')).toBeInTheDocument();
    expect(screen.getByText('Mission Events')).toBeInTheDocument();
  });

  it('handles timeline with maneuvers', () => {
    render(<TimelineChart timeline={mockTimeline} maneuvers={mockManeuvers} />);

    expect(screen.getByText('Mission Events')).toBeInTheDocument();
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <TimelineChart timeline={mockTimeline} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('renders responsive containers for all charts', () => {
    render(<TimelineChart timeline={mockTimeline} maneuvers={mockManeuvers} />);

    const containers = screen.getAllByTestId('responsive-container');
    expect(containers).toHaveLength(3); // Progress, phases, events
  });

  it('displays correct chart axes labels', () => {
    render(<TimelineChart timeline={mockTimeline} maneuvers={mockManeuvers} />);

    expect(screen.getAllByText('Mission Day')).toHaveLength(2); // Progress and events charts
    expect(screen.getByText('Progress (%)')).toBeInTheDocument();
    expect(screen.getByText('Days')).toBeInTheDocument();
    expect(screen.getByText('Delta-V (m/s)')).toBeInTheDocument();
  });

  it('handles empty phases array', () => {
    const emptyTimeline: MissionTimeline = {
      total_duration_days: 100,
      phases: [],
    };

    render(<TimelineChart timeline={emptyTimeline} />);

    expect(screen.getByText('Mission Progress Timeline')).toBeInTheDocument();
    expect(screen.getByText('Phase Summary')).toBeInTheDocument();
  });

  it('handles short duration missions', () => {
    const shortTimeline: MissionTimeline = {
      total_duration_days: 30,
      phases: [
        {
          name: 'Quick Mission',
          start_day: 0,
          duration_days: 30,
          description: 'Short duration test',
        },
      ],
    };

    render(<TimelineChart timeline={shortTimeline} />);

    expect(screen.getByText('Quick Mission')).toBeInTheDocument();
  });

  it('handles long duration missions', () => {
    const longTimeline: MissionTimeline = {
      total_duration_days: 2000,
      phases: [
        {
          name: 'Extended Mission',
          start_day: 0,
          duration_days: 2000,
          description: 'Long duration mission',
        },
      ],
    };

    render(<TimelineChart timeline={longTimeline} />);

    expect(screen.getByText('Extended Mission')).toBeInTheDocument();
  });

  it('renders chart components correctly', () => {
    render(<TimelineChart timeline={mockTimeline} maneuvers={mockManeuvers} />);

    // Check for presence of chart elements
    expect(screen.getAllByTestId('cartesian-grid')).toHaveLength(3);
    expect(screen.getAllByTestId('tooltip')).toHaveLength(3);
    expect(screen.getAllByTestId('legend')).toHaveLength(1); // Only bar chart has legend
  });
});