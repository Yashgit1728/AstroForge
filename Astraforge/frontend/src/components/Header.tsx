import React from 'react';

type ActiveView = 'dashboard' | 'planner' | 'vehicles' | 'simulation';

interface HeaderProps {
  activeView: ActiveView;
  setActiveView: (view: ActiveView) => void;
}

const Header: React.FC<HeaderProps> = ({ activeView, setActiveView }) => {
  return (
    <header className="bg-space-900/80 backdrop-blur-md border-b border-space-700/50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-purple-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-sm">🚀</span>
            </div>
            <h1 className="text-2xl font-bold text-white">AstraForge</h1>
            <span className="text-space-300 text-sm">Space Mission Simulator</span>
          </div>
          <nav className="flex space-x-6">
            <button 
              onClick={() => setActiveView('dashboard')}
              className={`transition-colors ${
                activeView === 'dashboard' ? 'text-white' : 'text-space-200 hover:text-white'
              }`}
            >
              Dashboard
            </button>
            <button 
              onClick={() => setActiveView('planner')}
              className={`transition-colors ${
                activeView === 'planner' ? 'text-white' : 'text-space-200 hover:text-white'
              }`}
            >
              Mission Planner
            </button>
            <button 
              onClick={() => setActiveView('vehicles')}
              className={`transition-colors ${
                activeView === 'vehicles' ? 'text-white' : 'text-space-200 hover:text-white'
              }`}
            >
              Vehicles
            </button>
            <button 
              onClick={() => setActiveView('simulation')}
              className={`transition-colors ${
                activeView === 'simulation' ? 'text-white' : 'text-space-200 hover:text-white'
              }`}
            >
              Simulation
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;