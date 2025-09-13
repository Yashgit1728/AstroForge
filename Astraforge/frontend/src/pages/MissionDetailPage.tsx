import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMission, useUpdateMission, useDeleteMission } from '../hooks/useMissions';
import { Mission } from '../types';
import ErrorBoundary from '../components/shared/ErrorBoundary';

type TabType = 'specs' | 'charts' | '3d';

const MissionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabType>('specs');
  const [isEditing, setIsEditing] = useState(false);
  const [editedMission, setEditedMission] = useState<Mission | null>(null);

  const { data: mission, isLoading, error } = useMission(id!);
  const updateMission = useUpdateMission();
  const deleteMission = useDeleteMission();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-transparent flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-white">Loading mission details...</p>
        </div>
      </div>
    );
  }

  if (error || !mission) {
    return (
      <div className="min-h-screen bg-transparent flex items-center justify-center">
        <div className="text-center max-w-md mx-4">
          <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-white mb-4">Mission Not Found</h2>
          <p className="text-gray-300 mb-6">
            The mission you're looking for doesn't exist or has been deleted.
          </p>
          <button
            onClick={() => navigate('/gallery')}
            className="bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            Browse Gallery
          </button>
        </div>
      </div>
    );
  }

  const handleEdit = () => {
    setEditedMission({ ...mission });
    setIsEditing(true);
  };

  const handleSave = async () => {
    if (!editedMission) return;
    
    try {
      await updateMission.mutateAsync({ id: mission.id, data: editedMission });
      setIsEditing(false);
      setEditedMission(null);
    } catch (error) {
      console.error('Failed to update mission:', error);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedMission(null);
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this mission? This action cannot be undone.')) {
      try {
        await deleteMission.mutateAsync(mission.id);
        navigate('/gallery');
      } catch (error) {
        console.error('Failed to delete mission:', error);
      }
    }
  };

  const currentMission = isEditing ? editedMission! : mission;

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-transparent">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <div>
                <button
                  onClick={() => navigate('/gallery')}
                  className="text-gray-400 hover:text-white transition-colors mb-2 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Back to Gallery
                </button>
                {isEditing ? (
                  <input
                    type="text"
                    value={currentMission.name}
                    onChange={(e) => setEditedMission({ ...currentMission, name: e.target.value })}
                    className="text-4xl font-bold text-white bg-transparent border-b border-white/30 focus:border-purple-500 focus:outline-none"
                  />
                ) : (
                  <h1 className="text-4xl font-bold text-white">{currentMission.name}</h1>
                )}
              </div>
              
              <div className="flex gap-3">
                {isEditing ? (
                  <>
                    <button
                      onClick={handleCancel}
                      className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSave}
                      disabled={updateMission.isPending}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg transition-colors flex items-center gap-2"
                    >
                      {updateMission.isPending && (
                        <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      )}
                      Save Changes
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={handleEdit}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Edit
                    </button>
                    <button
                      onClick={handleDelete}
                      disabled={deleteMission.isPending}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white rounded-lg transition-colors flex items-center gap-2"
                    >
                      {deleteMission.isPending && (
                        <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      )}
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      Delete
                    </button>
                  </>
                )}
              </div>
            </div>
            
            {isEditing ? (
              <textarea
                value={currentMission.description}
                onChange={(e) => setEditedMission({ ...currentMission, description: e.target.value })}
                className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-gray-300 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                rows={2}
              />
            ) : (
              <p className="text-gray-300 text-lg">{currentMission.description}</p>
            )}
          </div>

          {/* Tab Navigation */}
          <div className="mb-8">
            <div className="border-b border-white/20">
              <nav className="flex space-x-8">
                {[
                  { id: 'specs', label: 'Specifications', icon: '📋' },
                  { id: 'charts', label: 'Charts & Analytics', icon: '📊' },
                  { id: '3d', label: '3D Visualization', icon: '🌌' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as TabType)}
                    className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${
                      activeTab === tab.id
                        ? 'border-purple-500 text-purple-400'
                        : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                    }`}
                  >
                    <span>{tab.icon}</span>
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>
          </div>

          <div className="grid lg:grid-cols-4 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-3">
              {activeTab === 'specs' && (
                <MissionSpecifications mission={currentMission} isEditing={isEditing} onUpdate={setEditedMission} />
              )}
              {activeTab === 'charts' && (
                <ChartsAndAnalytics mission={currentMission} />
              )}
              {activeTab === '3d' && (
                <ThreeDVisualization mission={currentMission} />
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              <MissionActions mission={currentMission} />
              <PerformanceMetrics mission={currentMission} />
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
};

// Mission Specifications Component
const MissionSpecifications: React.FC<{
  mission: Mission;
  isEditing: boolean;
  onUpdate?: (mission: Mission) => void;
}> = ({ mission, isEditing, onUpdate }) => {
  const updateField = (field: keyof Mission, value: any) => {
    if (onUpdate) {
      onUpdate({ ...mission, [field]: value });
    }
  };

  return (
    <div className="space-y-6">
      {/* Mission Objectives */}
      <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
        <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
          🎯 Mission Objectives
        </h2>
        {isEditing ? (
          <div className="space-y-3">
            {mission.objectives.map((objective, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="text"
                  value={objective}
                  onChange={(e) => {
                    const newObjectives = [...mission.objectives];
                    newObjectives[index] = e.target.value;
                    updateField('objectives', newObjectives);
                  }}
                  className="flex-1 p-2 bg-white/10 border border-white/20 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <button
                  onClick={() => {
                    const newObjectives = mission.objectives.filter((_, i) => i !== index);
                    updateField('objectives', newObjectives);
                  }}
                  className="text-red-400 hover:text-red-300 p-2"
                >
                  ✕
                </button>
              </div>
            ))}
            <button
              onClick={() => updateField('objectives', [...mission.objectives, 'New objective'])}
              className="text-purple-400 hover:text-purple-300 text-sm"
            >
              + Add Objective
            </button>
          </div>
        ) : (
          <div className="grid gap-3">
            {mission.objectives.map((objective, index) => (
              <div key={index} className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
                <div className="w-6 h-6 bg-purple-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  {index + 1}
                </div>
                <span className="text-gray-300">{objective}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Spacecraft Configuration */}
      <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
        <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
          🚀 Spacecraft Configuration
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Vehicle Type</label>
              {isEditing ? (
                <input
                  type="text"
                  value={mission.spacecraft_config.vehicle_type}
                  onChange={(e) => updateField('spacecraft_config', { ...mission.spacecraft_config, vehicle_type: e.target.value })}
                  className="w-full p-2 bg-white/10 border border-white/20 rounded text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              ) : (
                <p className="text-white">{mission.spacecraft_config.vehicle_type}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Mass (kg)</label>
              {isEditing ? (
                <input
                  type="number"
                  value={mission.spacecraft_config.mass_kg}
                  onChange={(e) => updateField('spacecraft_config', { ...mission.spacecraft_config, mass_kg: Number(e.target.value) })}
                  className="w-full p-2 bg-white/10 border border-white/20 rounded text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              ) : (
                <p className="text-white">{mission.spacecraft_config.mass_kg.toLocaleString()} kg</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Fuel Capacity (kg)</label>
              {isEditing ? (
                <input
                  type="number"
                  value={mission.spacecraft_config.fuel_capacity_kg}
                  onChange={(e) => updateField('spacecraft_config', { ...mission.spacecraft_config, fuel_capacity_kg: Number(e.target.value) })}
                  className="w-full p-2 bg-white/10 border border-white/20 rounded text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              ) : (
                <p className="text-white">{mission.spacecraft_config.fuel_capacity_kg.toLocaleString()} kg</p>
              )}
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Thrust (N)</label>
              {isEditing ? (
                <input
                  type="number"
                  value={mission.spacecraft_config.thrust_n}
                  onChange={(e) => updateField('spacecraft_config', { ...mission.spacecraft_config, thrust_n: Number(e.target.value) })}
                  className="w-full p-2 bg-white/10 border border-white/20 rounded text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              ) : (
                <p className="text-white">{mission.spacecraft_config.thrust_n.toLocaleString()} N</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Specific Impulse (s)</label>
              {isEditing ? (
                <input
                  type="number"
                  value={mission.spacecraft_config.specific_impulse_s}
                  onChange={(e) => updateField('spacecraft_config', { ...mission.spacecraft_config, specific_impulse_s: Number(e.target.value) })}
                  className="w-full p-2 bg-white/10 border border-white/20 rounded text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              ) : (
                <p className="text-white">{mission.spacecraft_config.specific_impulse_s} s</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Payload Mass (kg)</label>
              {isEditing ? (
                <input
                  type="number"
                  value={mission.spacecraft_config.payload_mass_kg}
                  onChange={(e) => updateField('spacecraft_config', { ...mission.spacecraft_config, payload_mass_kg: Number(e.target.value) })}
                  className="w-full p-2 bg-white/10 border border-white/20 rounded text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              ) : (
                <p className="text-white">{mission.spacecraft_config.payload_mass_kg.toLocaleString()} kg</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Trajectory Plan */}
      <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
        <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
          🛰️ Trajectory Plan
        </h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Departure Body</label>
              <p className="text-white">{mission.trajectory.departure_body}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Target Body</label>
              <p className="text-white">{mission.trajectory.target_body}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Transfer Type</label>
              <p className="text-white">{mission.trajectory.transfer_type}</p>
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Total ΔV</label>
              <p className="text-white text-2xl font-bold">{mission.trajectory.total_delta_v.toFixed(2)} km/s</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Launch Window</label>
              <p className="text-white text-sm">
                {new Date(mission.trajectory.launch_window.start).toLocaleDateString()} - {new Date(mission.trajectory.launch_window.end).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        {/* Maneuvers */}
        {mission.trajectory.maneuvers.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-medium text-white mb-3">Planned Maneuvers</h3>
            <div className="space-y-2">
              {mission.trajectory.maneuvers.map((maneuver) => (
                <div key={maneuver.id} className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                  <div>
                    <span className="text-white font-medium">{maneuver.name}</span>
                    <p className="text-gray-400 text-sm">{maneuver.description}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-white">{maneuver.delta_v.toFixed(2)} km/s</p>
                    <p className="text-gray-400 text-sm">{new Date(maneuver.timestamp).toLocaleDateString()}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Mission Timeline */}
      <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
        <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
          ⏱️ Mission Timeline
        </h2>
        <div className="mb-4">
          <p className="text-gray-300">
            Total Duration: <span className="text-white font-medium">{mission.timeline.total_duration_days} days</span>
          </p>
        </div>
        <div className="space-y-3">
          {mission.timeline.phases.map((phase, index) => (
            <div key={index} className="flex items-center gap-4 p-4 bg-white/5 rounded-lg">
              <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                {index + 1}
              </div>
              <div className="flex-1">
                <h4 className="text-white font-medium">{phase.name}</h4>
                <p className="text-gray-400 text-sm">{phase.description}</p>
              </div>
              <div className="text-right">
                <p className="text-white text-sm">Day {phase.start_day} - {phase.start_day + phase.duration_days}</p>
                <p className="text-gray-400 text-xs">{phase.duration_days} days</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Charts and Analytics Component
const ChartsAndAnalytics: React.FC<{ mission: Mission }> = ({ mission: _mission }) => {
  return (
    <div className="space-y-6">
      <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
        <h2 className="text-2xl font-semibold text-white mb-4">Mission Analytics</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="h-64 bg-white/5 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <svg className="w-12 h-12 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <p className="text-gray-400">Trajectory Chart</p>
              <p className="text-gray-500 text-sm">Coming in Task 9.1</p>
            </div>
          </div>
          <div className="h-64 bg-white/5 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <svg className="w-12 h-12 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              <p className="text-gray-400">Performance Metrics</p>
              <p className="text-gray-500 text-sm">Coming in Task 9.2</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// 3D Visualization Component
const ThreeDVisualization: React.FC<{ mission: Mission }> = ({ mission: _mission }) => {
  return (
    <div className="space-y-6">
      <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
        <h2 className="text-2xl font-semibold text-white mb-4">3D Mission Visualization</h2>
        <div className="h-96 bg-white/5 rounded-lg flex items-center justify-center">
          <div className="text-center">
            <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <p className="text-gray-400 text-lg">3D Scene Viewer</p>
            <p className="text-gray-500">Interactive 3D visualization coming in Task 10</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Mission Actions Component
const MissionActions: React.FC<{ mission: Mission }> = ({ mission: _mission }) => {
  return (
    <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
      <h3 className="text-xl font-semibold text-white mb-4">Mission Actions</h3>
      <div className="space-y-3">
        <button className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h8m-9 5a9 9 0 1118 0 9 9 0 01-18 0z" />
          </svg>
          Run Simulation
        </button>
        <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Optimize Mission
        </button>
        <button className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          Clone Mission
        </button>
        <button className="w-full bg-gray-600 hover:bg-gray-700 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Export Data
        </button>
      </div>
    </div>
  );
};

// Performance Metrics Component
const PerformanceMetrics: React.FC<{ mission: Mission }> = ({ mission }) => {
  return (
    <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
      <h3 className="text-xl font-semibold text-white mb-4">Performance Metrics</h3>
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-gray-300">Total ΔV</span>
          <span className="text-white font-medium">{mission.trajectory.total_delta_v.toFixed(2)} km/s</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-300">Duration</span>
          <span className="text-white font-medium">{mission.timeline.total_duration_days} days</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-300">Spacecraft Mass</span>
          <span className="text-white font-medium">{(mission.spacecraft_config.mass_kg / 1000).toFixed(1)} tons</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-300">Fuel Capacity</span>
          <span className="text-white font-medium">{(mission.spacecraft_config.fuel_capacity_kg / 1000).toFixed(1)} tons</span>
        </div>
        <div className="pt-3 border-t border-white/20">
          <div className="flex justify-between items-center">
            <span className="text-gray-300">Success Probability</span>
            <span className="text-green-400 font-medium">Pending Simulation</span>
          </div>
          <div className="flex justify-between items-center mt-2">
            <span className="text-gray-300">Cost Estimate</span>
            <span className="text-yellow-400 font-medium">Pending Analysis</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MissionDetailPage;