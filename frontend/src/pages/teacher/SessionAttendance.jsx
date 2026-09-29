import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../../services/api';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import EmptyState from '../../components/EmptyState';
import { Users, ArrowLeft, CheckCircle2, Clock, Mail } from 'lucide-react';

export default function SessionAttendance() {
  const { sessionId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get(`/teacher/sessions/${sessionId}/attendance`);
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load attendance data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [sessionId]);

  if (loading) return <LoadingSpinner size="lg" className="min-h-[60vh]" />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/teacher/sessions"
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-border hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-4 w-4 text-foreground" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Session Attendance</h1>
          <p className="text-sm text-muted-foreground">
            {data?.class_name} — {data?.total_count} student{data?.total_count !== 1 ? 's' : ''} recorded
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={async () => {
              try {
                const res = await api.get(`/teacher/sessions/${sessionId}/export`, { responseType: 'blob' });
                const url = window.URL.createObjectURL(new Blob([res.data]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', `attendance_session_${sessionId}.csv`);
                document.body.appendChild(link);
                link.click();
                link.remove();
              } catch (err) {
                console.error("Failed to download CSV", err);
              }
            }}
            className="flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
          >
            Download CSV
          </button>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-green-500/10">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{data?.total_count || 0}</p>
              <p className="text-xs text-muted-foreground">Students Present</p>
            </div>
          </div>
        </div>
        <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
              <Users className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">#{data?.session_id}</p>
              <p className="text-xs text-muted-foreground">Session ID</p>
            </div>
          </div>
        </div>
      </div>

      {/* Student List */}
      <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-border">
          <h2 className="font-semibold text-foreground">Attendance List</h2>
        </div>
        {(!data?.attendances || data.attendances.length === 0) ? (
          <EmptyState icon={Users} title="No attendance records" description="No students have marked their attendance for this session." />
        ) : (
          <div className="divide-y divide-border">
            {data.attendances.map((record, index) => (
              <div key={`${record.student_id}-${index}`} className="flex items-center justify-between px-5 py-3.5 hover:bg-muted/30 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary font-semibold text-sm">
                    {record.student_name?.charAt(0)?.toUpperCase() || '?'}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">{record.student_name}</p>
                    <p className="text-xs text-muted-foreground flex items-center gap-1">
                      <Mail className="h-3 w-3" />
                      {record.student_email}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs font-medium text-green-600 flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" /> {record.status}
                  </p>
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(record.marked_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
