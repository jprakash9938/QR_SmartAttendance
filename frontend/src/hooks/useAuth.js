import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

/**
 * Convenience hook for accessing auth context.
 * @returns {{ user, token, loading, isAuthenticated, login, register, logout }}
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
