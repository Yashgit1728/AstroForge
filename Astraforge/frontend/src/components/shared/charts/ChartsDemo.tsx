import React from 'react';
import { TrajectoryChart } from './TrajectoryChart';
import { OrbitalParametersChart } from './OrbitalParametersChart';
import { TimelineChart } from './TimelineChart';
import { PerformanceMetricsChart } from './PerformanceMetricsChart';
import { Mission } from '../../../types/mission';

interface ChartsDemoProps {
  mission: Mission;
  className?: string;
}

export const ChartsDemo: React.FC<ChartsDemoProps> = ({
  mission,
  className = '',
}) => {
  return (
    <div className={`space-y-8 ${className}`}>
      <div className="bg-gray-50 p-6 rounded-lg">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Mission Analysis Dashboard</h2>
        <p className="text-gray-600 mb-4">
          Comprehensive visualization of mission parameters, trajectory analysis, and performance metrics.
        </p>
      </div>

      {/* Performance Metrics Overview */}
      <section>
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Performance Metrics</h3>
        <PerformanceMetricsChart
          trajectory={mission.trajectory}
          spacecraftConfig={mission.spacecraft_config}
        />
      </section>

      {/* Trajectory Analysis */}
      <section>
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Trajectory Analysis</h3>
        <TrajectoryChart trajectory={mission.trajectory} />
      </section>

      {/* Orbital Parameters */}
      <section>
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Orbital Parameters</h3>
        <OrbitalParametersChart
          trajectory={mission.trajectory}
          spacecraftConfig={mission.spacecraft_config}
        />
      </section>

      {/* Mission Timeline */}
      <section>
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Mission Timeline</h3>
        <TimelineChart
          timeline={mission.timeline}
          maneuvers={mission.trajectory.maneuvers}
        />
      </section>
    </div>
  );
};