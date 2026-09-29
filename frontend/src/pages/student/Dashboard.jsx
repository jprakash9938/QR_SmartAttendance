import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import EmptyState from '../../components/EmptyState';
import { useAuth } from '../../hooks/useAuth';
import {
  ScanLine,
  History,
  CheckCircle2,
  Calendar,
  BookOpen,
  ArrowRight,
  Clock,
} from 'lucide-react';

export default function StudentDashboard() {
  const { user } = useAuth();
  const [todayAttendance, setTodayAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/student/attendance/today');
      setTodayAttendance(res.data);
    } catch {
      setError('Failed to load today\'s attendance.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) return <LoadingSpinner size="lg" className="min-h-[60vh]" />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          Hello, {user?.name?.split(' ')[0]}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Link
          to="/student/scan"
          className="flex items-center justify-between rounded-2xl border border-primary/30 bg-primary/5 p-5 shadow-sm hover:bg-primary/10 transition-all group"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/20">
              <ScanLine className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="font-semibold text-foreground">Scan QR Code</p>
              <p className="text-xs text-muted-foreground">Mark your attendance now</p>
            </div>
          </div>
          <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
        </Link>
        <Link
          to="/student/attendance"
          className="flex items-center justify-between rounded-2xl border border-border bg-card p-5 shadow-sm hover:border-primary/20 hover:shadow-md transition-all group"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted">
              <History className="h-6 w-6 text-muted-foreground" />
            </div>
            <div>
              <p className="font-semibold text-foreground">View History</p>
              <p className="text-xs text-muted-foreground">Your full attendance record</p>
            </div>
          </div>
          <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
        </Link>
      </div>

      {/* Today's Stats */}
      <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-1">
          <Calendar className="h-4 w-4 text-primary" />
          <h2 className="font-semibold text-foreground">Today&apos;s Attendance</h2>
        </div>
        <p className="text-xs text-muted-foreground mb-4">
          {todayAttendance.length} session{todayAttendance.length !== 1 ? 's' : ''} attended today
        </p>

        {todayAttendance.length === 0 ? (
          <div className="flex flex-col items-center py-6 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-muted mb-3">
              <CheckCircle2 className="h-7 w-7 text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground">No attendance marked today.</p>
            <p className="text-xs text-muted-foreground mt-1">Scan a QR code to mark your attendance.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {todayAttendance.map((record) => (
              <div
                key={record.id}
                className="flex items-center justify-between rounded-xl bg-muted/50 border border-border px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-green-500/10">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {record.class_name || `Session #${record.session_id}`}
                    </p>
                    <p className="text-xs text-muted-foreground flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(record.marked_at).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1 rounded-full bg-green-500/10 border border-green-500/20 px-2.5 py-0.5 text-xs font-medium text-green-600">
                  {record.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
