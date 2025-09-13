import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-6xl font-bold text-white mb-6">
            🚀 AstraForge
          </h1>
          <p className="text-xl text-gray-300 mb-8">
            AI-powered space mission simulator
          </p>
          
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20 max-w-2xl mx-auto">
            <h2 className="text-2xl font-semibold text-white mb-6">
              Frontend is Working!
            </h2>
            
            <div className="space-y-4">
              <textarea
                className="w-full p-4 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                rows={4}
                placeholder="Describe your space mission..."
              />
              
              <button className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-6 rounded-lg">
                Generate Mission
              </button>
            </div>
          </div>
          
          <div className="mt-8 text-green-300">
            ✅ If you can see this, the frontend is working!
          </div>
        </div>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(<App />)