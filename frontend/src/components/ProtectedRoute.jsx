import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

/**
 * Route guard component.
 *
 * - Redirects to login if not authenticated
 * - Redirects to correct dashboard if wrong role
 * - NOTE: This is UX-only protection; backend enforces real auth/role checks
 */
export default function ProtectedRoute({ children, allowedRole }) {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (allowedRole && user?.role !== allowedRole) {
    const redirectPath = user?.role === 'TEACHER'
      ? '/teacher/dashboard'
      : '/student/dashboard';
    return <Navigate to={redirectPath} replace />;
  }

  return children;
}
