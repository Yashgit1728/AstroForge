import React, { useState } from 'react';
import VehicleCard from './VehicleCard';

interface VehiclePreset {
  id: string;
  name: string;
  description: string;
  vehicleType: string;
  massKg: number;
  thrustN: number;
  specificImpulseS: number;
  fuelCapacityKg: number;
  payloadMassKg: number;
  powerW: number;
}

const VehicleManagement: React.FC = () => {
  const [selectedVehicle, setSelectedVehicle] = useState<VehiclePreset | null>(null);
  const [filterType, setFilterType] = useState<string>('all');
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Mock vehicle presets
  const vehiclePresets: VehiclePreset[] = [
    {
      id: '1',
      name: 'CubeSat 3U',
      description: 'Standard 3U CubeSat configuration for small payloads and technology demonstrations',
      vehicleType: 'cubesat',
      massKg: 4.0,
      thrustN: 0.1,
      specificImpulseS: 220,
      fuelCapacityKg: 0.5,
      payloadMassKg: 1.5,
      powerW: 20
    },
    {
      id: '2',
      name: 'CubeSat 6U',
      description: 'Larger 6U CubeSat with enhanced capabilities for Earth observation',
      vehicleType: 'cubesat',
      massKg: 8.0,
      thrustN: 0.2,
      specificImpulseS: 230,
      fuelCapacityKg: 1.0,
      payloadMassKg: 3.0,
      powerW: 40
    },
    {
      id: '3',
      name: 'SmallSat Standard',
      description: 'Standard small satellite for commercial and scientific missions',
      vehicleType: 'small_sat',
      massKg: 150.0,
      thrustN: 5.0,
      specificImpulseS: 280,
      fuelCapacityKg: 30.0,
      payloadMassKg: 50.0,
      powerW: 500
    },
    {
      id: '4',
      name: 'Medium Satellite',
      description: 'Medium-class satellite for telecommunications and Earth observation',
      vehicleType: 'medium_sat',
      massKg: 1500.0,
      thrustN: 50.0,
      specificImpulseS: 320,
      fuelCapacityKg: 400.0,
      payloadMassKg: 600.0,
      powerW: 3000
    },
    {
      id: '5',
      name: 'Large Geostationary Satellite',
      description: 'Large satellite for geostationary orbit telecommunications',
      vehicleType: 'large_sat',
      massKg: 6000.0,
      thrustN: 400.0,
      specificImpulseS: 350,
      fuelCapacityKg: 2000.0,
      payloadMassKg: 2500.0,
      powerW: 15000
    },
    {
      id: '6',
      name: 'Mars Reconnaissance Probe',
      description: 'Interplanetary probe designed for Mars reconnaissance missions',
      vehicleType: 'probe',
      massKg: 2180.0,
      thrustN: 90.0,
      specificImpulseS: 330,
      fuelCapacityKg: 800.0,
      payloadMassKg: 400.0,
      powerW: 2000
    },
    {
      id: '7',
      name: 'Lunar Lander',
      description: 'Lunar surface lander with descent and landing capabilities',
      vehicleType: 'lander',
      massKg: 3500.0,
      thrustN: 15000.0,
      specificImpulseS: 311,
      fuelCapacityKg: 2200.0,
      payloadMassKg: 800.0,
      powerW: 1500
    },
    {
      id: '8',
      name: 'Mars Rover',
      description: 'Mars surface rover for exploration and sample collection',
      vehicleType: 'rover',
      massKg: 899.0,
      thrustN: 0.0,
      specificImpulseS: 0.0,
      fuelCapacityKg: 0.0,
      payloadMassKg: 65.0,
      powerW: 110
    },
    {
      id: '9',
      name: 'Crew Dragon Capsule',
      description: 'Crewed spacecraft for low Earth orbit and ISS missions',
      vehicleType: 'crewed',
      massKg: 12055.0,
      thrustN: 7400.0,
      specificImpulseS: 300,
      fuelCapacityKg: 1388.0,
      payloadMassKg: 6000.0,
      powerW: 4000
    },
    {
      id: '10',
      name: 'Deep Space Probe',
      description: 'Long-duration probe for outer solar system exploration',
      vehicleType: 'probe',
      massKg: 5712.0,
      thrustN: 890.0,
      specificImpulseS: 325,
      fuelCapacityKg: 3132.0,
      payloadMassKg: 1200.0,
      powerW: 470
    }
  ];

  const vehicleTypes = [
    { value: 'all', label: 'All Types' },
    { value: 'cubesat', label: 'CubeSat' },
    { value: 'small_sat', label: 'Small Satellite' },
    { value: 'medium_sat', label: 'Medium Satellite' },
    { value: 'large_sat', label: 'Large Satellite' },
    { value: 'probe', label: 'Probe' },
    { value: 'lander', label: 'Lander' },
    { value: 'rover', label: 'Rover' },
    { value: 'crewed', label: 'Crewed' }
  ];

  const filteredVehicles = filterType === 'all' 
    ? vehiclePresets 
    : vehiclePresets.filter(v => v.vehicleType === filterType);

  const getTypeStats = () => {
    const stats: { [key: string]: number } = {};
    vehiclePresets.forEach(vehicle => {
      stats[vehicle.vehicleType] = (stats[vehicle.vehicleType] || 0) + 1;
    });
    return stats;
  };

  const typeStats = getTypeStats();

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 relative z-10">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-3xl font-bold text-white mb-2">Vehicle Management</h2>
            <p className="text-space-300">Manage and configure spacecraft for your missions</p>
          </div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            + Create Vehicle
          </button>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
          {Object.entries(typeStats).map(([type, count]) => (
            <div key={type} className="bg-space-800/50 backdrop-blur-sm rounded-lg p-4 border border-space-600">
              <div className="text-2xl font-bold text-white">{count}</div>
              <div className="text-space-300 text-sm capitalize">{type.replace('_', ' ')}</div>
            </div>
          ))}
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <div className="flex items-center space-x-2">
            <label className="text-space-300 text-sm font-medium">Filter by type:</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-space-800 border border-space-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-400"
            >
              {vehicleTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
          <div className="text-space-400 text-sm">
            Showing {filteredVehicles.length} of {vehiclePresets.length} vehicles
          </div>
        </div>
      </div>

      {/* Vehicle Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {filteredVehicles.map(vehicle => (
          <VehicleCard
            key={vehicle.id}
            vehicle={vehicle}
            onSelect={setSelectedVehicle}
            isSelected={selectedVehicle?.id === vehicle.id}
          />
        ))}
      </div>

      {/* Selected Vehicle Details */}
      {selectedVehicle && (
        <div className="bg-space-800/50 backdrop-blur-sm rounded-lg p-6 border border-space-600">
          <h3 className="text-xl font-semibold text-white mb-4">Vehicle Details: {selectedVehicle.name}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="space-y-4">
              <h4 className="text-lg font-medium text-white">Physical Properties</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-space-300">Total Mass:</span>
                  <span className="text-white">{selectedVehicle.massKg.toLocaleString()} kg</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-space-300">Fuel Capacity:</span>
                  <span className="text-white">{selectedVehicle.fuelCapacityKg.toLocaleString()} kg</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-space-300">Payload Mass:</span>
                  <span className="text-white">{selectedVehicle.payloadMassKg.toLocaleString()} kg</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-space-300">Dry Mass:</span>
                  <span className="text-white">
                    {(selectedVehicle.massKg - selectedVehicle.fuelCapacityKg).toLocaleString()} kg
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="text-lg font-medium text-white">Propulsion</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-space-300">Thrust:</span>
                  <span className="text-white">{selectedVehicle.thrustN.toLocaleString()} N</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-space-300">Specific Impulse:</span>
                  <span className="text-white">{selectedVehicle.specificImpulseS} s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-space-300">Mass Ratio:</span>
                  <span className="text-white">
                    {(selectedVehicle.massKg / (selectedVehicle.massKg - selectedVehicle.fuelCapacityKg)).toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-space-300">Max ΔV:</span>
                  <span className="text-white">
                    {selectedVehicle.fuelCapacityKg > 0 
                      ? Math.round(selectedVehicle.specificImpulseS * 9.81 * Math.log(selectedVehicle.massKg / (selectedVehicle.massKg - selectedVehicle.fuelCapacityKg)))
                      : 0
                    } m/s
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="text-lg font-medium text-white">Systems</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-space-300">Power:</span>
                  <span className="text-white">{selectedVehicle.powerW.toLocaleString()} W</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-space-300">Type:</span>
                  <span className="text-white capitalize">{selectedVehicle.vehicleType.replace('_', ' ')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-space-300">T/W Ratio:</span>
                  <span className="text-white">
                    {(selectedVehicle.thrustN / (selectedVehicle.massKg * 9.81)).toFixed(3)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 flex space-x-4">
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
              Edit Vehicle
            </button>
            <button className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors">
              Use in Mission
            </button>
            <button className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors">
              Delete Vehicle
            </button>
          </div>
        </div>
      )}

      {/* Create Vehicle Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-space-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-white">Create New Vehicle</h3>
              <button
                onClick={() => setShowCreateForm(false)}
                className="text-space-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            <div className="text-space-300 text-center py-8">
              Vehicle creation form would go here...
              <br />
              <button
                onClick={() => setShowCreateForm(false)}
                className="mt-4 bg-space-600 hover:bg-space-500 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VehicleManagement;