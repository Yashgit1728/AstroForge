import React, { useState } from 'react';

const HomePage: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedMission, setGeneratedMission] = useState<any>(null);

  const handleGenerateMission = async () => {
    if (!prompt.trim()) return;
    
    setIsGenerating(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/missions/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });
      
      if (response.ok) {
        const mission = await response.json();
        setGeneratedMission(mission);
      } else {
        console.error('Failed to generate mission');
      }
    } catch (error) {
      console.error('Error generating mission:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-white mb-6">
            🚀 AstraForge
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
            
            <div className="space-y-4">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="w-full p-4 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                rows={4}
                placeholder="Describe your space mission idea... (e.g., 'Send a probe to Mars to study the atmosphere and search for signs of life')"
              />
              
              <button 
                onClick={handleGenerateMission}
                disabled={!prompt.trim() || isGenerating}
                className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white font-medium py-3 px-6 rounded-lg transition-colors"
              >
                {isGenerating ? '🔄 Generating Mission...' : '🚀 Generate Mission'}
              </button>
              
              <p className="text-sm text-gray-400 text-center">
                Our AI will generate a detailed mission specification based on your description
              </p>
            </div>

            {generatedMission && (
              <div className="mt-8 p-6 bg-green-500/10 border border-green-500/30 rounded-lg">
                <h3 className="text-xl font-semibold text-green-300 mb-4">
                  ✅ Mission Generated: {generatedMission.name}
                </h3>
                <p className="text-green-200 mb-4">{generatedMission.description}</p>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="bg-white/5 p-4 rounded-lg">
                    <h4 className="font-semibold text-white mb-2">🚀 Spacecraft</h4>
                    <p className="text-gray-300 text-sm">Type: {generatedMission.spacecraft?.type}</p>
                    <p className="text-gray-300 text-sm">Mass: {generatedMission.spacecraft?.mass_kg} kg</p>
                    <p className="text-gray-300 text-sm">Fuel: {generatedMission.spacecraft?.fuel_capacity_kg} kg</p>
                  </div>
                  
                  <div className="bg-white/5 p-4 rounded-lg">
                    <h4 className="font-semibold text-white mb-2">🛰️ Trajectory</h4>
                    <p className="text-gray-300 text-sm">From: {generatedMission.trajectory?.departure}</p>
                    <p className="text-gray-300 text-sm">To: {generatedMission.trajectory?.destination}</p>
                    <p className="text-gray-300 text-sm">Duration: {generatedMission.trajectory?.duration_days} days</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mt-16">
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
              ⚡
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">AI-Powered Generation</h3>
            <p className="text-gray-300">
              Describe your mission in natural language and let AI generate detailed specifications
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
              🔬
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Physics Simulation</h3>
            <p className="text-gray-300">
              Run realistic physics-based simulations with orbital mechanics and fuel calculations
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              👁️
            </div>
            <h3 className="text-xl font-semibent text-white mb-2">3D Visualization</h3>
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