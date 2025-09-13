import React from 'react';
import { Link } from 'react-router-dom';
import { Mission } from '../../types';

interface MissionCardProps {
  mission: Mission;
  onClone?: (mission: Mission) => void;
  onDelete?: (missionId: string) => void;
  showActions?: boolean;
}

const MissionCard: React.FC<MissionCardProps> = ({
  mission,
  onClone,
  onDelete,
  showActions = true,
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getMissionTypeColor = (targetBody: string) => {
    switch (targetBody.toLowerCase()) {
      case 'mars':
        return 'bg-red-600/30 text-red-300';
      case 'moon':
        return 'bg-gray-600/30 text-gray-300';
      case 'venus':
        return 'bg-yellow-600/30 text-yellow-300';
      case 'jupiter':
        return 'bg-orange-600/30 text-orange-300';
      default:
        return 'bg-purple-600/30 text-purple-300';
    }
  };

  return (
    <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all duration-200 group">
      <Link to={`/mission/${mission.id}`} className="block">
        {/* Mission Preview Image */}
        <div className="aspect-video bg-gradient-to-br from-purple-600/20 to-blue-600/20 rounded-lg mb-4 flex items-center justify-center relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-slate-900/50 to-transparent"></div>
          <svg className="w-12 h-12 text-white/50 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          
          {/* Mission Type Badge */}
          <div className="absolute top-3 right-3 z-10">
            <span className={`px-2 py-1 rounded text-xs font-medium ${getMissionTypeColor(mission.trajectory.target_body)}`}>
              {mission.trajectory.target_body}
            </span>
          </div>
        </div>

        {/* Mission Info */}
        <h3 className="text-xl font-semibold text-white mb-2 group-hover:text-purple-300 transition-colors line-clamp-1">
          {mission.name}
        </h3>

        <p className="text-gray-300 text-sm mb-4 line-clamp-2">
          {mission.description}
        </p>

        {/* Mission Metrics */}
        <div className="flex justify-between items-center text-sm mb-4">
          <div className="flex gap-4">
            <span className="text-gray-400">
              ΔV: <span className="text-white">{mission.trajectory.total_delta_v.toFixed(1)} km/s</span>
            </span>
            <span className="text-gray-400">
              Duration: <span className="text-white">{mission.timeline.total_duration_days}d</span>
            </span>
          </div>
        </div>

        {/* Objectives Preview */}
        <div className="mb-4">
          <div className="flex flex-wrap gap-1">
            {mission.objectives.slice(0, 2).map((objective, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-blue-600/20 text-blue-300 rounded text-xs"
              >
                {objective.length > 20 ? `${objective.substring(0, 20)}...` : objective}
              </span>
            ))}
            {mission.objectives.length > 2 && (
              <span className="px-2 py-1 bg-gray-600/20 text-gray-300 rounded text-xs">
                +{mission.objectives.length - 2} more
              </span>
            )}
          </div>
        </div>
      </Link>

      {/* Footer */}
      <div className="pt-4 border-t border-white/10 flex justify-between items-center">
        <span className="text-xs text-gray-400">
          Created {formatDate(mission.created_at)}
        </span>
        
        {showActions && (
          <div className="flex gap-2">
            {onClone && (
              <button
                onClick={(e) => {
                  e.preventDefault();
                  onClone(mission);
                }}
                className="text-gray-400 hover:text-white transition-colors p-1"
                title="Clone mission"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            )}
            
            {onDelete && (
              <button
                onClick={(e) => {
                  e.preventDefault();
                  if (window.confirm('Are you sure you want to delete this mission?')) {
                    onDelete(mission.id);
                  }
                }}
                className="text-gray-400 hover:text-red-400 transition-colors p-1"
                title="Delete mission"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MissionCard;