/**
 * Centralized Axios HTTP client for the FastAPI backend.
 *
 * - Reads base URL from VITE_API_BASE_URL environment variable.
 * - Injects Authorization header when a token is available.
 * - Intercepts 401 responses to trigger logout.
 *
 * Token is set/cleared via setAuthToken() — called by AuthContext.
 * Token is NEVER stored in localStorage or sessionStorage.
 */

import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

/* ── Token management (memory-only) ── */
let _token = null;
let _onAuthError = null;

/**
 * Store token in memory. Called by AuthContext on login.
 * @param {string|null} token
 */
export function setAuthToken(token) {
  _token = token;
}

/**
 * Register a callback that fires on 401 responses.
 * AuthContext uses this to auto-logout.
 * @param {Function|null} callback
 */
export function setAuthErrorHandler(callback) {
  _onAuthError = callback;
}

/* ── Request interceptor — inject Bearer token ── */
api.interceptors.request.use(
  (config) => {
    if (_token) {
      config.headers.Authorization = `Bearer ${_token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/* ── Response interceptor — handle 401 ── */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && _onAuthError) {
      _onAuthError();
    }
    return Promise.reject(error);
  }
);

export default api;
