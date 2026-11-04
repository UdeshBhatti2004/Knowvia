import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getUsage } from '../services/api'

export const USAGE_KEY = ['usage']

// Shared by the sidebar and every page. One cache, one request.
export function useUsage() {
  return useQuery({ queryKey: USAGE_KEY, queryFn: getUsage })
}

// Call after anything that changes usage (upload, delete).
export function useRefreshUsage() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: USAGE_KEY })
}