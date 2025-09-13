import React, { useEffect, useState } from 'react';

function App() {
  const [backendStatus, setBackendStatus] = useState<'loading' | 'connected' | 'error'>('loading');

  useEffect(() => {
    // Test backend connection
    fetch('http://localhost:8000/health')
      .then(response => response.json())
      .then(data => {
        if (data.status === 'healthy') {
          setBackendStatus('connected');
        } else {
          setBackendStatus('error');
        }
      })
      .catch(() => {
        setBackendStatus('error');
      });
  }, []);
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-white mb-6">
            🚀 AstraForge
          </h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto mb-8">
            AI-powered space mission simulator. Design, simulate, and optimize space missions 
            with cutting-edge physics and interactive 3D visualization.
          </p>
          
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20 max-w-2xl mx-auto">
            <h2 className="text-2xl font-semibold text-white mb-6">
              Describe Your Mission
            </h2>
            
            <div className="space-y-4">
              <textarea
                className="w-full p-4 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                rows={4}
                placeholder="Describe your space mission idea... (e.g., 'Send a probe to Mars to study the atmosphere and search for signs of life')"
              />
              
              <button className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-6 rounded-lg transition-colors">
                Generate Mission
              </button>
              
              <p className="text-sm text-gray-400 text-center">
                Our AI will generate a detailed mission specification based on your description
              </p>
            </div>
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
            <h3 className="text-xl font-semibold text-white mb-2">3D Visualization</h3>
            <p className="text-gray-300">
              Explore your missions in interactive 3D with spacecraft, trajectories, and celestial bodies
            </p>
          </div>
        </div>
        
        <div className="text-center mt-16">
          <div className={`border rounded-lg p-4 max-w-md mx-auto ${
            backendStatus === 'connected' 
              ? 'bg-green-500/20 border-green-500/30' 
              : backendStatus === 'error'
              ? 'bg-red-500/20 border-red-500/30'
              : 'bg-yellow-500/20 border-yellow-500/30'
          }`}>
            <p className={`font-medium ${
              backendStatus === 'connected' 
                ? 'text-green-300' 
                : backendStatus === 'error'
                ? 'text-red-300'
                : 'text-yellow-300'
            }`}>
              {backendStatus === 'connected' && '✅ Frontend & Backend Connected!'}
              {backendStatus === 'error' && '❌ Backend Connection Failed'}
              {backendStatus === 'loading' && '⏳ Checking Backend...'}
            </p>
            <p className={`text-sm mt-1 ${
              backendStatus === 'connected' 
                ? 'text-green-200' 
                : backendStatus === 'error'
                ? 'text-red-200'
                : 'text-yellow-200'
            }`}>
              Backend API: <span className="font-mono">http://localhost:8000</span>
            </p>
            {backendStatus === 'error' && (
              <p className="text-red-200 text-xs mt-2">
                Make sure the backend is running: <code>npm start</code>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;