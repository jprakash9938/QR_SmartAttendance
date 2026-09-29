import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import api from '../../services/api';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import {
  QrCode,
  Users,
  Clock,
  StopCircle,
  PlayCircle,
  RefreshCw,
  Loader2,
  CheckCircle2,
  Timer,
} from 'lucide-react';

const QR_POLL_INTERVAL = 4000; // Poll slightly before 5s expiry

export default function ActiveSession() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [session, setSession] = useState(null);
  const [qrData, setQrData] = useState(null);
  const [attendance, setAttendance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [countdown, setCountdown] = useState(5);

  const qrTimerRef = useRef(null);
  const countdownRef = useRef(null);
  const mountedRef = useRef(true);

  /* ── Fetch session details ── */
  const fetchSession = useCallback(async () => {
    try {
      const res = await api.get(`/sessions/${sessionId}`);
      if (mountedRef.current) setSession(res.data);
      return res.data;
    } catch (err) {
      if (mountedRef.current) setError('Failed to load session.');
      return null;
    }
  }, [sessionId]);

  /* ── Fetch attendance count ── */
  const fetchAttendance = useCallback(async () => {
    try {
      const res = await api.get(`/teacher/sessions/${sessionId}/attendance/count`);
      if (mountedRef.current) setAttendance(res.data);
    } catch {
      // Non-critical, silently continue
    }
  }, [sessionId]);

  /* ── Fetch QR token ── */
  const fetchQR = useCallback(async () => {
    try {
      const res = await api.get(`/sessions/${sessionId}/qr`);
      if (mountedRef.current) {
        setQrData(res.data);
        setCountdown(5);
      }
    } catch (err) {
      // Session might have ended
      if (err.response?.status === 400 && mountedRef.current) {
        clearInterval(qrTimerRef.current);
        clearInterval(countdownRef.current);
        fetchSession();
      }
    }
  }, [sessionId, fetchSession]);

  /* ── Initial load ── */
  useEffect(() => {
    mountedRef.current = true;
    const init = async () => {
      setLoading(true);
      const sess = await fetchSession();
      await fetchAttendance();
      if (sess?.status === 'ACTIVE') {
        await fetchQR();
      }
      if (mountedRef.current) setLoading(false);
    };
    init();
    return () => { mountedRef.current = false; };
  }, [fetchSession, fetchAttendance, fetchQR]);

  /* ── QR polling ── */
  useEffect(() => {
    if (session?.status !== 'ACTIVE') return;

    qrTimerRef.current = setInterval(() => {
      fetchQR();
      fetchAttendance();
    }, QR_POLL_INTERVAL);

    return () => clearInterval(qrTimerRef.current);
  }, [session?.status, fetchQR, fetchAttendance]);

  /* ── Countdown timer ── */
  useEffect(() => {
    if (session?.status !== 'ACTIVE' || !qrData) return;

    countdownRef.current = setInterval(() => {
      setCountdown((prev) => (prev > 0 ? prev - 1 : 5));
    }, 1000);

    return () => clearInterval(countdownRef.current);
  }, [session?.status, qrData]);

  /* ── Start session ── */
  const handleStart = async () => {
    setActionLoading(true);
    try {
      const res = await api.post(`/sessions/${sessionId}/start`);
      setSession(res.data);
      await fetchQR();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start session.');
    } finally {
      setActionLoading(false);
    }
  };

  /* ── End session ── */
  const handleEnd = async () => {
    setActionLoading(true);
    try {
      clearInterval(qrTimerRef.current);
      clearInterval(countdownRef.current);
      const res = await api.post(`/sessions/${sessionId}/end`);
      setSession(res.data);
      setQrData(null);
      await fetchAttendance();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to end session.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <LoadingSpinner size="lg" className="min-h-[60vh]" />;
  if (error && !session) return <ErrorMessage message={error} onRetry={() => window.location.reload()} />;

  const isActive = session?.status === 'ACTIVE';
  const isPending = session?.status === 'PENDING';
  const isCompleted = session?.status === 'COMPLETED';

  // Build QR data as JSON string for student scanner
  const qrValue = qrData
    ? JSON.stringify({ session_id: qrData.session_id, token: qrData.token })
    : '';

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <QrCode className="h-6 w-6 text-primary" />
            Session #{sessionId}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {session?.class_name || `Class #${session?.class_id}`}
          </p>
        </div>
        <div className="flex gap-3">
          {isPending && (
            <button
              onClick={handleStart}
              disabled={actionLoading}
              className="flex items-center gap-2 rounded-xl bg-green-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {actionLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlayCircle className="h-4 w-4" />}
              Start Session
            </button>
          )}
          {isActive && (
            <button
              onClick={handleEnd}
              disabled={actionLoading}
              className="flex items-center gap-2 rounded-xl bg-destructive px-5 py-2.5 text-sm font-medium text-destructive-foreground shadow-sm hover:bg-destructive/90 disabled:opacity-50 transition-colors"
            >
              {actionLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <StopCircle className="h-4 w-4" />}
              End Session
            </button>
          )}
          {isCompleted && (
            <button
              onClick={() => navigate(`/teacher/sessions/${sessionId}/attendance`)}
              className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Users className="h-4 w-4" /> View Attendance
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-xl bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* QR Code Panel */}
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm flex flex-col items-center">
          {isActive && qrData ? (
            <>
              <div className="mb-4 flex items-center gap-2">
                <div className="h-2.5 w-2.5 rounded-full bg-green-500 animate-pulse" />
                <span className="text-sm font-medium text-green-600">Live — QR refreshes automatically</span>
              </div>

              {/* QR Code */}
              <div className="qr-container rounded-2xl bg-white p-5">
                <QRCodeSVG
                  value={qrValue}
                  size={240}
                  level="M"
                  bgColor="#ffffff"
                  fgColor="#000000"
                />
              </div>

              {/* Countdown */}
              <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
                <Timer className="h-4 w-4" />
                Refreshing in <span className="font-bold text-primary">{countdown}s</span>
              </div>
            </>
          ) : isPending ? (
            <div className="flex flex-col items-center py-12 gap-4">
              <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-muted">
                <QrCode className="h-10 w-10 text-muted-foreground" />
              </div>
              <p className="text-sm text-muted-foreground text-center">
                Start the session to display the QR code.
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center py-12 gap-4">
              <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-muted">
                <CheckCircle2 className="h-10 w-10 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium text-foreground">Session Completed</p>
              <p className="text-sm text-muted-foreground text-center">
                This session has ended. No more attendance can be marked.
              </p>
            </div>
          )}
        </div>

        {/* Session Info Panel */}
        <div className="space-y-4">
          {/* Status Card */}
          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <h3 className="font-semibold text-foreground mb-3">Session Details</h3>
            <div className="space-y-3">
              {[
                { label: 'Status', value: session?.status, icon: isActive ? PlayCircle : isCompleted ? CheckCircle2 : Clock },
                { label: 'Start Time', value: session?.start_time ? new Date(session.start_time).toLocaleString() : '—' },
                { label: 'End Time', value: session?.end_time ? new Date(session.end_time).toLocaleString() : '—' },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between py-1.5">
                  <span className="text-sm text-muted-foreground">{item.label}</span>
                  <span className="text-sm font-medium text-foreground">{item.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Attendance Count */}
          {attendance && (
            <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
              <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                <Users className="h-4 w-4 text-primary" /> Attendance
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-xl bg-green-500/10 p-4 text-center">
                  <p className="text-2xl font-bold text-green-600">{attendance.present_count}</p>
                  <p className="text-xs text-muted-foreground mt-1">Present</p>
                </div>
                <div className="rounded-xl bg-muted p-4 text-center">
                  <p className="text-2xl font-bold text-foreground">{attendance.total_students}</p>
                  <p className="text-xs text-muted-foreground mt-1">Total</p>
                </div>
              </div>
              {isActive && (
                <p className="mt-3 text-xs text-muted-foreground text-center flex items-center justify-center gap-1">
                  <RefreshCw className="h-3 w-3" /> Updates automatically
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
