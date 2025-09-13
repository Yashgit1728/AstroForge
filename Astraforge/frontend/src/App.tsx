import { Routes, Route } from 'react-router-dom';
import { HomePage, MissionDetailPage, GalleryPage } from './pages';
import Navigation from './components/Navigation';
import StarField from './components/StarField';

function App() {
  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden">
      <StarField />
      <Navigation />
      <div className="relative z-10">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/gallery" element={<GalleryPage />} />
          <Route path="/mission/:id" element={<MissionDetailPage />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;