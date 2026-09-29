import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

/* Layouts */
import TeacherLayout from '../layouts/TeacherLayout';
import StudentLayout from '../layouts/StudentLayout';

/* Auth */
import LoginPage from '../pages/auth/LoginPage';

/* Protected route */
import ProtectedRoute from '../components/ProtectedRoute';

/* Admin pages */
import AdminLayout from '../layouts/AdminLayout';
import AdminDashboard from '../pages/admin/AdminDashboard';
import AdminLogin from '../pages/admin/AdminLogin';

/* Teacher pages */
import TeacherDashboard from '../pages/teacher/Dashboard';
import Classes from '../pages/teacher/Classes';
import CreateSession from '../pages/teacher/CreateSession';
import Sessions from '../pages/teacher/Sessions';
import ActiveSession from '../pages/teacher/ActiveSession';
import SessionAttendance from '../pages/teacher/SessionAttendance';

/* Student pages */
import StudentDashboard from '../pages/student/Dashboard';
import ScanQR from '../pages/student/ScanQR';
import AttendanceHistory from '../pages/student/AttendanceHistory';

/* Shared */
import Profile from '../pages/shared/Profile';

function AuthRedirect() {
  const { isAuthenticated, user } = useAuth();
  if (!isAuthenticated) return <LoginPage />;
  if (user?.role === 'ADMIN') return <Navigate to="/admin/dashboard" replace />;
  return user?.role === 'TEACHER'
    ? <Navigate to="/teacher/dashboard" replace />
    : <Navigate to="/student/dashboard" replace />;
}

function AdminAuthRedirect() {
  const { isAuthenticated, user } = useAuth();
  if (isAuthenticated && user?.role === 'ADMIN') return <Navigate to="/admin/dashboard" replace />;
  if (isAuthenticated) return <Navigate to="/" replace />;
  return <AdminLogin />;
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/" element={<AuthRedirect />} />
        <Route path="/admin/login" element={<AdminAuthRedirect />} />

        {/* Admin routes */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRole="ADMIN">
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route path="dashboard" element={<AdminDashboard />} />
        </Route>

        {/* Teacher routes */}
        <Route
          path="/teacher"
          element={
            <ProtectedRoute allowedRole="TEACHER">
              <TeacherLayout />
            </ProtectedRoute>
          }
        >
          <Route path="dashboard" element={<TeacherDashboard />} />
          <Route path="classes" element={<Classes />} />
          <Route path="sessions/create" element={<CreateSession />} />
          <Route path="sessions" element={<Sessions />} />
          <Route path="sessions/:sessionId/active" element={<ActiveSession />} />
          <Route path="sessions/:sessionId/attendance" element={<SessionAttendance />} />
          <Route path="profile" element={<Profile />} />
        </Route>

        {/* Student routes */}
        <Route
          path="/student"
          element={
            <ProtectedRoute allowedRole="STUDENT">
              <StudentLayout />
            </ProtectedRoute>
          }
        >
          <Route path="dashboard" element={<StudentDashboard />} />
          <Route path="scan" element={<ScanQR />} />
          <Route path="attendance" element={<AttendanceHistory />} />
          <Route path="profile" element={<Profile />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
