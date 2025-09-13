import { useState } from 'react'
import Header from './components/Header'
import MissionPlanner from './components/MissionPlanner'
import MissionDashboard from './components/MissionDashboard'
import VehicleManagement from './components/VehicleManagement'
import SimulationCenter from './components/SimulationCenter'
import StarField from './components/StarField'

type ActiveView = 'dashboard' | 'planner' | 'vehicles' | 'simulation';

function App() {
  const [activeView, setActiveView] = useState<ActiveView>('dashboard');

  const renderContent = () => {
    switch (activeView) {
      case 'dashboard':
        return <MissionDashboard />;
      case 'planner':
        return <MissionPlanner />;
      case 'vehicles':
        return <VehicleManagement />;
      case 'simulation':
        return <SimulationCenter />;
      default:
        return <MissionDashboard />;
    }
  };

  return (
    <div className="min-h-screen text-white relative">
      <StarField />
      <div className="relative z-10">
        <Header activeView={activeView} setActiveView={setActiveView} />
        {renderContent()}
      </div>
    </div>
  )
}

export default App