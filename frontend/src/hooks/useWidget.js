import { useQuery } from '@tanstack/react-query'
import { API_URL, apiFetch } from '../services/api'

export const WIDGET_KEY = ['widget']
export const WIDGET_DOMAINS_KEY = ['widget-domains']

async function getJson(path, message) {
  const response = await apiFetch(`${API_URL}${path}`)
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(data.detail || message)
  }

  return data
}

// Public widget key. Almost never changes.
export function useWidget() {
  return useQuery({
    queryKey: WIDGET_KEY,
    queryFn: () => getJson('/widget', 'Could not load widget.'),
    staleTime: 5 * 60_000,
  })
}

// Allowed domains. Install page writes the cache when you save.
export function useWidgetDomains() {
  return useQuery({
    queryKey: WIDGET_DOMAINS_KEY,
    queryFn: () => getJson('/widget/domains', 'Could not load domains.'),
    staleTime: 5 * 60_000,
  })
}