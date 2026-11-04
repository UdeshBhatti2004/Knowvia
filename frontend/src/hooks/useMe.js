import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getMe } from '../services/api'

export const ME_KEY = ['me']

// Account info (email, workspace name). Rarely changes, so cache it longer.
export function useMe() {
  return useQuery({
    queryKey: ME_KEY,
    queryFn: getMe,
    staleTime: 5 * 60_000,
  })
}

// Call after anything that changes the account (e.g. workspace rename).
export function useRefreshMe() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: ME_KEY })
}