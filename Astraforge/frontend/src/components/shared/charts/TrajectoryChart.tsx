import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
} from 'recharts';
import { TrajectoryPlan } from '../../../types/mission';

interface TrajectoryChartProps {
  trajectory: TrajectoryPlan;
  className?: string;
}

interface TrajectoryPoint {
  time: number;
  x: number;
  y: number;
  z: number;
  velocity: number;
  altitude: number;
}

interface ManeuverPoint {
  time: number;
  deltaV: number;
  name: string;
}

export const TrajectoryChart: React.FC<TrajectoryChartProps> = ({
  trajectory,
  className = '',
}) => {
  // Generate trajectory points based on maneuvers
  const generateTrajectoryPoints = (): TrajectoryPoint[] => {
    const points: TrajectoryPoint[] = [];
    const totalDuration = 365; // Default mission duration in days
    
    // Generate points for visualization
    for (let day = 0; day <= totalDuration; day += 5) {
      // Simplified orbital mechanics calculation for visualization
      const angle = (day / totalDuration) * 2 * Math.PI;
      const radius = 150 + Math.sin(angle * 3) * 50; // Varying orbital radius
      
      points.push({
        time: day,
        x: radius * Math.cos(angle),
        y: radius * Math.sin(angle),
        z: Math.sin(angle * 2) * 20,
        velocity: 7.8 + Math.random() * 0.5, // km/s
        altitude: radius - 150, // km above surface
      });
    }
    
    return points;
  };

  // Convert maneuvers to chart data
  const maneuverPoints: ManeuverPoint[] = trajectory.maneuvers.map((maneuver, index) => ({
    time: index * 30, // Spread maneuvers across mission timeline
    deltaV: maneuver.delta_v,
    name: maneuver.name,
  }));

  const trajectoryPoints = generateTrajectoryPoints();

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 2D Trajectory Plot */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Orbital Trajectory (2D View)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart data={trajectoryPoints}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="x" 
              type="number"
              domain={['dataMin - 50', 'dataMax + 50']}
              label={{ value: 'X Position (km)', position: 'insideBottom', offset: -10 }}
            />
            <YAxis 
              dataKey="y" 
              type="number"
              domain={['dataMin - 50', 'dataMax + 50']}
              label={{ value: 'Y Position (km)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              formatter={(value, name) => [
                typeof value === 'number' ? value.toFixed(2) : value,
                name
              ]}
              labelFormatter={(label) => `Time: ${label} days`}
            />
            <Scatter 
              dataKey="y" 
              fill="#3b82f6" 
              name="Trajectory"
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* Velocity Profile */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Velocity Profile</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={trajectoryPoints}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="time" 
              label={{ value: 'Time (days)', position: 'insideBottom', offset: -10 }}
            />
            <YAxis 
              label={{ value: 'Velocity (km/s)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              formatter={(value) => [
                typeof value === 'number' ? `${value.toFixed(2)} km/s` : value,
                'Velocity'
              ]}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="velocity" 
              stroke="#10b981" 
              strokeWidth={2}
              dot={false}
              name="Orbital Velocity"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Altitude Profile */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Altitude Profile</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={trajectoryPoints}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="time" 
              label={{ value: 'Time (days)', position: 'insideBottom', offset: -10 }}
            />
            <YAxis 
              label={{ value: 'Altitude (km)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              formatter={(value) => [
                typeof value === 'number' ? `${value.toFixed(0)} km` : value,
                'Altitude'
              ]}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="altitude" 
              stroke="#f59e0b" 
              strokeWidth={2}
              dot={false}
              name="Altitude"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Delta-V Maneuvers */}
      {maneuverPoints.length > 0 && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Delta-V Maneuvers</h3>
          <ResponsiveContainer width="100%" height={250}>
            <ScatterChart data={maneuverPoints}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="time" 
                type="number"
                label={{ value: 'Time (days)', position: 'insideBottom', offset: -10 }}
              />
              <YAxis 
                dataKey="deltaV" 
                type="number"
                label={{ value: 'Delta-V (m/s)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                formatter={(value, name) => [
                  typeof value === 'number' ? `${value.toFixed(1)} m/s` : value,
                  name
                ]}
                labelFormatter={(label) => `Time: ${label} days`}
              />
              <Scatter 
                dataKey="deltaV" 
                fill="#ef4444" 
                name="Maneuvers"
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};