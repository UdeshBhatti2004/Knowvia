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
// Pass { skipLogoutOn401: true } for calls where a 401 means "wrong input",
// not "session expired".
export async function apiFetch(url, options = {}) {
  const { skipLogoutOn401, ...fetchOptions } = options
  const headers = new Headers(fetchOptions.headers || {})
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(url, { ...fetchOptions, headers })

  if (response.status === 401 && !skipLogoutOn401) {
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

export async function getUsage() {
  const response = await apiFetch(`${API_URL}/usage`)
  if (!response.ok) throw new Error('Could not load usage.')
  return response.json()
}

export async function createSubscription(plan) {
  const response = await apiFetch(`${API_URL}/billing/subscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plan }),
  })
  if (response.status === 503) {
    throw new Error('Billing is not available yet.')
  }
  if (response.status === 409) {
    throw new Error('You already have a paid plan. Cancel it first.')
  }
  if (!response.ok) throw new Error('Could not start the payment. Try again.')
  return response.json()
}

export async function cancelSubscription() {
  const response = await apiFetch(`${API_URL}/billing/cancel`, {
    method: 'POST',
  })
  if (response.status === 404) throw new Error('No active subscription found.')
  if (response.status === 503) throw new Error('Billing is not available yet.')
  if (!response.ok) throw new Error('Could not cancel the plan. Try again.')
  return response.json()
}

export async function updateWorkspace(name) {
  const response = await apiFetch(`${API_URL}/auth/workspace`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (response.status === 422) throw new Error('Enter a workspace name.')
  if (!response.ok) throw new Error('Could not save. Try again.')
  const data = await response.json()
  window.dispatchEvent(new Event('knowvia:account-updated'))
  return data
}

export async function changePassword(currentPassword, newPassword) {
  const response = await apiFetch(`${API_URL}/auth/password`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
    skipLogoutOn401: true,
  })

  if (response.status === 429) {
    throw new Error('Too many attempts. Try again in a few minutes.')
  }
  if (response.status === 401) {
    // Wrong current password, or the session really expired.
    const stillSignedIn = await apiFetch(`${API_URL}/auth/me`)
    if (stillSignedIn.ok) throw new Error('Current password is wrong.')
    throw new Error('Session expired. Sign in again.')
  }
  if (response.status === 422) {
    throw new Error(
      'Use a new password of at least 8 characters, different from the current one.',
    )
  }
  if (!response.ok) throw new Error('Could not change password. Try again.')

  const data = await response.json()
  localStorage.setItem(TOKEN_KEY, data.token)
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

export function login(email, password) {
  return authRequest(
    '/auth/login',
    { email, password },
    {
      401: 'Wrong email or password.',
      422: 'Enter a valid email and password.',
    },
  )
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

export async function forgotPassword(email) {
  const response = await fetch(`${API_URL}/auth/forgot-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  })

  if (response.status === 429) {
    throw new Error('Too many attempts. Try again in a few minutes.')
  }
  if (response.status === 422) throw new Error('Enter a valid email.')
  if (!response.ok) throw new Error('Something went wrong. Try again.')
}

export async function resetPassword(token, newPassword) {
  const response = await fetch(`${API_URL}/auth/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, new_password: newPassword }),
  })

  if (response.status === 429) {
    throw new Error('Too many attempts. Try again in a few minutes.')
  }
  if (response.status === 400) {
    throw new Error('This reset link is invalid or has expired.')
  }
  if (response.status === 422) {
    throw new Error('Use a password of at least 8 characters.')
  }
  if (!response.ok) throw new Error('Something went wrong. Try again.')
}
