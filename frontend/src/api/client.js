// Axios instance for the MlimiSmart API.
import axios from 'axios'

const TOKEN_KEY = 'mlimismart_token'

export const api = axios.create({
  baseURL: '/api',
  timeout: 40000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach the JWT to every request once the farmer has logged in.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// An expired or invalid session clears the stored token so the app returns to
// the login screen rather than repeatedly retrying with a dead token.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem('mlimismart_farmer')
    }
    return Promise.reject(error)
  },
)

export function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem('mlimismart_farmer')
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

// Turns an axios failure into a message that can be shown to a farmer.
export function errorMessage(error, fallback) {
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail
    if (typeof detail === 'string') return detail
    // FastAPI validation errors arrive as a list of objects.
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  }
  if (error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED') return null
  return fallback
}
