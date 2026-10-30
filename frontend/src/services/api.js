export const API_URL =
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const TOKEN_KEY = 'knowvia_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

// fetch wrapper for the dashboard API. Adds the admin token, and on a 401
// clears it and tells the app to show the login screen.
export async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {})
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(url, { ...options, headers })

  if (response.status === 401) {
    clearToken()
    window.dispatchEvent(new Event('knowvia:logout'))
  }

  return response
}

export async function login(password) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  })

  if (response.status === 401) throw new Error('Wrong password.')
  if (response.status === 503) throw new Error('Login is not configured.')
  if (response.status === 429) throw new Error('Too many attempts. Try again in a few minutes.')  
  if (!response.ok) throw new Error('Could not sign in. Try again.')

  const data = await response.json()
  localStorage.setItem(TOKEN_KEY, data.token)
}

export function logout() {
  clearToken()
  window.dispatchEvent(new Event('knowvia:logout'))
}