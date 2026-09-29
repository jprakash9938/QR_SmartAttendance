import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import EmptyState from '../../components/EmptyState';
import {
  QrCode,
  PlayCircle,
  CheckCircle2,
  Clock,
  CalendarPlus,
  Users,
  ArrowRight,
} from 'lucide-react';

export default function Sessions() {
  const [sessions, setSessions] = useState([]);
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const [sessRes, clsRes] = await Promise.all([
        api.get('/teacher/sessions'),
        api.get('/classes'),
      ]);
      setSessions(sessRes.data);
      setClasses(clsRes.data);
    } catch {
      setError('Failed to load sessions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) return <LoadingSpinner size="lg" className="min-h-[60vh]" />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

  const statusConfig = {
    ACTIVE: { color: 'bg-green-500/10 text-green-600 border-green-500/20', icon: PlayCircle },
    COMPLETED: { color: 'bg-muted text-muted-foreground border-border', icon: CheckCircle2 },
    PENDING: { color: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20', icon: Clock },
  };

  const getClassName = (classId) => classes.find((c) => c.id === classId)?.name || `Class #${classId}`;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Sessions</h1>
          <p className="text-sm text-muted-foreground mt-1">All your attendance sessions</p>
        </div>
        <Link
          to="/teacher/sessions/create"
          className="flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
        >
          <CalendarPlus className="h-4 w-4" /> New Session
        </Link>
      </div>

      {sessions.length === 0 ? (
        <EmptyState
          icon={QrCode}
          title="No sessions yet"
          description="Create your first attendance session."
          action={
            <Link
              to="/teacher/sessions/create"
              className="flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <CalendarPlus className="h-4 w-4" /> Create Session
            </Link>
          }
        />
      ) : (
        <div className="space-y-3 stagger-children">
          {sessions.map((session) => {
            const cfg = statusConfig[session.status] || statusConfig.PENDING;
            const StatusIcon = cfg.icon;
            const link = session.status === 'ACTIVE'
              ? `/teacher/sessions/${session.id}/active`
              : `/teacher/sessions/${session.id}/attendance`;

            return (
              <Link
                key={session.id}
                to={link}
                className="flex items-center justify-between rounded-2xl border border-border bg-card p-5 shadow-sm hover:border-primary/20 hover:shadow-md transition-all group"
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10">
                    <QrCode className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-semibold text-foreground">{getClassName(session.class_id)}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {new Date(session.created_at).toLocaleDateString()} · Session #{session.id}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${cfg.color}`}>
                    <StatusIcon className="h-3.5 w-3.5" />
                    {session.status}
                  </span>
                  <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
