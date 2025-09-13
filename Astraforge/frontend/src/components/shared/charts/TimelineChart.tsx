import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  Area,
  AreaChart,
} from 'recharts';
import { MissionTimeline, Maneuver } from '../../../types/mission';

interface TimelineChartProps {
  timeline: MissionTimeline;
  maneuvers?: Maneuver[];
  className?: string;
}

interface TimelineEvent {
  day: number;
  phase: string;
  event: string;
  type: 'phase' | 'maneuver' | 'milestone';
  duration?: number;
  deltaV?: number;
}

interface PhaseData {
  name: string;
  startDay: number;
  endDay: number;
  duration: number;
  progress: number;
  color: string;
}

const PHASE_COLORS = [
  '#3b82f6', // Blue
  '#10b981', // Green
  '#f59e0b', // Yellow
  '#ef4444', // Red
  '#8b5cf6', // Purple
  '#06b6d4', // Cyan
  '#f97316', // Orange
  '#84cc16', // Lime
];

export const TimelineChart: React.FC<TimelineChartProps> = ({
  timeline,
  maneuvers = [],
  className = '',
}) => {
  // Process timeline data for visualization
  const processTimelineData = (): {
    phaseData: PhaseData[];
    events: TimelineEvent[];
    dailyProgress: Array<{ day: number; progress: number; phase: string }>;
  } => {
    const phaseData: PhaseData[] = timeline.phases.map((phase, index) => ({
      name: phase.name,
      startDay: phase.start_day,
      endDay: phase.start_day + phase.duration_days,
      duration: phase.duration_days,
      progress: 100, // Assume completed for visualization
      color: PHASE_COLORS[index % PHASE_COLORS.length],
    }));

    const events: TimelineEvent[] = [];
    
    // Add phase events
    timeline.phases.forEach((phase) => {
      events.push({
        day: phase.start_day,
        phase: phase.name,
        event: `Start ${phase.name}`,
        type: 'phase',
        duration: phase.duration_days,
      });
      
      events.push({
        day: phase.start_day + phase.duration_days,
        phase: phase.name,
        event: `End ${phase.name}`,
        type: 'milestone',
      });
    });

    // Add maneuver events
    maneuvers.forEach((maneuver, index) => {
      const maneuverDay = (index + 1) * (timeline.total_duration_days / (maneuvers.length + 1));
      events.push({
        day: maneuverDay,
        phase: 'Maneuver',
        event: maneuver.name,
        type: 'maneuver',
        deltaV: maneuver.delta_v,
      });
    });

    // Generate daily progress data
    const dailyProgress: Array<{ day: number; progress: number; phase: string }> = [];
    for (let day = 0; day <= timeline.total_duration_days; day += Math.max(1, Math.floor(timeline.total_duration_days / 100))) {
      const currentPhase = timeline.phases.find(
        (phase) => day >= phase.start_day && day < phase.start_day + phase.duration_days
      );
      
      const overallProgress = (day / timeline.total_duration_days) * 100;
      
      dailyProgress.push({
        day,
        progress: overallProgress,
        phase: currentPhase?.name || 'Transit',
      });
    }

    return { phaseData, events, dailyProgress };
  };

  const { phaseData, events, dailyProgress } = processTimelineData();

  // Gantt chart data
  const ganttData = phaseData.map((phase) => ({
    name: phase.name,
    start: phase.startDay,
    duration: phase.duration,
    end: phase.endDay,
  }));

  // Events for scatter plot
  const eventData = events.map((event) => ({
    day: event.day,
    type: event.type,
    name: event.event,
    deltaV: event.deltaV || 0,
    phase: event.phase,
  }));

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Mission Progress Over Time */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Mission Progress Timeline</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={dailyProgress}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="day" 
              label={{ value: 'Mission Day', position: 'insideBottom', offset: -10 }}
            />
            <YAxis 
              label={{ value: 'Progress (%)', angle: -90, position: 'insideLeft' }}
              domain={[0, 100]}
            />
            <Tooltip 
              formatter={(value) => [
                `${typeof value === 'number' ? value.toFixed(1) : value}%`,
                'Progress'
              ]}
              labelFormatter={(label) => `Day ${label}`}
            />
            <Area
              type="monotone"
              dataKey="progress"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.3}
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Phase Duration Gantt Chart */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Mission Phases</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart 
            data={ganttData} 
            layout="horizontal"
            margin={{ top: 20, right: 30, left: 100, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              type="number" 
              label={{ value: 'Days', position: 'insideBottom', offset: -10 }}
            />
            <YAxis 
              dataKey="name" 
              type="category" 
              width={90}
            />
            <Tooltip 
              formatter={(value, name) => {
                if (name === 'duration') return [`${value} days`, 'Duration'];
                if (name === 'start') return [`Day ${value}`, 'Start Day'];
                return [value, name];
              }}
            />
            <Legend />
            <Bar 
              dataKey="duration" 
              fill="#10b981" 
              name="Phase Duration"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Mission Events Timeline */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Mission Events</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={eventData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="day" 
              label={{ value: 'Mission Day', position: 'insideBottom', offset: -10 }}
            />
            <YAxis 
              dataKey="deltaV" 
              label={{ value: 'Delta-V (m/s)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              formatter={(value, name) => {
                if (name === 'deltaV') return [`${value} m/s`, 'Delta-V'];
                return [value, name];
              }}
              labelFormatter={(label) => `Day ${label}`}
            />
            <Line 
              type="monotone" 
              dataKey="deltaV" 
              stroke="#ef4444" 
              strokeWidth={2}
              dot={{ fill: '#ef4444', strokeWidth: 2, r: 4 }}
              name="Maneuver Delta-V"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Phase Summary Table */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Phase Summary</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Phase
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Start Day
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  End Day
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {timeline.phases.map((phase, index) => (
                <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    <div className="flex items-center">
                      <div 
                        className="w-3 h-3 rounded-full mr-2"
                        style={{ backgroundColor: PHASE_COLORS[index % PHASE_COLORS.length] }}
                      />
                      {phase.name}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {phase.start_day}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {phase.duration_days} days
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {phase.start_day + phase.duration_days}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {phase.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};