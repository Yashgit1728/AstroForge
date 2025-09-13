import React from 'react';

const LoadingCard: React.FC = () => {
  return (
    <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 animate-pulse">
      {/* Image placeholder */}
      <div className="aspect-video bg-white/10 rounded-lg mb-4"></div>
      
      {/* Title placeholder */}
      <div className="h-6 bg-white/10 rounded mb-2"></div>
      
      {/* Description placeholder */}
      <div className="space-y-2 mb-4">
        <div className="h-4 bg-white/10 rounded"></div>
        <div className="h-4 bg-white/10 rounded w-3/4"></div>
      </div>
      
      {/* Metrics placeholder */}
      <div className="flex gap-4 mb-4">
        <div className="h-4 bg-white/10 rounded w-20"></div>
        <div className="h-4 bg-white/10 rounded w-24"></div>
      </div>
      
      {/* Tags placeholder */}
      <div className="flex gap-2 mb-4">
        <div className="h-6 bg-white/10 rounded w-16"></div>
        <div className="h-6 bg-white/10 rounded w-20"></div>
      </div>
      
      {/* Footer placeholder */}
      <div className="pt-4 border-t border-white/10 flex justify-between items-center">
        <div className="h-4 bg-white/10 rounded w-24"></div>
        <div className="flex gap-2">
          <div className="w-6 h-6 bg-white/10 rounded"></div>
          <div className="w-6 h-6 bg-white/10 rounded"></div>
        </div>
      </div>
    </div>
  );
};

export default LoadingCard;