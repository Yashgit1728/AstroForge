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

  Area,
  AreaChart,
  PieChart,
  Pie,
  Cell,
  RadialBarChart,
  RadialBar,
} from 'recharts';
import { SimulationResult, TrajectoryPlan, SpacecraftConfig } from '../../../types/mission';

interface PerformanceMetricsChartProps {
  simulationResult?: SimulationResult;
  trajectory: TrajectoryPlan;
  spacecraftConfig: SpacecraftConfig;
  className?: string;
}

interface MetricData {
  name: string;
  value: number;
  unit: string;
  target?: number;
  status: 'good' | 'warning' | 'critical';
  description: string;
}

interface DeltaVBreakdown {
  phase: string;
  deltaV: number;
  percentage: number;
  color: string;
}

interface CostBreakdown {
  category: string;
  cost: number;
  percentage: number;
  color: string;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];
// Risk color mapping for future use
// const RISK_COLORS = {
//   low: '#10b981',
//   medium: '#f59e0b',
//   high: '#ef4444',
//   critical: '#dc2626'
// };

export const PerformanceMetricsChart: React.FC<PerformanceMetricsChartProps> = ({
  simulationResult,
  trajectory,
  spacecraftConfig,
  className = '',
}) => {
  // Calculate performance metrics
  const calculateMetrics = (): MetricData[] => {
    const totalMass = spacecraftConfig.mass_kg + spacecraftConfig.fuel_capacity_kg;
    const thrustToWeight = spacecraftConfig.thrust_n / (totalMass * 9.81);
    const payloadFraction = (spacecraftConfig.payload_mass_kg / totalMass) * 100;
    
    // Use simulation result if available, otherwise estimate
    const fuelConsumption = simulationResult?.fuel_consumption_kg || 
      estimateFuelConsumption(trajectory.total_delta_v, spacecraftConfig);
    const successProbability = simulationResult?.success_probability || 
      estimateSuccessProbability(trajectory, spacecraftConfig);
    const missionDuration = simulationResult?.total_duration_days || 365;
    // Cost estimate for future use
    // const costEstimate = simulationResult?.cost_estimate_usd || 
    //   estimateCost(spacecraftConfig, trajectory);

    return [
      {
        name: 'Delta-V Budget',
        value: trajectory.total_delta_v,
        unit: 'm/s',
        target: 15000,
        status: trajectory.total_delta_v > 12000 ? 'critical' : 
                trajectory.total_delta_v > 8000 ? 'warning' : 'good',
        description: 'Total velocity change required for mission'
      },
      {
        name: 'Fuel Consumption',
        value: fuelConsumption,
        unit: 'kg',
        target: spacecraftConfig.fuel_capacity_kg * 0.9,
        status: fuelConsumption > spacecraftConfig.fuel_capacity_kg * 0.9 ? 'critical' :
                fuelConsumption > spacecraftConfig.fuel_capacity_kg * 0.7 ? 'warning' : 'good',
        description: 'Estimated fuel consumption'
      },
      {
        name: 'Success Probability',
        value: successProbability * 100,
        unit: '%',
        target: 85,
        status: successProbability < 0.7 ? 'critical' :
                successProbability < 0.85 ? 'warning' : 'good',
        description: 'Mission success probability'
      },
      {
        name: 'Thrust-to-Weight',
        value: thrustToWeight,
        unit: '',
        target: 1.5,
        status: thrustToWeight < 1.2 ? 'critical' :
                thrustToWeight < 1.5 ? 'warning' : 'good',
        description: 'Thrust to weight ratio'
      },
      {
        name: 'Payload Fraction',
        value: payloadFraction,
        unit: '%',
        target: 15,
        status: payloadFraction < 5 ? 'critical' :
                payloadFraction < 10 ? 'warning' : 'good',
        description: 'Payload as percentage of total mass'
      },
      {
        name: 'Mission Duration',
        value: missionDuration,
        unit: 'days',
        target: 500,
        status: missionDuration > 800 ? 'warning' :
                missionDuration > 1200 ? 'critical' : 'good',
        description: 'Total mission duration'
      }
    ];
  };

  // Estimate fuel consumption using rocket equation
  const estimateFuelConsumption = (deltaV: number, config: SpacecraftConfig): number => {
    const massRatio = Math.exp(deltaV / (config.specific_impulse_s * 9.81));
    const initialMass = config.mass_kg + config.fuel_capacity_kg;
    const finalMass = initialMass / massRatio;
    return Math.min(initialMass - finalMass, config.fuel_capacity_kg);
  };

  // Estimate success probability based on complexity
  const estimateSuccessProbability = (traj: TrajectoryPlan, config: SpacecraftConfig): number => {
    let probability = 0.95; // Base probability
    
    // Reduce probability based on delta-v requirements
    if (traj.total_delta_v > 10000) probability -= 0.1;
    if (traj.total_delta_v > 15000) probability -= 0.15;
    
    // Reduce probability based on number of maneuvers
    probability -= traj.maneuvers.length * 0.02;
    
    // Adjust based on thrust-to-weight ratio
    const thrustToWeight = config.thrust_n / ((config.mass_kg + config.fuel_capacity_kg) * 9.81);
    if (thrustToWeight < 1.2) probability -= 0.1;
    
    return Math.max(probability, 0.3);
  };

  // Estimate mission cost
  const estimateCost = (config: SpacecraftConfig, traj: TrajectoryPlan): number => {
    const baseCost = 100000000; // $100M base
    const massMultiplier = (config.mass_kg + config.fuel_capacity_kg) / 50000;
    const complexityMultiplier = 1 + (traj.maneuvers.length * 0.1);
    const deltaVMultiplier = 1 + (traj.total_delta_v / 20000);
    
    return baseCost * massMultiplier * complexityMultiplier * deltaVMultiplier;
  };

  // Generate delta-v breakdown
  const generateDeltaVBreakdown = (): DeltaVBreakdown[] => {
    const maneuvers = trajectory.maneuvers;
    const totalDeltaV = trajectory.total_delta_v;
    
    if (maneuvers.length === 0) {
      return [
        {
          phase: 'Total Mission',
          deltaV: totalDeltaV,
          percentage: 100,
          color: COLORS[0]
        }
      ];
    }
    
    return maneuvers.map((maneuver, index) => ({
      phase: maneuver.name,
      deltaV: maneuver.delta_v,
      percentage: (maneuver.delta_v / totalDeltaV) * 100,
      color: COLORS[index % COLORS.length]
    }));
  };

  // Generate cost breakdown
  const generateCostBreakdown = (): CostBreakdown[] => {
    const totalCost = simulationResult?.cost_estimate_usd || estimateCost(spacecraftConfig, trajectory);
    
    return [
      {
        category: 'Launch Vehicle',
        cost: totalCost * 0.4,
        percentage: 40,
        color: COLORS[0]
      },
      {
        category: 'Spacecraft',
        cost: totalCost * 0.3,
        percentage: 30,
        color: COLORS[1]
      },
      {
        category: 'Operations',
        cost: totalCost * 0.15,
        percentage: 15,
        color: COLORS[2]
      },
      {
        category: 'Ground Systems',
        cost: totalCost * 0.1,
        percentage: 10,
        color: COLORS[3]
      },
      {
        category: 'Contingency',
        cost: totalCost * 0.05,
        percentage: 5,
        color: COLORS[4]
      }
    ];
  };

  // Generate risk factors data
  const generateRiskFactors = () => {
    const riskFactors = simulationResult?.risk_factors || [
      { category: 'Technical', description: 'Propulsion system failure', probability: 0.05, impact: 'High' },
      { category: 'Environmental', description: 'Space weather events', probability: 0.1, impact: 'Medium' },
      { category: 'Operational', description: 'Communication loss', probability: 0.03, impact: 'Medium' },
      { category: 'Schedule', description: 'Launch window delays', probability: 0.15, impact: 'Low' }
    ];

    return riskFactors.map((risk, index) => ({
      name: risk.category,
      probability: risk.probability * 100,
      impact: risk.impact,
      description: risk.description,
      riskScore: risk.probability * (risk.impact === 'High' ? 3 : risk.impact === 'Medium' ? 2 : 1) * 100,
      color: COLORS[index % COLORS.length]
    }));
  };

  const metrics = calculateMetrics();
  const deltaVBreakdown = generateDeltaVBreakdown();
  const costBreakdown = generateCostBreakdown();
  const riskFactors = generateRiskFactors();

  // Prepare data for radial chart (key metrics)
  const radialData = [
    {
      name: 'Success Rate',
      value: metrics.find(m => m.name === 'Success Probability')?.value || 0,
      fill: '#10b981'
    },
    {
      name: 'Efficiency',
      value: Math.min((metrics.find(m => m.name === 'Payload Fraction')?.value || 0) * 5, 100),
      fill: '#3b82f6'
    },
    {
      name: 'Fuel Usage',
      value: 100 - ((metrics.find(m => m.name === 'Fuel Consumption')?.value || 0) / spacecraftConfig.fuel_capacity_kg) * 100,
      fill: '#f59e0b'
    }
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {metrics.map((metric, index) => (
          <div key={index} className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-gray-600">{metric.name}</h4>
              <div className={`w-3 h-3 rounded-full ${
                metric.status === 'good' ? 'bg-green-500' :
                metric.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {typeof metric.value === 'number' ? metric.value.toFixed(1) : metric.value}
              <span className="text-sm font-normal text-gray-500 ml-1">{metric.unit}</span>
            </div>
            {metric.target && (
              <div className="text-xs text-gray-500 mt-1">
                Target: {metric.target} {metric.unit}
              </div>
            )}
            <p className="text-xs text-gray-600 mt-2">{metric.description}</p>
          </div>
        ))}
      </div>

      {/* Performance Overview Radial Chart */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Performance Overview</h3>
        <ResponsiveContainer width="100%" height={300}>
          <RadialBarChart data={radialData} innerRadius="20%" outerRadius="80%">
            <RadialBar dataKey="value" cornerRadius={10} fill="#8884d8" />
            <Tooltip formatter={(value) => [`${typeof value === 'number' ? value.toFixed(1) : value}%`, 'Score']} />
            <Legend />
          </RadialBarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Delta-V Requirements Breakdown */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Delta-V Requirements</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={deltaVBreakdown}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ phase, percentage }) => `${phase} ${percentage.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="deltaV"
              >
                {deltaVBreakdown.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => [`${value} m/s`, 'Delta-V']} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Cost Breakdown */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Cost Breakdown</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={costBreakdown}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip 
                formatter={(value) => [
                  `$${(typeof value === 'number' ? value / 1000000 : 0).toFixed(1)}M`,
                  'Cost'
                ]}
              />
              <Bar dataKey="cost" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Risk Assessment */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Risk Assessment</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={riskFactors} layout="horizontal">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="name" type="category" width={100} />
            <Tooltip 
              formatter={(value, name) => {
                if (name === 'probability') return [`${typeof value === 'number' ? value.toFixed(1) : value}%`, 'Probability'];
                if (name === 'riskScore') return [`${typeof value === 'number' ? value.toFixed(1) : value}`, 'Risk Score'];
                return [value, name];
              }}
            />
            <Legend />
            <Bar dataKey="probability" fill="#f59e0b" name="Probability %" />
            <Bar dataKey="riskScore" fill="#ef4444" name="Risk Score" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Fuel Consumption Timeline */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Fuel Consumption Profile</h3>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={generateFuelConsumptionTimeline()}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="day" 
              label={{ value: 'Mission Day', position: 'insideBottom', offset: -10 }}
            />
            <YAxis 
              label={{ value: 'Fuel Remaining (kg)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              formatter={(value) => [`${typeof value === 'number' ? value.toFixed(0) : value} kg`, 'Fuel Remaining']}
            />
            <Area
              type="monotone"
              dataKey="fuelRemaining"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.3}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  // Helper function to generate fuel consumption timeline
  function generateFuelConsumptionTimeline() {
    const timeline = [];
    const totalDuration = simulationResult?.total_duration_days || 365;
    const totalFuelConsumption = simulationResult?.fuel_consumption_kg || 
      estimateFuelConsumption(trajectory.total_delta_v, spacecraftConfig);
    
    for (let day = 0; day <= totalDuration; day += Math.max(1, Math.floor(totalDuration / 50))) {
      // Simulate fuel consumption with maneuvers
      let fuelUsed = 0;
      
      // Add fuel consumption from maneuvers
      trajectory.maneuvers.forEach((maneuver, index) => {
        const maneuverDay = (index + 1) * (totalDuration / (trajectory.maneuvers.length + 1));
        if (day >= maneuverDay) {
          fuelUsed += (maneuver.delta_v / trajectory.total_delta_v) * totalFuelConsumption;
        }
      });
      
      // Add gradual fuel consumption for station-keeping
      fuelUsed += (day / totalDuration) * (totalFuelConsumption * 0.1);
      
      timeline.push({
        day,
        fuelRemaining: Math.max(spacecraftConfig.fuel_capacity_kg - fuelUsed, 0),
        fuelUsed: Math.min(fuelUsed, spacecraftConfig.fuel_capacity_kg)
      });
    }
    
    return timeline;
  }
};