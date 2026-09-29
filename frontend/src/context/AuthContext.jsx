/**
 * AuthContext — Global authentication state.
 *
 * Security: JWT token is stored in React state (memory only).
 * It is NOT persisted to localStorage or sessionStorage.
 * This means users must re-login after a page refresh.
 *
 * TODO(security): Consider implementing HttpOnly cookie-based
 * auth in the backend for persistent secure sessions.
 */

import { createContext, useState, useCallback, useEffect, useRef } from 'react';
import api, { setAuthToken, setAuthErrorHandler } from '../services/api';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(false);
  const logoutCalledRef = useRef(false);

  const isAuthenticated = !!token && !!user;

  /* ── Logout: clear state and hard redirect ── */
  const logout = useCallback(() => {
    if (logoutCalledRef.current) return;
    logoutCalledRef.current = true;

    setUser(null);
    setToken(null);
    setAuthToken(null);

    // Full page redirect to clear any cached state
    window.location.href = '/';
  }, []);

  /* ── Register 401 handler with Axios ── */
  useEffect(() => {
    setAuthErrorHandler(logout);
    return () => setAuthErrorHandler(null);
  }, [logout]);

  /* ── Login ── */
  const login = useCallback(async (email, password) => {
    setLoading(true);
    try {
      const response = await api.post('/auth/login', { email, password });
      const { access_token, user: userData } = response.data;

      setToken(access_token);
      setAuthToken(access_token);
      setUser(userData);
      logoutCalledRef.current = false;

      return { success: true, user: userData };
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        'Login failed. Please check your credentials.';
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  }, []);

  /* ── Admin Login ── */
  const adminLogin = useCallback(async (email, password) => {
    setLoading(true);
    try {
      const response = await api.post('/admin/login', { email, password });
      const { access_token, user: userData } = response.data;

      setToken(access_token);
      setAuthToken(access_token);
      setUser(userData);
      logoutCalledRef.current = false;

      return { success: true, user: userData };
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        'Admin login failed. Please check your credentials.';
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  }, []);

  /* ── Register ── */
  const register = useCallback(async (name, email, password, role) => {
    setLoading(true);
    try {
      const response = await api.post('/auth/register', {
        name,
        email,
        password,
        role,
      });
      const { access_token, user: userData } = response.data;

      setToken(access_token);
      setAuthToken(access_token);
      setUser(userData);
      logoutCalledRef.current = false;

      return { success: true, user: userData };
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        'Registration failed. Please try again.';
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  }, []);

  const value = {
    user,
    token,
    loading,
    initializing,
    isAuthenticated,
    login,
    adminLogin,
    register,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
