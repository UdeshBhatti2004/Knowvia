import { useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { API_URL, apiFetch } from '../services/api'
import { USAGE_KEY } from './useUsage'

export const SOURCES_KEY = ['sources']

// How often (ms) to re-check while a file is processing.
const POLL_INTERVAL_MS = 3000

async function getSources() {
  const response = await apiFetch(`${API_URL}/sources`)
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(data.detail || 'Unable to load your documents.')
  }

  return Array.isArray(data.sources) ? data.sources : []
}

const isProcessing = (sources) =>
  Array.isArray(sources) && sources.some((s) => s.status === 'Processing')

// Shared by Overview and Uploaded Documents. Polls only while a file is
// processing, and stops by itself afterwards.
export function useSources() {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: SOURCES_KEY,
    queryFn: getSources,
    staleTime: 0,
    refetchInterval: (q) =>
      isProcessing(q.state.data) ? POLL_INTERVAL_MS : false,
  })

  // When processing finishes, a document may have failed (failed docs don't
  // count toward the limit), so refresh usage once.
  const processing = isProcessing(query.data)
  const wasProcessing = useRef(false)

  useEffect(() => {
    if (wasProcessing.current && !processing) {
      queryClient.invalidateQueries({ queryKey: USAGE_KEY })
    }
    wasProcessing.current = processing
  }, [processing, queryClient])

  return query
}

// Call after anything that changes the document list (upload, delete).
export function useRefreshSources() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: SOURCES_KEY })
}