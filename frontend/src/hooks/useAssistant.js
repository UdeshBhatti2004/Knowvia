import { useQuery } from '@tanstack/react-query'
import { API_URL, apiFetch } from '../services/api'

export const ASSISTANT_KEY = ['assistant']
export const ASSISTANT_STATUS_KEY = ['assistant-status']

async function getJson(path, message) {
  const response = await apiFetch(`${API_URL}${path}`)
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(data.detail || message)
  }

  return data
}

// Saved assistant settings (name, welcome and fallback message).
// Assistant Setup writes the cache when you save, so a long staleTime is safe.
export function useAssistant() {
  return useQuery({
    queryKey: ASSISTANT_KEY,
    queryFn: () => getJson('/assistant', 'Unable to load assistant.'),
    staleTime: 5 * 60_000,
  })
}

// Whether the owner has tested the assistant yet. Always refetch.
export function useAssistantStatus() {
  return useQuery({
    queryKey: ASSISTANT_STATUS_KEY,
    queryFn: () =>
      getJson('/assistant/status', 'Unable to load assistant status.'),
    staleTime: 0,
  })
}