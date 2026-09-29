import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import EmptyState from '../../components/EmptyState';
import { useAuth } from '../../hooks/useAuth';
import {
  BookOpen,
  QrCode,
  Users,
  CalendarPlus,
  ArrowRight,
  Clock,
  CheckCircle2,
  PlayCircle,
} from 'lucide-react';

export default function TeacherDashboard() {
  const { user } = useAuth();
  const [classes, setClasses] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const [classesRes, sessionsRes] = await Promise.all([
        api.get('/classes'),
        api.get('/teacher/sessions'),
      ]);
      setClasses(classesRes.data);
      setSessions(sessionsRes.data);
    } catch (err) {
      setError('Failed to load dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) return <LoadingSpinner size="lg" className="min-h-[60vh]" />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

  const activeSessions = sessions.filter((s) => s.status === 'ACTIVE');
  const completedSessions = sessions.filter((s) => s.status === 'COMPLETED');

  const statusIcon = (status) => {
    switch (status) {
      case 'ACTIVE': return <PlayCircle className="h-4 w-4 text-green-500" />;
      case 'COMPLETED': return <CheckCircle2 className="h-4 w-4 text-muted-foreground" />;
      default: return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  const statusBadge = (status) => {
    const styles = {
      ACTIVE: 'bg-green-500/10 text-green-600 border-green-500/20',
      COMPLETED: 'bg-muted text-muted-foreground border-border',
      PENDING: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20',
    };
    return `inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[status] || styles.PENDING}`;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          Welcome back, {user?.name?.split(' ')[0]}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Here&apos;s an overview of your classes and sessions.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 stagger-children">
        {[
          { label: 'Total Classes', value: classes.length, icon: BookOpen, color: 'text-primary' },
          { label: 'Active Sessions', value: activeSessions.length, icon: QrCode, color: 'text-green-500' },
          { label: 'Completed', value: completedSessions.length, icon: CheckCircle2, color: 'text-muted-foreground' },
        ].map((stat) => (
          <div key={stat.label} className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
                <p className="text-3xl font-bold text-foreground mt-1">{stat.value}</p>
              </div>
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-muted">
                <stat.icon className={`h-5 w-5 ${stat.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Link
          to="/teacher/classes"
          className="flex items-center justify-between rounded-2xl border border-border bg-card p-5 shadow-sm hover:border-primary/30 hover:shadow-md transition-all group"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
              <BookOpen className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="font-semibold text-foreground">Manage Classes</p>
              <p className="text-xs text-muted-foreground">Create and view your classes</p>
            </div>
          </div>
          <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
        </Link>
        <Link
          to="/teacher/sessions/create"
          className="flex items-center justify-between rounded-2xl border border-primary/30 bg-primary/5 p-5 shadow-sm hover:bg-primary/10 transition-all group"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/20">
              <CalendarPlus className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="font-semibold text-foreground">New Session</p>
              <p className="text-xs text-muted-foreground">Start an attendance session</p>
            </div>
          </div>
          <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
        </Link>
      </div>

      {/* Recent Sessions */}
      <div className="rounded-2xl border border-border bg-card shadow-sm">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h2 className="font-semibold text-foreground">Recent Sessions</h2>
          <Link to="/teacher/sessions" className="text-xs font-medium text-primary hover:underline">
            View All
          </Link>
        </div>
        {sessions.length === 0 ? (
          <EmptyState
            icon={QrCode}
            title="No sessions yet"
            description="Create your first attendance session to get started."
          />
        ) : (
          <div className="divide-y divide-border">
            {sessions.slice(0, 5).map((session) => {
              const cls = classes.find((c) => c.id === session.class_id);
              return (
                <Link
                  key={session.id}
                  to={
                    session.status === 'ACTIVE'
                      ? `/teacher/sessions/${session.id}/active`
                      : `/teacher/sessions/${session.id}/attendance`
                  }
                  className="flex items-center justify-between px-5 py-3.5 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {statusIcon(session.status)}
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        {cls?.name || `Class #${session.class_id}`}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(session.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <span className={statusBadge(session.status)}>{session.status}</span>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
