import { useQuery } from '@tanstack/react-query'
import { API_URL, apiFetch } from '../services/api'

export const CONVERSATIONS_KEY = ['conversations']

async function getGroupedConversations(outcome) {
  const query = new URLSearchParams({ limit: '100' })
  if (outcome) query.set('outcome', outcome)

  let response
  try {
    response = await apiFetch(`${API_URL}/conversations/grouped?${query}`)
  } catch {
    throw new Error('Could not reach the server.')
  }

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(data.detail || 'Unable to load conversations.')
  }

  return Array.isArray(data.items) ? data.items : []
}

// One cache entry per filter ('' = All), so switching filters is instant
// after the first load.
export function useConversations(outcome) {
  return useQuery({
    queryKey: [...CONVERSATIONS_KEY, outcome || 'all'],
    queryFn: () => getGroupedConversations(outcome),
  })
}