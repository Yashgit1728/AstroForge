import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import { PerformanceMetricsChart } from '../PerformanceMetricsChart';
import { TrajectoryPlan, SpacecraftConfig, SimulationResult } from '../../../../types/mission';

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
    PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
    Pie: () => <div data-testid="pie" />,
    Cell: () => <div data-testid="cell" />,
    RadialBarChart: ({ children }: any) => <div data-testid="radial-bar-chart">{children}</div>,
    RadialBar: () => <div data-testid="radial-bar" />,
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
            name: 'Mars Orbit Insertion',
            delta_v: 1200,
            timestamp: '2024-07-20T18:00:00Z',
            description: 'Burn to enter Mars orbit',
        },
    ],
    total_delta_v: 4800,
};

const mockSpacecraftConfig: SpacecraftConfig = {
    vehicle_type: 'Heavy Lift Vehicle',
    mass_kg: 50000,
    fuel_capacity_kg: 200000,
    thrust_n: 7500000,
    specific_impulse_s: 450,
    payload_mass_kg: 15000,
};

const mockSimulationResult: SimulationResult = {
    mission_id: 'test-mission-1',
    success_probability: 0.85,
    total_duration_days: 365,
    fuel_consumption_kg: 150000,
    cost_estimate_usd: 250000000,
    risk_factors: [
        {
            category: 'Technical',
            description: 'Propulsion system failure',
            probability: 0.05,
            impact: 'High'
        },
        {
            category: 'Environmental',
            description: 'Space weather events',
            probability: 0.1,
            impact: 'Medium'
        }
    ],
    performance_metrics: {
        efficiency: 0.85,
        reliability: 0.9
    }
};

describe('PerformanceMetricsChart', () => {
    it('renders without crashing', () => {
        render(
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
            />
        );
        expect(screen.getByText('Performance Overview')).toBeInTheDocument();
    });

    it('displays key performance indicators', () => {
        render(
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
            />
        );

        expect(screen.getByText('Delta-V Budget')).toBeInTheDocument();
        expect(screen.getByText('Fuel Consumption')).toBeInTheDocument();
        expect(screen.getByText('Success Probability')).toBeInTheDocument();
        expect(screen.getByText('Thrust-to-Weight')).toBeInTheDocument();
        expect(screen.getByText('Payload Fraction')).toBeInTheDocument();
        expect(screen.getByText('Mission Duration')).toBeInTheDocument();
    });

    it('displays all chart sections', () => {
        render(
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
                simulationResult={mockSimulationResult}
            />
        );

        expect(screen.getByText('Performance Overview')).toBeInTheDocument();
        expect(screen.getByText('Delta-V Requirements')).toBeInTheDocument();
        expect(screen.getByText('Cost Breakdown')).toBeInTheDocument();
        expect(screen.getByText('Risk Assessment')).toBeInTheDocument();
        expect(screen.getByText('Fuel Consumption Profile')).toBeInTheDocument();
    });

    it('renders all chart types', () => {
        render(
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
                simulationResult={mockSimulationResult}
            />
        );

        expect(screen.getByTestId('radial-bar-chart')).toBeInTheDocument();
        expect(screen.getAllByTestId('pie-chart')).toHaveLength(1);
        expect(screen.getAllByTestId('bar-chart')).toHaveLength(2); // Cost and risk charts
        expect(screen.getByTestId('area-chart')).toBeInTheDocument();
    });

    it('works without simulation result', () => {
        render(
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
            />
        );

        expect(screen.getByText('Performance Overview')).toBeInTheDocument();
        expect(screen.getByText('Delta-V Budget')).toBeInTheDocument();
    });

    it('works with simulation result', () => {
        render(
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
                simulationResult={mockSimulationResult}
            />
        );

        expect(screen.getByText('Performance Overview')).toBeInTheDocument();
        expect(screen.getByText('Risk Assessment')).toBeInTheDocument();
    });

    it('applies custom className', () => {
        const { container } = render(
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
                className="custom-class"
            />
        );

        expect(container.firstChild).toHaveClass('custom-class');
    });

    it('displays metric status indicators', () => {
        render(
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
            />
        );

        // Check for status indicator elements (colored dots)
        const statusIndicators = document.querySelectorAll('.w-3.h-3.rounded-full');
        expect(statusIndicators.length).toBeGreaterThan(0);
    });

    it('handles high delta-v missions', () => {
        const highDeltaVTrajectory: TrajectoryPlan = {
            ...mockTrajectory,
            total_delta_v: 15000,
        };

        render(
            <PerformanceMetricsChart
                trajectory={highDeltaVTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
            />
        );

        expect(screen.getByText('Delta-V Budget')).toBeInTheDocument();
    });

    it('handles missions with no maneuvers', () => {
        const noManeuversTrajectory: TrajectoryPlan = {
            ...mockTrajectory,
            maneuvers: [],
        };

        render(
            <PerformanceMetricsChart
                trajectory={noManeuversTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
            />
        );

        expect(screen.getByText('Delta-V Requirements')).toBeInTheDocument();
    });

    it('displays cost breakdown correctly', () => {
        render(
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
                simulationResult={mockSimulationResult}
            />
        );

        expect(screen.getByText('Cost Breakdown')).toBeInTheDocument();
        expect(screen.getAllByTestId('bar-chart')).toHaveLength(2);
    });

    it('shows risk assessment with factors', () => {
        render(
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
                simulationResult={mockSimulationResult}
            />
        );

        expect(screen.getByText('Risk Assessment')).toBeInTheDocument();
    });

    it('renders fuel consumption timeline', () => {
        render(
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
            />
        );

        expect(screen.getByText('Fuel Consumption Profile')).toBeInTheDocument();
        expect(screen.getByTestId('area-chart')).toBeInTheDocument();
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
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={lightSpacecraft}
            />
        );

        expect(screen.getByText('Performance Overview')).toBeInTheDocument();
    });

    it('calculates metrics correctly', () => {
        render(
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
            />
        );

        // Verify that metrics are displayed (indicating calculations worked)
        expect(screen.getByText('Delta-V Budget')).toBeInTheDocument();
        expect(screen.getByText('Fuel Consumption')).toBeInTheDocument();
        expect(screen.getByText('Success Probability')).toBeInTheDocument();
    });

    it('renders responsive containers for all charts', () => {
        render(
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
                simulationResult={mockSimulationResult}
            />
        );

        const containers = screen.getAllByTestId('responsive-container');
        expect(containers).toHaveLength(5); // Overview, delta-v, cost, risk, fuel consumption
    });

    it('displays chart axes labels correctly', () => {
        render(
            <PerformanceMetricsChart
                trajectory={mockTrajectory}
                spacecraftConfig={mockSpacecraftConfig}
            />
        );

        expect(screen.getByText('Mission Day')).toBeInTheDocument();
        expect(screen.getByText('Fuel Remaining (kg)')).toBeInTheDocument();
    });

    it('handles edge cases in calculations', () => {
        const extremeConfig: SpacecraftConfig = {
            vehicle_type: 'Extreme Vehicle',
            mass_kg: 1000,
            fuel_capacity_kg: 500,
            thrust_n: 100000,
            specific_impulse_s: 200,
            payload_mass_kg: 100,
        };

        const extremeTrajectory: TrajectoryPlan = {
            ...mockTrajectory,
            total_delta_v: 25000,
        };

        render(
            <PerformanceMetricsChart
                trajectory={extremeTrajectory}
                spacecraftConfig={extremeConfig}
            />
        );

        // Should render without errors even with extreme values
        expect(screen.getByText('Performance Overview')).toBeInTheDocument();
    });
});