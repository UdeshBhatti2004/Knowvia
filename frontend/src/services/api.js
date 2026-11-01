export const API_URL =
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const TOKEN_KEY = 'knowvia_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

// fetch wrapper for the dashboard API. Adds the token, and on a 401
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

export async function getMe() {
  const response = await apiFetch(`${API_URL}/auth/me`)
  if (!response.ok) throw new Error('Could not load account.')
  return response.json()
}

export async function updateWorkspace(name) {
  const response = await apiFetch(`${API_URL}/auth/workspace`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (response.status === 403) {
    throw new Error('The admin account has no workspace to rename.')
  }
  if (response.status === 422) throw new Error('Enter a workspace name.')
  if (!response.ok) throw new Error('Could not save. Try again.')
  const data = await response.json()
  window.dispatchEvent(new Event('knowvia:account-updated'))
  return data
}

async function authRequest(path, body, errors) {
  const response = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (response.status === 429) {
    throw new Error('Too many attempts. Try again in a few minutes.')
  }
  if (response.status === 503) throw new Error('Login is not configured.')
  if (errors[response.status]) throw new Error(errors[response.status])
  if (!response.ok) throw new Error('Something went wrong. Try again.')

  const data = await response.json()
  localStorage.setItem(TOKEN_KEY, data.token)
  return data
}

// With an email: account login. Without: legacy admin-password login.
export function login(password, email) {
  const body = email ? { email, password } : { password }
  return authRequest('/auth/login', body, {
    401: email ? 'Wrong email or password.' : 'Wrong password.',
    422: 'Enter a valid email and password.',
  })
}

export function signup(email, password, workspaceName) {
  return authRequest(
    '/auth/signup',
    { email, password, workspace_name: workspaceName },
    {
      409: 'That email is already registered.',
      422: 'Check your email, and use a password of at least 8 characters.',
    },
  )
}

export function logout() {
  clearToken()
  window.dispatchEvent(new Event('knowvia:logout'))
}