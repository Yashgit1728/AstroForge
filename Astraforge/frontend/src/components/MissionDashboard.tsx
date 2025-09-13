import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

interface MissionStats {
  totalMissions: number;
  successfulMissions: number;
  activeMissions: number;
  totalDeltaV: number;
}

const MissionDashboard: React.FC = () => {
  const stats: MissionStats = {
    totalMissions: 42,
    successfulMissions: 38,
    activeMissions: 4,
    totalDeltaV: 156780
  };

  // Mock data for charts
  const missionData = [
    { month: 'Jan', missions: 3, success: 3 },
    { month: 'Feb', missions: 5, success: 4 },
    { month: 'Mar', missions: 4, success: 4 },
    { month: 'Apr', missions: 6, success: 5 },
    { month: 'May', missions: 8, success: 7 },
    { month: 'Jun', missions: 7, success: 6 }
  ];

  const vehicleUsage = [
    { type: 'CubeSat', count: 15 },
    { type: 'Medium Sat', count: 12 },
    { type: 'Probe', count: 8 },
    { type: 'Lander', count: 4 },
    { type: 'Rover', count: 2 },
    { type: 'Crewed', count: 1 }
  ];

  const StatCard: React.FC<{ title: string; value: string | number; icon: string; color: string }> = 
    ({ title, value, icon, color }) => (
    <div className="bg-space-800 rounded-lg p-6 border border-space-600">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-space-400 text-sm font-medium">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
        </div>
        <div className={`w-12 h-12 rounded-lg ${color} flex items-center justify-center text-2xl`}>
          {icon}
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Mission Dashboard</h2>
        <p className="text-space-300">Overview of your space missions and performance</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Missions"
          value={stats.totalMissions}
          icon="🚀"
          color="bg-blue-600"
        />
        <StatCard
          title="Success Rate"
          value={`${Math.round((stats.successfulMissions / stats.totalMissions) * 100)}%`}
          icon="✅"
          color="bg-green-600"
        />
        <StatCard
          title="Active Missions"
          value={stats.activeMissions}
          icon="🛰️"
          color="bg-yellow-600"
        />
        <StatCard
          title="Total ΔV Used"
          value={`${(stats.totalDeltaV / 1000).toFixed(1)}k m/s`}
          icon="⚡"
          color="bg-purple-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Mission Timeline */}
        <div className="bg-space-800 rounded-lg p-6 border border-space-600">
          <h3 className="text-xl font-semibold text-white mb-4">Mission Timeline</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={missionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="month" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F9FAFB'
                }} 
              />
              <Line 
                type="monotone" 
                dataKey="missions" 
                stroke="#3B82F6" 
                strokeWidth={2}
                name="Total Missions"
              />
              <Line 
                type="monotone" 
                dataKey="success" 
                stroke="#10B981" 
                strokeWidth={2}
                name="Successful"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Vehicle Usage */}
        <div className="bg-space-800 rounded-lg p-6 border border-space-600">
          <h3 className="text-xl font-semibold text-white mb-4">Vehicle Usage</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={vehicleUsage}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="type" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F9FAFB'
                }} 
              />
              <Bar dataKey="count" fill="#8B5CF6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Missions */}
      <div className="mt-8 bg-space-800 rounded-lg p-6 border border-space-600">
        <h3 className="text-xl font-semibold text-white mb-4">Recent Missions</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-space-600">
                <th className="pb-3 text-space-300 font-medium">Mission</th>
                <th className="pb-3 text-space-300 font-medium">Vehicle</th>
                <th className="pb-3 text-space-300 font-medium">Destination</th>
                <th className="pb-3 text-space-300 font-medium">Status</th>
                <th className="pb-3 text-space-300 font-medium">Success Rate</th>
              </tr>
            </thead>
            <tbody className="text-white">
              <tr className="border-b border-space-700">
                <td className="py-3">Mars Sample Return</td>
                <td className="py-3">Mars Probe</td>
                <td className="py-3">🔴 Mars</td>
                <td className="py-3">
                  <span className="bg-green-600 text-white px-2 py-1 rounded text-xs">
                    Completed
                  </span>
                </td>
                <td className="py-3">94%</td>
              </tr>
              <tr className="border-b border-space-700">
                <td className="py-3">Lunar Gateway</td>
                <td className="py-3">Medium Satellite</td>
                <td className="py-3">🌙 Moon</td>
                <td className="py-3">
                  <span className="bg-yellow-600 text-white px-2 py-1 rounded text-xs">
                    Active
                  </span>
                </td>
                <td className="py-3">87%</td>
              </tr>
              <tr className="border-b border-space-700">
                <td className="py-3">Earth Observation</td>
                <td className="py-3">CubeSat 6U</td>
                <td className="py-3">🌍 Earth Orbit</td>
                <td className="py-3">
                  <span className="bg-green-600 text-white px-2 py-1 rounded text-xs">
                    Completed
                  </span>
                </td>
                <td className="py-3">98%</td>
              </tr>
              <tr>
                <td className="py-3">Venus Atmospheric Study</td>
                <td className="py-3">Deep Space Probe</td>
                <td className="py-3">🟡 Venus</td>
                <td className="py-3">
                  <span className="bg-blue-600 text-white px-2 py-1 rounded text-xs">
                    Planning
                  </span>
                </td>
                <td className="py-3">--</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default MissionDashboard;