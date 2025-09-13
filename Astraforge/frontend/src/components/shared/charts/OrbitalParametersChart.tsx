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
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import { TrajectoryPlan, SpacecraftConfig } from '../../../types/mission';

interface OrbitalParametersChartProps {
  trajectory: TrajectoryPlan;
  spacecraftConfig: SpacecraftConfig;
  className?: string;
}

interface OrbitalParameter {
  name: string;
  value: number;
  unit: string;
  description: string;
}

interface TransferEfficiency {
  transferType: string;
  efficiency: number;
  deltaV: number;
  duration: number;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export const OrbitalParametersChart: React.FC<OrbitalParametersChartProps> = ({
  trajectory,
  spacecraftConfig,
  className = '',
}) => {
  // Calculate orbital parameters
  const calculateOrbitalParameters = (): OrbitalParameter[] => {
    // Earth parameters for future calculations
    // const earthMu = 398600.4418; // km³/s² - Earth's gravitational parameter
    // const earthRadius = 6371; // km
    
    // Simplified calculations for demonstration
    const totalDeltaV = trajectory.total_delta_v;
    const specificImpulse = spacecraftConfig.specific_impulse_s;
    const initialMass = spacecraftConfig.mass_kg + spacecraftConfig.fuel_capacity_kg;
    
    // Calculate mass ratio using rocket equation
    const massRatio = Math.exp(totalDeltaV / (specificImpulse * 9.81));
    const finalMass = initialMass / massRatio;
    const fuelUsed = initialMass - finalMass;
    
    // Estimate orbital parameters (for future use)
    // const circularVelocity = Math.sqrt(earthMu / (earthRadius + 400)); // 400km altitude
    // const escapeVelocity = Math.sqrt(2 * earthMu / earthRadius);
    
    return [
      {
        name: 'Total Delta-V',
        value: totalDeltaV,
        unit: 'm/s',
        description: 'Total velocity change required'
      },
      {
        name: 'Fuel Consumption',
        value: fuelUsed,
        unit: 'kg',
        description: 'Estimated fuel consumption'
      },
      {
        name: 'Mass Ratio',
        value: massRatio,
        unit: '',
        description: 'Initial to final mass ratio'
      },
      {
        name: 'Specific Impulse',
        value: specificImpulse,
        unit: 's',
        description: 'Engine efficiency'
      },
      {
        name: 'Thrust-to-Weight',
        value: spacecraftConfig.thrust_n / (initialMass * 9.81),
        unit: '',
        description: 'Thrust to weight ratio'
      },
      {
        name: 'Payload Fraction',
        value: (spacecraftConfig.payload_mass_kg / initialMass) * 100,
        unit: '%',
        description: 'Payload as percentage of total mass'
      }
    ];
  };

  // Generate transfer efficiency comparison
  const generateTransferComparison = (): TransferEfficiency[] => {
    const baseEfficiency = 100 - (trajectory.total_delta_v / 15000) * 100; // Normalized efficiency
    
    return [
      {
        transferType: 'Hohmann Transfer',
        efficiency: Math.max(baseEfficiency, 20),
        deltaV: trajectory.total_delta_v * 0.8,
        duration: 259 // days to Mars
      },
      {
        transferType: 'Bi-elliptic Transfer',
        efficiency: Math.max(baseEfficiency * 0.9, 15),
        deltaV: trajectory.total_delta_v * 0.7,
        duration: 400
      },
      {
        transferType: 'Direct Transfer',
        efficiency: Math.max(baseEfficiency * 1.2, 25),
        deltaV: trajectory.total_delta_v * 1.3,
        duration: 180
      },
      {
        transferType: 'Gravity Assist',
        efficiency: Math.max(baseEfficiency * 1.5, 30),
        deltaV: trajectory.total_delta_v * 0.6,
        duration: 500
      }
    ];
  };

  // Mass breakdown for pie chart
  const massBreakdown = [
    { name: 'Payload', value: spacecraftConfig.payload_mass_kg, color: COLORS[0] },
    { name: 'Fuel', value: spacecraftConfig.fuel_capacity_kg, color: COLORS[1] },
    { name: 'Structure', value: spacecraftConfig.mass_kg - spacecraftConfig.payload_mass_kg, color: COLORS[2] }
  ];

  const orbitalParameters = calculateOrbitalParameters();
  const transferComparison = generateTransferComparison();

  // Radar chart data for spacecraft performance
  const performanceData = [
    {
      parameter: 'Efficiency',
      value: Math.min((spacecraftConfig.specific_impulse_s / 450) * 100, 100),
      fullMark: 100
    },
    {
      parameter: 'Thrust',
      value: Math.min((spacecraftConfig.thrust_n / 1000000) * 100, 100),
      fullMark: 100
    },
    {
      parameter: 'Payload Ratio',
      value: (spacecraftConfig.payload_mass_kg / (spacecraftConfig.mass_kg + spacecraftConfig.fuel_capacity_kg)) * 100,
      fullMark: 100
    },
    {
      parameter: 'Fuel Capacity',
      value: Math.min((spacecraftConfig.fuel_capacity_kg / 500000) * 100, 100),
      fullMark: 100
    },
    {
      parameter: 'Mass Efficiency',
      value: Math.min((spacecraftConfig.payload_mass_kg / spacecraftConfig.mass_kg) * 100, 100),
      fullMark: 100
    }
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Orbital Parameters Bar Chart */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Orbital Parameters</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={orbitalParameters} layout="horizontal">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="name" type="category" width={120} />
            <Tooltip 
              formatter={(value, name) => [
                `${typeof value === 'number' ? value.toFixed(2) : value}`,
                name
              ]}
              labelFormatter={(label) => orbitalParameters.find(p => p.name === label)?.description || label}
            />
            <Legend />
            <Bar dataKey="value" fill="#3b82f6" name="Value" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Transfer Efficiency Comparison */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Transfer Type Comparison</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={transferComparison}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="transferType" />
            <YAxis />
            <Tooltip 
              formatter={(value, name) => {
                if (name === 'efficiency') return [`${value}%`, 'Efficiency'];
                if (name === 'deltaV') return [`${value} m/s`, 'Delta-V'];
                if (name === 'duration') return [`${value} days`, 'Duration'];
                return [value, name];
              }}
            />
            <Legend />
            <Bar dataKey="efficiency" fill="#10b981" name="Efficiency %" />
            <Bar dataKey="deltaV" fill="#f59e0b" name="Delta-V (m/s)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Mass Breakdown Pie Chart */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Mass Breakdown</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={massBreakdown}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {massBreakdown.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => [`${value} kg`, 'Mass']} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Spacecraft Performance Radar */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Spacecraft Performance</h3>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={performanceData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="parameter" />
              <PolarRadiusAxis 
                angle={90} 
                domain={[0, 100]} 
                tick={false}
              />
              <Radar
                name="Performance"
                dataKey="value"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.3}
                strokeWidth={2}
              />
              <Tooltip formatter={(value) => [`${typeof value === 'number' ? value.toFixed(1) : value}%`, 'Score']} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};