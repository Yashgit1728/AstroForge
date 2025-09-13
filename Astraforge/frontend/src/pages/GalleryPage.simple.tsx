import React from 'react';
import { Link } from 'react-router-dom';

const GalleryPage: React.FC = () => {
  const exampleMissions = [
    {
      id: '1',
      name: 'Mars Sample Return',
      description: 'Collect samples from Mars surface and return them to Earth',
      difficulty: 'Advanced',
      duration: '450 days',
      image: '🔴'
    },
    {
      id: '2', 
      name: 'Europa Ice Explorer',
      description: 'Study the subsurface ocean of Jupiter\'s moon Europa',
      difficulty: 'Expert',
      duration: '2.5 years',
      image: '🌙'
    },
    {
      id: '3',
      name: 'Asteroid Mining Mission',
      description: 'Extract valuable minerals from near-Earth asteroids',
      difficulty: 'Intermediate',
      duration: '180 days',
      image: '☄️'
    },
    {
      id: '4',
      name: 'Solar Observatory',
      description: 'Deploy advanced solar monitoring equipment',
      difficulty: 'Beginner',
      duration: '90 days',
      image: '☀️'
    },
    {
      id: '5',
      name: 'Lunar Base Setup',
      description: 'Establish the first permanent lunar research station',
      difficulty: 'Advanced',
      duration: '1 year',
      image: '🌕'
    },
    {
      id: '6',
      name: 'Venus Atmospheric Probe',
      description: 'Study the dense atmosphere and surface of Venus',
      difficulty: 'Expert',
      duration: '300 days',
      image: '🟡'
    }
  ];

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner': return 'bg-green-500/20 text-green-300 border-green-500/30';
      case 'Intermediate': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
      case 'Advanced': return 'bg-orange-500/20 text-orange-300 border-orange-500/30';
      case 'Expert': return 'bg-red-500/20 text-red-300 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 pt-24">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">
            🌌 Mission Gallery
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Explore example missions and discover the possibilities of space exploration
          </p>
        </div>

        <div className="mb-8 flex justify-center">
          <div className="flex gap-4">
            <button className="px-6 py-2 bg-purple-600 text-white rounded-lg font-medium">
              All Missions
            </button>
            <button className="px-6 py-2 bg-white/10 text-gray-300 rounded-lg font-medium hover:bg-white/20">
              My Missions
            </button>
            <button className="px-6 py-2 bg-white/10 text-gray-300 rounded-lg font-medium hover:bg-white/20">
              Favorites
            </button>
          </div>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {exampleMissions.map((mission) => (
            <div
              key={mission.id}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 hover:border-purple-500/50 transition-all duration-300 hover:transform hover:scale-105"
            >
              <div className="text-center mb-4">
                <div className="text-4xl mb-2">{mission.image}</div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  {mission.name}
                </h3>
              </div>
              
              <p className="text-gray-300 text-sm mb-4 line-clamp-3">
                {mission.description}
              </p>
              
              <div className="flex justify-between items-center mb-4">
                <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getDifficultyColor(mission.difficulty)}`}>
                  {mission.difficulty}
                </span>
                <span className="text-gray-400 text-sm">
                  ⏱️ {mission.duration}
                </span>
              </div>
              
              <div className="flex gap-2">
                <Link
                  to={`/mission/${mission.id}`}
                  className="flex-1 bg-purple-600 hover:bg-purple-700 text-white text-center py-2 px-4 rounded-lg font-medium transition-colors"
                >
                  View Details
                </Link>
                <button className="bg-white/10 hover:bg-white/20 text-white py-2 px-4 rounded-lg font-medium transition-colors">
                  ⭐
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-12">
          <Link
            to="/"
            className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            <span>🚀</span>
            Create Your Own Mission
          </Link>
        </div>
      </div>
    </div>
  );
};

export default GalleryPage;