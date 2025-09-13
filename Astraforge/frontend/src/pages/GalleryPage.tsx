import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMissions, useCreateMission, useDeleteMission } from '../hooks/useMissions';
import MissionCard from '../components/shared/MissionCard';
import { Mission } from '../types';
import ErrorBoundary from '../components/shared/ErrorBoundary';

const GalleryPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortBy, setSortBy] = useState<'created_at' | 'name' | 'duration'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const itemsPerPage = 12;

  // Fetch missions with search and filter parameters
  const { data: missionsResponse, isLoading, error, refetch } = useMissions({
    page: currentPage,
    per_page: itemsPerPage,
    search: searchTerm || undefined,
    mission_type: selectedFilter !== 'all' ? selectedFilter : undefined,
  });

  const createMission = useCreateMission();
  const deleteMission = useDeleteMission();

  const filters = [
    { id: 'all', label: 'All Missions', count: missionsResponse?.total || 0 },
    { id: 'mars', label: 'Mars Missions', count: 0 },
    { id: 'moon', label: 'Lunar Missions', count: 0 },
    { id: 'venus', label: 'Venus Missions', count: 0 },
    { id: 'jupiter', label: 'Jupiter Missions', count: 0 },
    { id: 'asteroid', label: 'Asteroid Missions', count: 0 },
  ];

  // Sort missions locally if needed
  const sortedMissions = useMemo(() => {
    if (!missionsResponse?.data) return [];
    
    const missions = [...missionsResponse.data];
    return missions.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'duration':
          aValue = a.timeline.total_duration_days;
          bValue = b.timeline.total_duration_days;
          break;
        case 'created_at':
        default:
          aValue = new Date(a.created_at).getTime();
          bValue = new Date(b.created_at).getTime();
          break;
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  }, [missionsResponse?.data, sortBy, sortOrder]);

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setCurrentPage(1); // Reset to first page when searching
  };

  const handleFilterChange = (filterId: string) => {
    setSelectedFilter(filterId);
    setCurrentPage(1); // Reset to first page when filtering
  };

  const handleSort = (newSortBy: typeof sortBy) => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
  };

  const handleCloneMission = async (mission: Mission) => {
    try {
      const clonedMission = {
        ...mission,
        name: `${mission.name} (Copy)`,
        id: undefined, // Remove ID so a new one is generated
        created_at: undefined,
        user_id: undefined,
      };
      
      const newMission = await createMission.mutateAsync(clonedMission);
      navigate(`/mission/${newMission.id}`);
    } catch (error) {
      console.error('Failed to clone mission:', error);
    }
  };

  const handleDeleteMission = async (missionId: string) => {
    try {
      await deleteMission.mutateAsync(missionId);
      refetch(); // Refresh the list
    } catch (error) {
      console.error('Failed to delete mission:', error);
    }
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-transparent">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h1 className="text-4xl font-bold text-white mb-2">Mission Gallery</h1>
                <p className="text-gray-300">
                  Explore example missions and your saved designs
                  {missionsResponse && (
                    <span className="ml-2 text-purple-400">
                      ({missionsResponse.total} missions)
                    </span>
                  )}
                </p>
              </div>
              <button
                onClick={() => navigate('/')}
                className="bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Create New Mission
              </button>
            </div>

            {/* Search and Controls */}
            <div className="space-y-4">
              {/* Search Bar */}
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  placeholder="Search missions by name, description, or objectives..."
                  value={searchTerm}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                {searchTerm && (
                  <button
                    onClick={() => handleSearch('')}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-white"
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Filters and Sort */}
              <div className="flex flex-col lg:flex-row gap-4 justify-between">
                {/* Filter Buttons */}
                <div className="flex gap-2 flex-wrap">
                  {filters.map((filter) => (
                    <button
                      key={filter.id}
                      onClick={() => handleFilterChange(filter.id)}
                      className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 ${
                        selectedFilter === filter.id
                          ? 'bg-purple-600 text-white'
                          : 'bg-white/10 text-gray-300 hover:bg-white/20'
                      }`}
                    >
                      {filter.label}
                      {filter.id === 'all' && missionsResponse && (
                        <span className="text-xs bg-white/20 px-2 py-1 rounded-full">
                          {missionsResponse.total}
                        </span>
                      )}
                    </button>
                  ))}
                </div>

                {/* Sort Controls */}
                <div className="flex items-center gap-3">
                  <span className="text-gray-400 text-sm">Sort by:</span>
                  <div className="flex gap-2">
                    {[
                      { key: 'created_at', label: 'Date' },
                      { key: 'name', label: 'Name' },
                      { key: 'duration', label: 'Duration' },
                    ].map((sort) => (
                      <button
                        key={sort.key}
                        onClick={() => handleSort(sort.key as typeof sortBy)}
                        className={`px-3 py-1 rounded text-sm font-medium transition-colors flex items-center gap-1 ${
                          sortBy === sort.key
                            ? 'bg-purple-600 text-white'
                            : 'bg-white/10 text-gray-300 hover:bg-white/20'
                        }`}
                      >
                        {sort.label}
                        {sortBy === sort.key && (
                          <svg 
                            className={`w-3 h-3 transition-transform ${sortOrder === 'desc' ? 'rotate-180' : ''}`} 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                          </svg>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="animate-spin w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-white">Loading missions...</p>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-4">Failed to Load Missions</h2>
              <p className="text-gray-300 mb-6">
                There was an error loading the mission gallery. Please try again.
              </p>
              <button
                onClick={() => refetch()}
                className="bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && sortedMissions.length === 0 && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-4">
                {searchTerm ? 'No Missions Found' : 'No Missions Yet'}
              </h2>
              <p className="text-gray-300 mb-6">
                {searchTerm 
                  ? `No missions match your search for "${searchTerm}". Try different keywords or filters.`
                  : 'Start by creating your first mission to see it here in the gallery.'
                }
              </p>
              <div className="flex gap-3 justify-center">
                {searchTerm && (
                  <button
                    onClick={() => handleSearch('')}
                    className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
                  >
                    Clear Search
                  </button>
                )}
                <button
                  onClick={() => navigate('/')}
                  className="bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
                >
                  Create Mission
                </button>
              </div>
            </div>
          )}

          {/* Mission Grid */}
          {!isLoading && !error && sortedMissions.length > 0 && (
            <>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
                {sortedMissions.map((mission) => (
                  <MissionCard
                    key={mission.id}
                    mission={mission}
                    onClone={handleCloneMission}
                    onDelete={handleDeleteMission}
                    showActions={true}
                  />
                ))}
              </div>

              {/* Pagination */}
              {missionsResponse && missionsResponse.total_pages > 1 && (
                <div className="flex items-center justify-center gap-2">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-3 py-2 bg-white/10 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/20 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  
                  <div className="flex gap-1">
                    {Array.from({ length: Math.min(5, missionsResponse.total_pages) }, (_, i) => {
                      let pageNum;
                      if (missionsResponse.total_pages <= 5) {
                        pageNum = i + 1;
                      } else if (currentPage <= 3) {
                        pageNum = i + 1;
                      } else if (currentPage >= missionsResponse.total_pages - 2) {
                        pageNum = missionsResponse.total_pages - 4 + i;
                      } else {
                        pageNum = currentPage - 2 + i;
                      }
                      
                      return (
                        <button
                          key={pageNum}
                          onClick={() => handlePageChange(pageNum)}
                          className={`px-3 py-2 rounded-lg transition-colors ${
                            currentPage === pageNum
                              ? 'bg-purple-600 text-white'
                              : 'bg-white/10 text-white hover:bg-white/20'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                  </div>
                  
                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === missionsResponse.total_pages}
                    className="px-3 py-2 bg-white/10 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/20 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              )}

              {/* Results Summary */}
              {missionsResponse && (
                <div className="text-center mt-6 text-gray-400 text-sm">
                  Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, missionsResponse.total)} of {missionsResponse.total} missions
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default GalleryPage;