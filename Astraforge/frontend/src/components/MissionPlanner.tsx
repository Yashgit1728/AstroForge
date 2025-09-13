import React, { useState } from 'react';
import VehicleCard from './VehicleCard';
import SolarSystemVisualization from './SolarSystemVisualization';

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

interface Mission {
  name: string;
  description: string;
  objectives: string[];
  departureBody: string;
  targetBody: string;
  transferType: string;
  selectedVehicle?: VehiclePreset;
}

const MissionPlanner: React.FC = () => {
  const [selectedVehicle, setSelectedVehicle] = useState<VehiclePreset | null>(null);
  const [mission, setMission] = useState<Mission>({
    name: '',
    description: '',
    objectives: [''],
    departureBody: 'earth',
    targetBody: 'mars',
    transferType: 'hohmann'
  });
  
  const [savedMissions, setSavedMissions] = useState<Mission[]>([]);
  const [showSaveSuccess, setShowSaveSuccess] = useState(false);

  // Mock vehicle presets based on our backend data
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
      id: '3',
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
      id: '4',
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
      id: '5',
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
      id: '6',
      name: 'Crew Dragon Capsule',
      description: 'Crewed spacecraft for low Earth orbit and ISS missions',
      vehicleType: 'crewed',
      massKg: 12055.0,
      thrustN: 7400.0,
      specificImpulseS: 300,
      fuelCapacityKg: 1388.0,
      payloadMassKg: 6000.0,
      powerW: 4000
    }
  ];

  const celestialBodies = [
    { value: 'earth', label: 'Earth', emoji: '🌍' },
    { value: 'moon', label: 'Moon', emoji: '🌙' },
    { value: 'mars', label: 'Mars', emoji: '🔴' },
    { value: 'venus', label: 'Venus', emoji: '🟡' },
    { value: 'jupiter', label: 'Jupiter', emoji: '🟤' },
    { value: 'saturn', label: 'Saturn', emoji: '🪐' }
  ];

  const transferTypes = [
    { value: 'hohmann', label: 'Hohmann Transfer' },
    { value: 'bi_elliptic', label: 'Bi-elliptic Transfer' },
    { value: 'direct', label: 'Direct Transfer' },
    { value: 'gravity_assist', label: 'Gravity Assist' }
  ];

  const calculateDeltaV = () => {
    if (!selectedVehicle) return 0;
    
    // Simplified delta-v calculation based on destination
    const deltaVMap: { [key: string]: number } = {
      'earth-moon': 3200,
      'earth-mars': 9500,
      'earth-venus': 7300,
      'earth-jupiter': 12800,
      'earth-saturn': 15600
    };
    
    const key = `${mission.departureBody}-${mission.targetBody}`;
    return deltaVMap[key] || 5000;
  };

  const calculateMissionFeasibility = () => {
    if (!selectedVehicle) return { feasible: false, issues: ['No vehicle selected'] };
    
    const requiredDeltaV = calculateDeltaV();
    const availableDeltaV = selectedVehicle.specificImpulseS * 9.81 * 
      Math.log(selectedVehicle.massKg / (selectedVehicle.massKg - selectedVehicle.fuelCapacityKg));
    
    const issues: string[] = [];
    
    if (availableDeltaV < requiredDeltaV) {
      issues.push(`Insufficient delta-v: need ${requiredDeltaV.toFixed(0)} m/s, have ${availableDeltaV.toFixed(0)} m/s`);
    }
    
    if (selectedVehicle.vehicleType === 'rover' && mission.targetBody !== 'mars' && mission.targetBody !== 'moon') {
      issues.push('Rovers are only suitable for Mars or Moon missions');
    }
    
    return { feasible: issues.length === 0, issues };
  };

  const addObjective = () => {
    setMission(prev => ({
      ...prev,
      objectives: [...prev.objectives, '']
    }));
  };

  const updateObjective = (index: number, value: string) => {
    setMission(prev => ({
      ...prev,
      objectives: prev.objectives.map((obj, i) => i === index ? value : obj)
    }));
  };

  const removeObjective = (index: number) => {
    setMission(prev => ({
      ...prev,
      objectives: prev.objectives.filter((_, i) => i !== index)
    }));
  };

  const feasibility = calculateMissionFeasibility();

  const saveMission = () => {
    if (!mission.name.trim()) {
      alert('Please enter a mission name');
      return;
    }
    
    const missionToSave = {
      ...mission,
      selectedVehicle,
      id: Date.now().toString(),
      createdAt: new Date().toISOString()
    };
    
    setSavedMissions(prev => [...prev, missionToSave]);
    setShowSaveSuccess(true);
    setTimeout(() => setShowSaveSuccess(false), 3000);
  };

  const runSimulation = () => {
    if (!feasibility.feasible) {
      alert('Cannot run simulation: Mission has feasibility issues');
      return;
    }
    
    if (!selectedVehicle) {
      alert('Please select a vehicle before running simulation');
      return;
    }
    
    // Simulate running simulation
    alert(`Running simulation for ${mission.name || 'Unnamed Mission'} with ${selectedVehicle.name}...`);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Mission Planner</h2>
        <p className="text-space-300">Design and analyze your space mission</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Mission Configuration */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Mission Info */}
          <div className="bg-space-800/50 backdrop-blur-sm rounded-lg p-6 border border-space-600">
            <h3 className="text-xl font-semibold text-white mb-4">Mission Details</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-space-300 text-sm font-medium mb-2">
                  Mission Name
                </label>
                <input
                  type="text"
                  value={mission.name}
                  onChange={(e) => setMission(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full bg-space-900 border border-space-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-400"
                  placeholder="Enter mission name..."
                />
              </div>
              
              <div>
                <label className="block text-space-300 text-sm font-medium mb-2">
                  Description
                </label>
                <textarea
                  value={mission.description}
                  onChange={(e) => setMission(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full bg-space-900 border border-space-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-400"
                  rows={3}
                  placeholder="Describe your mission..."
                />
              </div>

              <div>
                <label className="block text-space-300 text-sm font-medium mb-2">
                  Mission Objectives
                </label>
                {mission.objectives.map((objective, index) => (
                  <div key={index} className="flex items-center space-x-2 mb-2">
                    <input
                      type="text"
                      value={objective}
                      onChange={(e) => updateObjective(index, e.target.value)}
                      className="flex-1 bg-space-900 border border-space-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-400"
                      placeholder={`Objective ${index + 1}...`}
                    />
                    {mission.objectives.length > 1 && (
                      <button
                        onClick={() => removeObjective(index)}
                        className="text-red-400 hover:text-red-300 p-2"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
                <button
                  onClick={addObjective}
                  className="text-blue-400 hover:text-blue-300 text-sm font-medium"
                >
                  + Add Objective
                </button>
              </div>
            </div>
          </div>

          {/* Trajectory Configuration */}
          <div className="bg-space-800/50 backdrop-blur-sm rounded-lg p-6 border border-space-600">
            <h3 className="text-xl font-semibold text-white mb-4">Trajectory</h3>
            
            {/* 3D Solar System Visualization */}
            <div className="mb-6">
              <SolarSystemVisualization
                departureBody={mission.departureBody}
                targetBody={mission.targetBody}
                showTrajectory={true}
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-space-300 text-sm font-medium mb-2">
                  Departure Body
                </label>
                <select
                  value={mission.departureBody}
                  onChange={(e) => setMission(prev => ({ ...prev, departureBody: e.target.value }))}
                  className="w-full bg-space-900 border border-space-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-400"
                >
                  {celestialBodies.map(body => (
                    <option key={body.value} value={body.value}>
                      {body.emoji} {body.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-space-300 text-sm font-medium mb-2">
                  Target Body
                </label>
                <select
                  value={mission.targetBody}
                  onChange={(e) => setMission(prev => ({ ...prev, targetBody: e.target.value }))}
                  className="w-full bg-space-900 border border-space-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-400"
                >
                  {celestialBodies.filter(body => body.value !== mission.departureBody).map(body => (
                    <option key={body.value} value={body.value}>
                      {body.emoji} {body.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-space-300 text-sm font-medium mb-2">
                  Transfer Type
                </label>
                <select
                  value={mission.transferType}
                  onChange={(e) => setMission(prev => ({ ...prev, transferType: e.target.value }))}
                  className="w-full bg-space-900 border border-space-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-400"
                >
                  {transferTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Vehicle Selection */}
          <div className="bg-space-800/50 backdrop-blur-sm rounded-lg p-6 border border-space-600">
            <h3 className="text-xl font-semibold text-white mb-4">Select Vehicle</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {vehiclePresets.map(vehicle => (
                <VehicleCard
                  key={vehicle.id}
                  vehicle={vehicle}
                  onSelect={setSelectedVehicle}
                  isSelected={selectedVehicle?.id === vehicle.id}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Mission Analysis */}
        <div className="space-y-6">
          {/* Mission Summary */}
          <div className="bg-space-800/50 backdrop-blur-sm rounded-lg p-6 border border-space-600">
            <h3 className="text-xl font-semibold text-white mb-4">Mission Summary</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-space-300">Route:</span>
                <span className="text-white">
                  {celestialBodies.find(b => b.value === mission.departureBody)?.emoji} → {' '}
                  {celestialBodies.find(b => b.value === mission.targetBody)?.emoji}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-space-300">Transfer:</span>
                <span className="text-white capitalize">
                  {mission.transferType.replace('_', ' ')}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-space-300">Required ΔV:</span>
                <span className="text-white">{calculateDeltaV().toLocaleString()} m/s</span>
              </div>
              {selectedVehicle && (
                <div className="flex justify-between">
                  <span className="text-space-300">Vehicle:</span>
                  <span className="text-white">{selectedVehicle.name}</span>
                </div>
              )}
            </div>
          </div>

          {/* Feasibility Analysis */}
          <div className="bg-space-800/50 backdrop-blur-sm rounded-lg p-6 border border-space-600">
            <h3 className="text-xl font-semibold text-white mb-4">Feasibility Analysis</h3>
            <div className={`p-4 rounded-lg ${feasibility.feasible ? 'bg-green-900/30 border border-green-600' : 'bg-red-900/30 border border-red-600'}`}>
              <div className="flex items-center space-x-2 mb-2">
                <span className={`text-2xl ${feasibility.feasible ? 'text-green-400' : 'text-red-400'}`}>
                  {feasibility.feasible ? '✅' : '❌'}
                </span>
                <span className={`font-semibold ${feasibility.feasible ? 'text-green-400' : 'text-red-400'}`}>
                  {feasibility.feasible ? 'Mission Feasible' : 'Mission Issues'}
                </span>
              </div>
              {feasibility.issues.length > 0 && (
                <ul className="text-sm text-red-300 space-y-1">
                  {feasibility.issues.map((issue, index) => (
                    <li key={index}>• {issue}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={runSimulation}
              disabled={!feasibility.feasible}
              className={`w-full py-3 px-4 rounded-lg font-semibold transition-colors ${
                feasibility.feasible
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-space-700 text-space-400 cursor-not-allowed'
              }`}
            >
              🚀 Run Simulation
            </button>
            <button 
              onClick={saveMission}
              className="w-full py-3 px-4 rounded-lg font-semibold bg-green-600 hover:bg-green-700 text-white transition-colors"
            >
              💾 Save Mission
            </button>
          </div>

          {/* Save Success Message */}
          {showSaveSuccess && (
            <div className="bg-green-600/20 border border-green-600 rounded-lg p-4 mt-4">
              <div className="flex items-center space-x-2">
                <span className="text-green-400 text-xl">✅</span>
                <span className="text-green-400 font-medium">Mission saved successfully!</span>
              </div>
            </div>
          )}

          {/* Saved Missions */}
          {savedMissions.length > 0 && (
            <div className="bg-space-800/50 backdrop-blur-sm rounded-lg p-6 border border-space-600 mt-6">
              <h3 className="text-lg font-semibold text-white mb-4">Saved Missions ({savedMissions.length})</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {savedMissions.map((savedMission, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-space-900/50 rounded">
                    <div>
                      <div className="text-white font-medium text-sm">{savedMission.name}</div>
                      <div className="text-space-400 text-xs">
                        {savedMission.departureBody} → {savedMission.targetBody}
                      </div>
                    </div>
                    <button 
                      onClick={() => setMission(savedMission)}
                      className="text-blue-400 hover:text-blue-300 text-sm"
                    >
                      Load
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MissionPlanner;