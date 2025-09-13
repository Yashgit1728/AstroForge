import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

interface SimulationResult {
  id: string;
  missionName: string;
  vehicleName: string;
  successProbability: number;
  totalDurationDays: number;
  fuelConsumptionKg: number;
  costEstimateUsd: number;
  status: 'completed' | 'running' | 'failed';
  createdAt: string;
}

const SimulationCenter: React.FC = () => {
  const [selectedSimulation, setSelectedSimulation] = useState<SimulationResult | null>(null);
  const [isRunningSimulation, setIsRunningSimulation] = useState(false);
  const [simulationProgress, setSimulationProgress] = useState(0);

  // Mock simulation results
  const simulationResults: SimulationResult[] = [
    {
      id: '1',
      missionName: 'Mars Sample Return',
      vehicleName: 'Mars Reconnaissance Probe',
      successProbability: 0.94,
      totalDurationDays: 687,
      fuelConsumptionKg: 750,
      costEstimateUsd: 2500000000,
      status: 'completed',
      createdAt: '2024-12-10T10:30:00Z'
    },
    {
      id: '2',
      missionName: 'Lunar Gateway',
      vehicleName: 'Medium Satellite',
      successProbability: 0.87,
      totalDurationDays: 14,
      fuelConsumptionKg: 320,
      costEstimateUsd: 150000000,
      status: 'completed',
      createdAt: '2024-12-09T15:45:00Z'
    },
    {
      id: '3',
      missionName: 'Europa Explorer',
      vehicleName: 'Deep Space Probe',
      successProbability: 0.76,
      totalDurationDays: 2190,
      fuelConsumptionKg: 2800,
      costEstimateUsd: 4200000000,
      status: 'running',
      createdAt: '2024-12-12T09:15:00Z'
    }
  ];

  // Mock trajectory data for visualization
  const trajectoryData = [
    { time: 0, velocity: 0, altitude: 0, fuel: 100 },
    { time: 10, velocity: 2500, altitude: 150, fuel: 85 },
    { time: 20, velocity: 7800, altitude: 400, fuel: 70 },
    { time: 30, velocity: 11200, altitude: 35786, fuel: 55 },
    { time: 40, velocity: 10800, altitude: 384400, fuel: 40 },
    { time: 50, velocity: 1000, altitude: 384400, fuel: 35 }
  ];

  const performanceData = [
    { phase: 'Launch', efficiency: 0.92, deltaV: 9500 },
    { phase: 'Trans-lunar', efficiency: 0.88, deltaV: 3200 },
    { phase: 'Lunar Orbit', efficiency: 0.95, deltaV: 800 },
    { phase: 'Landing', efficiency: 0.85, deltaV: 2000 }
  ];

  const runSimulation = () => {
    setIsRunningSimulation(true);
    setSimulationProgress(0);

    const interval = setInterval(() => {
      setSimulationProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsRunningSimulation(false);
          return 100;
        }
        return prev + 10;
      });
    }, 500);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      notation: 'compact',
      maximumFractionDigits: 1
    }).format(amount);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400';
      case 'running': return 'text-yellow-400';
      case 'failed': return 'text-red-400';
      default: return 'text-space-300';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-600';
      case 'running': return 'bg-yellow-600';
      case 'failed': return 'bg-red-600';
      default: return 'bg-space-600';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 relative z-10">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-3xl font-bold text-white mb-2">Simulation Center</h2>
            <p className="text-space-300">Run and analyze mission simulations</p>
          </div>
          <button
            onClick={runSimulation}
            disabled={isRunningSimulation}
            className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
              isRunningSimulation
                ? 'bg-space-600 text-space-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {isRunningSimulation ? 'Running...' : '🚀 Run New Simulation'}
          </button>
        </div>

        {/* Simulation Progress */}
        {isRunningSimulation && (
          <div className="bg-space-800/50 backdrop-blur-sm rounded-lg p-6 border border-space-600 mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white font-medium">Simulation Progress</span>
              <span className="text-space-300">{simulationProgress}%</span>
            </div>
            <div className="w-full bg-space-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${simulationProgress}%` }}
              />
            </div>
            <div className="mt-2 text-space-400 text-sm">
              {simulationProgress < 30 && 'Initializing orbital mechanics...'}
              {simulationProgress >= 30 && simulationProgress < 60 && 'Calculating trajectory...'}
              {simulationProgress >= 60 && simulationProgress < 90 && 'Analyzing fuel consumption...'}
              {simulationProgress >= 90 && 'Finalizing results...'}
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Simulation Results List */}
        <div className="lg:col-span-1">
          <div className="bg-space-800/50 backdrop-blur-sm rounded-lg p-6 border border-space-600">
            <h3 className="text-xl font-semibold text-white mb-4">Recent Simulations</h3>
            <div className="space-y-4">
              {simulationResults.map(result => (
                <div
                  key={result.id}
                  onClick={() => setSelectedSimulation(result)}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedSimulation?.id === result.id
                      ? 'border-blue-400 bg-space-700'
                      : 'border-space-600 hover:border-space-500 bg-space-900/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-white font-medium text-sm">{result.missionName}</h4>
                    <span className={`px-2 py-1 rounded text-xs ${getStatusBg(result.status)} text-white`}>
                      {result.status}
                    </span>
                  </div>
                  <div className="text-space-300 text-xs mb-2">{result.vehicleName}</div>
                  <div className="flex justify-between text-xs">
                    <span className="text-space-400">Success:</span>
                    <span className={getStatusColor(result.status)}>
                      {(result.successProbability * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-space-400">Duration:</span>
                    <span className="text-space-300">{result.totalDurationDays} days</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Simulation Details */}
        <div className="lg:col-span-2 space-y-6">
          {selectedSimulation ? (
            <>
              {/* Simulation Overview */}
              <div className="bg-space-800/50 backdrop-blur-sm rounded-lg p-6 border border-space-600">
                <h3 className="text-xl font-semibold text-white mb-4">
                  {selectedSimulation.missionName} - Simulation Results
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-400">
                      {(selectedSimulation.successProbability * 100).toFixed(1)}%
                    </div>
                    <div className="text-space-400 text-sm">Success Rate</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-400">
                      {selectedSimulation.totalDurationDays}
                    </div>
                    <div className="text-space-400 text-sm">Days</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-400">
                      {selectedSimulation.fuelConsumptionKg.toLocaleString()}
                    </div>
                    <div className="text-space-400 text-sm">kg Fuel</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-400">
                      {formatCurrency(selectedSimulation.costEstimateUsd)}
                    </div>
                    <div className="text-space-400 text-sm">Cost</div>
                  </div>
                </div>
              </div>

              {/* Trajectory Visualization */}
              <div className="bg-space-800/50 backdrop-blur-sm rounded-lg p-6 border border-space-600">
                <h4 className="text-lg font-semibold text-white mb-4">Mission Trajectory</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={trajectoryData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="time" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1F2937', 
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        color: '#F9FAFB'
                      }} 
                    />
                    <Area 
                      type="monotone" 
                      dataKey="altitude" 
                      stroke="#3B82F6" 
                      fill="#3B82F6" 
                      fillOpacity={0.3}
                      name="Altitude (km)"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="velocity" 
                      stroke="#10B981" 
                      fill="#10B981" 
                      fillOpacity={0.3}
                      name="Velocity (m/s)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Performance Analysis */}
              <div className="bg-space-800/50 backdrop-blur-sm rounded-lg p-6 border border-space-600">
                <h4 className="text-lg font-semibold text-white mb-4">Performance Analysis</h4>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="phase" stroke="#9CA3AF" />
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
                      dataKey="efficiency" 
                      stroke="#8B5CF6" 
                      strokeWidth={2}
                      name="Efficiency"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Risk Analysis */}
              <div className="bg-space-800/50 backdrop-blur-sm rounded-lg p-6 border border-space-600">
                <h4 className="text-lg font-semibold text-white mb-4">Risk Analysis</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-space-900/50 rounded">
                    <div>
                      <div className="text-white font-medium">Propulsion System Failure</div>
                      <div className="text-space-400 text-sm">Critical system malfunction</div>
                    </div>
                    <div className="text-right">
                      <div className="text-red-400 font-medium">5%</div>
                      <div className="text-space-400 text-sm">High Impact</div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-space-900/50 rounded">
                    <div>
                      <div className="text-white font-medium">Communication Loss</div>
                      <div className="text-space-400 text-sm">Temporary signal interruption</div>
                    </div>
                    <div className="text-right">
                      <div className="text-yellow-400 font-medium">12%</div>
                      <div className="text-space-400 text-sm">Medium Impact</div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-space-900/50 rounded">
                    <div>
                      <div className="text-white font-medium">Navigation Drift</div>
                      <div className="text-space-400 text-sm">Minor course correction needed</div>
                    </div>
                    <div className="text-right">
                      <div className="text-green-400 font-medium">8%</div>
                      <div className="text-space-400 text-sm">Low Impact</div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-space-800/50 backdrop-blur-sm rounded-lg p-12 border border-space-600 text-center">
              <div className="text-6xl mb-4">🚀</div>
              <h3 className="text-xl font-semibold text-white mb-2">Select a Simulation</h3>
              <p className="text-space-300">Choose a simulation from the list to view detailed results and analysis</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SimulationCenter;