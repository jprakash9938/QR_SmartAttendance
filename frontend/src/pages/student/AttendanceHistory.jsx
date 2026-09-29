import { useState, useEffect } from 'react';
import api from '../../services/api';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import EmptyState from '../../components/EmptyState';
import {
  History,
  CheckCircle2,
  Clock,
  ChevronLeft,
  ChevronRight,
  Calendar,
  BookOpen,
} from 'lucide-react';

export default function AttendanceHistory() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const fetchHistory = async (p = page) => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/student/attendance', {
        params: { page: p, page_size: pageSize },
      });
      setData(res.data);
    } catch {
      setError('Failed to load attendance history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchHistory(page); }, [page]);

  if (loading) return <LoadingSpinner size="lg" className="min-h-[60vh]" />;
  if (error) return <ErrorMessage message={error} onRetry={() => fetchHistory(page)} />;

  const items = data?.items || [];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <History className="h-6 w-6 text-primary" />
          Attendance History
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          {data?.total || 0} total record{(data?.total || 0) !== 1 ? 's' : ''}
        </p>
      </div>

      {/* List */}
      {items.length === 0 ? (
        <EmptyState
          icon={History}
          title="No attendance records"
          description="Your attendance history will appear here after you scan a QR code."
        />
      ) : (
        <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
          <div className="divide-y divide-border">
            {items.map((record) => (
              <div
                key={record.id}
                className="flex items-center justify-between px-5 py-4 hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-green-500/10 flex-shrink-0">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground flex items-center gap-1.5">
                      <BookOpen className="h-3.5 w-3.5 text-muted-foreground" />
                      {record.class_name || `Session #${record.session_id}`}
                    </p>
                    <div className="flex items-center gap-3 mt-0.5">
                      <p className="text-xs text-muted-foreground flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(record.marked_at).toLocaleDateString()}
                      </p>
                      <p className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(record.marked_at).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1 rounded-full bg-green-500/10 border border-green-500/20 px-2.5 py-0.5 text-xs font-medium text-green-600">
                  {record.status}
                </span>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between px-5 py-3.5 border-t border-border bg-muted/30">
              <p className="text-xs text-muted-foreground">
                Page {data.page} of {data.total_pages}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-background hover:bg-muted disabled:opacity-40 transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                  disabled={page >= data.total_pages}
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-background hover:bg-muted disabled:opacity-40 transition-colors"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
