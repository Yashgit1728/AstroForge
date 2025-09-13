import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGenerateMission, useCreateMission } from '../hooks/useMissions';
import MissionPromptForm from '../components/shared/MissionPromptForm';
import { Mission } from '../types';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [generatedMission, setGeneratedMission] = useState<Mission | null>(null);
  const [error, setError] = useState<string | null>(null);

  const generateMission = useGenerateMission();
  const createMission = useCreateMission();

  const handleGenerateMission = async (prompt: string) => {
    setError(null);
    setGeneratedMission(null);
    
    try {
      const mission = await generateMission.mutateAsync(prompt);
      setGeneratedMission(mission);
    } catch (error) {
      console.error('Error generating mission:', error);
      setError(error instanceof Error ? error.message : 'Failed to generate mission. Please try again.');
    }
  };

  const handleSaveMission = async () => {
    if (!generatedMission) return;
    
    try {
      const savedMission = await createMission.mutateAsync(generatedMission);
      navigate(`/mission/${savedMission.id}`);
    } catch (error) {
      console.error('Error saving mission:', error);
      setError(error instanceof Error ? error.message : 'Failed to save mission. Please try again.');
    }
  };

  const handleTryAgain = () => {
    setError(null);
    setGeneratedMission(null);
  };

  return (
    <div className="min-h-screen bg-transparent">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-white mb-6">
            AstraForge
          </h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            AI-powered space mission simulator. Design, simulate, and optimize space missions 
            with cutting-edge physics and interactive 3D visualization.
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20">
            <h2 className="text-2xl font-semibold text-white mb-6 text-center">
              Describe Your Mission
            </h2>
            
            {/* Error Display */}
            {error && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <svg className="w-5 h-5 text-red-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="flex-1">
                    <h4 className="text-red-300 font-medium">Generation Failed</h4>
                    <p className="text-red-200 text-sm mt-1">{error}</p>
                  </div>
                  <button
                    onClick={handleTryAgain}
                    className="text-red-300 hover:text-red-200 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            )}

            {/* Mission Prompt Form */}
            {!generatedMission && (
              <MissionPromptForm
                onSubmit={handleGenerateMission}
                loading={generateMission.isPending}
              />
            )}

            {/* Generated Mission Display */}
            {generatedMission && (
              <div className="space-y-6">
                <div className="p-6 bg-green-500/10 border border-green-500/30 rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold text-green-300">
                      ✅ Mission Generated: {generatedMission.name}
                    </h3>
                    <button
                      onClick={handleTryAgain}
                      className="text-green-300 hover:text-green-200 transition-colors text-sm"
                    >
                      Generate New
                    </button>
                  </div>
                  
                  <p className="text-green-200 mb-6">{generatedMission.description}</p>
                  
                  {/* Mission Overview Grid */}
                  <div className="grid md:grid-cols-2 gap-4 mb-6">
                    <div className="bg-white/5 p-4 rounded-lg">
                      <h4 className="font-semibold text-white mb-3 flex items-center gap-2">
                        🚀 Spacecraft Configuration
                      </h4>
                      <div className="space-y-2 text-sm">
                        <p className="text-gray-300">Type: <span className="text-white">{generatedMission.spacecraft_config.vehicle_type}</span></p>
                        <p className="text-gray-300">Mass: <span className="text-white">{generatedMission.spacecraft_config.mass_kg.toLocaleString()} kg</span></p>
                        <p className="text-gray-300">Fuel: <span className="text-white">{generatedMission.spacecraft_config.fuel_capacity_kg.toLocaleString()} kg</span></p>
                        <p className="text-gray-300">Payload: <span className="text-white">{generatedMission.spacecraft_config.payload_mass_kg.toLocaleString()} kg</span></p>
                      </div>
                    </div>
                    
                    <div className="bg-white/5 p-4 rounded-lg">
                      <h4 className="font-semibold text-white mb-3 flex items-center gap-2">
                        🛰️ Trajectory Plan
                      </h4>
                      <div className="space-y-2 text-sm">
                        <p className="text-gray-300">From: <span className="text-white">{generatedMission.trajectory.departure_body}</span></p>
                        <p className="text-gray-300">To: <span className="text-white">{generatedMission.trajectory.target_body}</span></p>
                        <p className="text-gray-300">Transfer: <span className="text-white">{generatedMission.trajectory.transfer_type}</span></p>
                        <p className="text-gray-300">Total ΔV: <span className="text-white">{generatedMission.trajectory.total_delta_v.toFixed(2)} km/s</span></p>
                      </div>
                    </div>
                  </div>

                  {/* Mission Objectives */}
                  <div className="bg-white/5 p-4 rounded-lg mb-6">
                    <h4 className="font-semibold text-white mb-3 flex items-center gap-2">
                      🎯 Mission Objectives
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {generatedMission.objectives.map((objective, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-blue-600/20 text-blue-300 rounded-full text-sm"
                        >
                          {objective}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Timeline */}
                  <div className="bg-white/5 p-4 rounded-lg mb-6">
                    <h4 className="font-semibold text-white mb-3 flex items-center gap-2">
                      ⏱️ Mission Timeline
                    </h4>
                    <p className="text-gray-300 text-sm mb-3">
                      Total Duration: <span className="text-white">{generatedMission.timeline.total_duration_days} days</span>
                    </p>
                    <div className="space-y-2">
                      {generatedMission.timeline.phases.slice(0, 3).map((phase, index) => (
                        <div key={index} className="flex justify-between items-center text-sm">
                          <span className="text-gray-300">{phase.name}</span>
                          <span className="text-white">Day {phase.start_day} - {phase.start_day + phase.duration_days}</span>
                        </div>
                      ))}
                      {generatedMission.timeline.phases.length > 3 && (
                        <p className="text-gray-400 text-xs">+{generatedMission.timeline.phases.length - 3} more phases</p>
                      )}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-3">
                    <button
                      onClick={handleSaveMission}
                      disabled={createMission.isPending}
                      className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                      {createMission.isPending ? (
                        <>
                          <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Saving...
                        </>
                      ) : (
                        <>
                          💾 Save & View Details
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => navigate('/gallery')}
                      className="px-6 py-3 bg-white/10 hover:bg-white/20 text-white font-medium rounded-lg transition-colors border border-white/20"
                    >
                      Browse Gallery
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mt-16">
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">AI-Powered Generation</h3>
            <p className="text-gray-300">
              Describe your mission in natural language and let AI generate detailed specifications
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Physics Simulation</h3>
            <p className="text-gray-300">
              Run realistic physics-based simulations with orbital mechanics and fuel calculations
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">3D Visualization</h3>
            <p className="text-gray-300">
              Explore your missions in interactive 3D with spacecraft, trajectories, and celestial bodies
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;