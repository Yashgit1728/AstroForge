import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, handleApiResponse, handlePaginatedResponse } from '../lib/api';
import { Mission, PaginatedResponse, ApiResponse } from '../types';

// Query keys
export const missionKeys = {
  all: ['missions'] as const,
  lists: () => [...missionKeys.all, 'list'] as const,
  list: (filters: Record<string, any>) => [...missionKeys.lists(), filters] as const,
  details: () => [...missionKeys.all, 'detail'] as const,
  detail: (id: string) => [...missionKeys.details(), id] as const,
};

// Fetch missions with pagination and filtering
export const useMissions = (params?: {
  page?: number;
  per_page?: number;
  search?: string;
  mission_type?: string;
}) => {
  return useQuery({
    queryKey: missionKeys.list(params || {}),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.page) searchParams.append('page', params.page.toString());
      if (params?.per_page) searchParams.append('per_page', params.per_page.toString());
      if (params?.search) searchParams.append('search', params.search);
      if (params?.mission_type) searchParams.append('mission_type', params.mission_type);

      const response = await apiClient.get<PaginatedResponse<Mission>>(
        `/api/missions?${searchParams.toString()}`
      );
      return handlePaginatedResponse(response);
    },
  });
};

// Fetch single mission
export const useMission = (id: string) => {
  return useQuery({
    queryKey: missionKeys.detail(id),
    queryFn: async () => {
      const response = await apiClient.get<ApiResponse<Mission>>(`/api/missions/${id}`);
      return handleApiResponse(response);
    },
    enabled: !!id,
  });
};

// Create mission mutation
export const useCreateMission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (missionData: Partial<Mission>) => {
      const response = await apiClient.post<ApiResponse<Mission>>('/api/missions', missionData);
      return handleApiResponse(response);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: missionKeys.lists() });
    },
  });
};

// Update mission mutation
export const useUpdateMission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Mission> }) => {
      const response = await apiClient.put<ApiResponse<Mission>>(`/api/missions/${id}`, data);
      return handleApiResponse(response);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: missionKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: missionKeys.lists() });
    },
  });
};

// Delete mission mutation
export const useDeleteMission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await apiClient.delete<ApiResponse<void>>(`/api/missions/${id}`);
      return handleApiResponse(response);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: missionKeys.lists() });
    },
  });
};

// Generate mission from prompt
export const useGenerateMission = () => {
  return useMutation({
    mutationFn: async (prompt: string) => {
      const response = await apiClient.post<ApiResponse<Mission>>('/api/missions/generate', {
        prompt,
      });
      return handleApiResponse(response);
    },
  });
};