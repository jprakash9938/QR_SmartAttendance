import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import EmptyState from '../../components/EmptyState';
import { CalendarPlus, BookOpen, Clock, ArrowRight, Loader2 } from 'lucide-react';

export default function CreateSession() {
  const navigate = useNavigate();
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedClassId, setSelectedClassId] = useState('');
  const [duration, setDuration] = useState(30);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');

  useEffect(() => {
    const fetchClasses = async () => {
      try {
        const res = await api.get('/classes');
        setClasses(res.data);
        if (res.data.length > 0) setSelectedClassId(String(res.data[0].id));
      } catch {
        setError('Failed to load classes.');
      } finally {
        setLoading(false);
      }
    };
    fetchClasses();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!selectedClassId) return;

    setCreating(true);
    setCreateError('');
    try {
      const res = await api.post('/sessions', {
        class_id: parseInt(selectedClassId, 10),
        duration_minutes: duration,
      });
      // Navigate to the session — start it or view it
      navigate(`/teacher/sessions/${res.data.id}/active`);
    } catch (err) {
      setCreateError(err.response?.data?.detail || 'Failed to create session.');
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <LoadingSpinner size="lg" className="min-h-[60vh]" />;
  if (error) return <ErrorMessage message={error} onRetry={() => window.location.reload()} />;

  return (
    <div className="max-w-xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Create Attendance Session</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Select a class and set the session duration.
        </p>
      </div>

      {classes.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="No classes found"
          description="You need to create a class first before starting an attendance session."
          action={
            <button
              onClick={() => navigate('/teacher/classes')}
              className="flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Create Class <ArrowRight className="h-4 w-4" />
            </button>
          }
        />
      ) : (
        <form onSubmit={handleCreate} className="space-y-5">
          {createError && (
            <div className="rounded-xl bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive animate-fade-in">
              {createError}
            </div>
          )}

          {/* Class selector */}
          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm space-y-3">
            <label className="flex items-center gap-2 text-sm font-semibold text-foreground">
              <BookOpen className="h-4 w-4 text-primary" />
              Select Class
            </label>
            <select
              value={selectedClassId}
              onChange={(e) => setSelectedClassId(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all"
            >
              {classes.map((cls) => (
                <option key={cls.id} value={cls.id}>{cls.name}</option>
              ))}
            </select>
          </div>

          {/* Duration */}
          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm space-y-3">
            <label className="flex items-center gap-2 text-sm font-semibold text-foreground">
              <Clock className="h-4 w-4 text-primary" />
              Duration (minutes)
            </label>
            <input
              type="number"
              value={duration}
              onChange={(e) => setDuration(Math.max(1, Math.min(480, parseInt(e.target.value, 10) || 1)))}
              min={1}
              max={480}
              className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all"
            />
            <div className="flex gap-2 flex-wrap">
              {[15, 30, 45, 60, 90, 120].map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDuration(d)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                    duration === d
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground hover:bg-accent'
                  }`}
                >
                  {d} min
                </button>
              ))}
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={creating || !selectedClassId}
            className="w-full flex items-center justify-center gap-2 rounded-2xl bg-primary py-3.5 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/20 hover:bg-primary/90 disabled:opacity-50 transition-all"
          >
            {creating ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <CalendarPlus className="h-4 w-4" />
            )}
            {creating ? 'Creating Session...' : 'Create & Start Session'}
          </button>
        </form>
      )}
    </div>
  );
}
