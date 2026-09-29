import { useState, useEffect, useRef } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import api from '../../services/api';
import {
  ScanLine,
  CheckCircle2,
  XCircle,
  Camera,
  RefreshCw,
  Loader2,
  Info,
} from 'lucide-react';

export default function ScanQR() {
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null); // { success, message }
  const [submitting, setSubmitting] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const scannerRef = useRef(null);
  const containerRef = useRef(null);

  const startScanner = async () => {
    setResult(null);
    setCameraError('');
    setScanning(true);

    // Wait for React to render the div#qr-reader
    setTimeout(async () => {
      try {
        const scanner = new Html5Qrcode('qr-reader');
        scannerRef.current = scanner;

        const config = {
          fps: 10,
          qrbox: { width: 250, height: 250 },
          aspectRatio: 1.0,
        };

        let isProcessing = false;
        const handleSuccess = async (decodedText) => {
          if (isProcessing) return;
          isProcessing = true;
          
          // Stop scanner immediately so it doesn't fire again while we process
          stopScanner();
          
          await handleScan(decodedText);
        };

        try {
          // Try back camera first
          await scanner.start({ facingMode: 'environment' }, config, handleSuccess, () => {});
        } catch (err1) {
          // Fallback to front camera or default camera
          console.warn('Environment camera failed, falling back to user camera', err1);
          await scanner.start({ facingMode: 'user' }, config, handleSuccess, () => {});
        }
      } catch (err) {
        console.error('Camera error:', err);
        let errorMsg = 'Camera error: ';
        
        if (typeof err === 'string') {
          errorMsg += err;
        } else if (err instanceof Error) {
          errorMsg += err.message || err.name;
        } else {
          errorMsg += JSON.stringify(err);
        }
        
        if (!window.isSecureContext) {
          errorMsg += ' (Note: Camera requires HTTPS or localhost)';
        }
        
        setCameraError(errorMsg);
        setScanning(false);
      }
    }, 100);
  };

  const stopScanner = async () => {
    try {
      if (scannerRef.current?.isScanning) {
        await scannerRef.current.stop();
      }
    } catch {
      // Ignore cleanup errors
    }
    setScanning(false);
  };

  const handleScan = async (decodedText) => {
    setSubmitting(true);
    try {
      let data;
      try {
        data = JSON.parse(decodedText);
      } catch {
        setResult({ success: false, message: 'Invalid QR code format.' });
        setSubmitting(false);
        return;
      }

      if (!data.session_id || !data.token) {
        setResult({ success: false, message: 'Invalid QR code: missing session or token.' });
        setSubmitting(false);
        return;
      }

      const res = await api.post('/attendance/mark', {
        session_id: data.session_id,
        token: data.token,
      });

      setResult({
        success: res.data.success,
        message: res.data.message,
        markedAt: res.data.marked_at,
      });
    } catch (err) {
      const message = err.response?.data?.detail || err.response?.data?.message || 'Failed to mark attendance.';
      setResult({ success: false, message });
    } finally {
      setSubmitting(false);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (scannerRef.current?.isScanning) {
        scannerRef.current.stop().catch(() => {});
      }
    };
  }, []);

  const reset = () => {
    setResult(null);
    setCameraError('');
  };

  return (
    <div className="max-w-lg mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <ScanLine className="h-6 w-6 text-primary" />
          Scan QR Code
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Point your camera at the QR code displayed by your teacher.
        </p>
      </div>

      {/* Info banner */}
      <div className="flex items-start gap-3 rounded-2xl border border-primary/20 bg-primary/5 px-4 py-3.5">
        <Info className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
        <p className="text-xs text-muted-foreground">
          The QR code refreshes every 5 seconds. Position your camera steadily for the best results.
        </p>
      </div>

      {/* Result Display */}
      {result && (
        <div className={`rounded-2xl border p-6 text-center animate-fade-in ${
          result.success
            ? 'border-green-500/20 bg-green-500/5'
            : 'border-destructive/20 bg-destructive/5'
        }`}>
          {result.success ? (
            <>
              <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto mb-3" />
              <h3 className="text-lg font-bold text-foreground">Attendance Marked!</h3>
              <p className="text-sm text-muted-foreground mt-1">{result.message}</p>
              {result.markedAt && (
                <p className="text-xs text-muted-foreground mt-2">
                  Recorded at {new Date(result.markedAt).toLocaleTimeString()}
                </p>
              )}
            </>
          ) : (
            <>
              <XCircle className="h-16 w-16 text-destructive mx-auto mb-3" />
              <h3 className="text-lg font-bold text-foreground">Unable to Mark</h3>
              <p className="text-sm text-muted-foreground mt-1">{result.message}</p>
            </>
          )}
          <button
            onClick={reset}
            className="mt-4 flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground mx-auto hover:bg-primary/90 transition-colors"
          >
            <RefreshCw className="h-4 w-4" /> Scan Again
          </button>
        </div>
      )}

      {/* Scanner area */}
      {!result && (
        <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
          {scanning ? (
            <div className="relative">
              <div id="qr-reader" ref={containerRef} className="w-full" />
              <button
                onClick={stopScanner}
                className="absolute top-3 right-3 rounded-lg bg-black/60 px-3 py-1.5 text-xs font-medium text-white backdrop-blur-sm hover:bg-black/80 transition-colors"
              >
                Stop
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center py-16 px-6">
              {cameraError ? (
                <>
                  <XCircle className="h-12 w-12 text-destructive mb-3" />
                  <p className="text-sm text-destructive text-center mb-4">{cameraError}</p>
                </>
              ) : submitting ? (
                <>
                  <Loader2 className="h-12 w-12 text-primary animate-spin mb-3" />
                  <p className="text-sm text-muted-foreground">Marking attendance...</p>
                </>
              ) : (
                <>
                  <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-primary/10 mb-4">
                    <Camera className="h-10 w-10 text-primary" />
                  </div>
                  <p className="text-sm text-muted-foreground text-center mb-5">
                    Tap the button below to open your camera and scan the QR code.
                  </p>
                </>
              )}
              {!submitting && (
                <button
                  onClick={startScanner}
                  className="flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/20 hover:bg-primary/90 transition-colors"
                >
                  <Camera className="h-4 w-4" />
                  {cameraError ? 'Try Again' : 'Open Camera'}
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
