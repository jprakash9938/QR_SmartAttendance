import { useState, useEffect, useRef } from 'react';
import api from '../../services/api';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import EmptyState from '../../components/EmptyState';
import { BookOpen, Plus, FolderOpen } from 'lucide-react';

export default function Classes() {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [newClassName, setNewClassName] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');
  const [uploadClassId, setUploadClassId] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState(null); // { type, text }
  const fileInputRef = useRef(null);

  const fetchClasses = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/classes');
      setClasses(res.data);
    } catch {
      setError('Failed to load classes.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchClasses(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newClassName.trim()) return;
    setCreating(true);
    setCreateError('');
    try {
      const res = await api.post('/classes', { name: newClassName.trim() });
      setClasses((prev) => [res.data, ...prev]);
      setNewClassName('');
      setShowCreate(false);
    } catch (err) {
      setCreateError(err.response?.data?.detail || 'Failed to create class.');
    } finally {
      setCreating(false);
    }
  };

  const handleUploadRoster = async (e, classId) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setUploadClassId(classId);
    setUploadMessage(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post(`/classes/${classId}/roster/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadMessage({ type: 'success', text: res.data.message || 'Roster uploaded successfully!' });
    } catch (err) {
      setUploadMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to upload roster.' });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = ''; // reset input
    }
  };

  if (loading) return <LoadingSpinner size="lg" className="min-h-[60vh]" />;
  if (error) return <ErrorMessage message={error} onRetry={fetchClasses} />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Classes</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage your classes</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          New Class
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="rounded-2xl border border-primary/20 bg-primary/5 p-5 animate-fade-in">
          <h3 className="font-semibold text-foreground mb-3">Create New Class</h3>
          {createError && (
            <div className="mb-3 rounded-xl bg-destructive/10 border border-destructive/20 px-4 py-2.5 text-sm text-destructive">
              {createError}
            </div>
          )}
          <form onSubmit={handleCreate} className="flex gap-3">
            <input
              type="text"
              value={newClassName}
              onChange={(e) => setNewClassName(e.target.value)}
              placeholder="e.g., Computer Science 101"
              className="flex-1 rounded-xl border border-border bg-background px-4 py-2.5 text-sm text-foreground placeholder-muted-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all"
              required
              maxLength={255}
            />
            <button
              type="submit"
              disabled={creating}
              className="rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {creating ? 'Creating...' : 'Create'}
            </button>
            <button
              type="button"
              onClick={() => { setShowCreate(false); setCreateError(''); }}
              className="rounded-xl border border-border px-4 py-2.5 text-sm font-medium text-foreground hover:bg-muted transition-colors"
            >
              Cancel
            </button>
          </form>
        </div>
      )}

      {/* Classes list */}
      {classes.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="No classes yet"
          description="Create your first class to start tracking attendance."
          action={
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Plus className="h-4 w-4" /> Create Class
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 stagger-children">
          {classes.map((cls) => (
            <div
              key={cls.id}
              className="rounded-2xl border border-border bg-card p-5 shadow-sm hover:shadow-md hover:border-primary/20 transition-all"
            >
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 flex-shrink-0">
                  <FolderOpen className="h-5 w-5 text-primary" />
                </div>
                <div className="min-w-0">
                  <h3 className="font-semibold text-foreground truncate">{cls.name}</h3>
                  <p className="text-xs text-muted-foreground mt-1">
                    Created {new Date(cls.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-border flex items-center justify-between">
                <p className="text-xs text-muted-foreground">
                  Class ID: <span className="font-mono font-medium text-foreground">{cls.id}</span>
                </p>
                <div className="flex flex-col items-end">
                  <label className={`text-xs cursor-pointer px-2 py-1 rounded bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors ${(uploading && uploadClassId === cls.id) ? 'opacity-50 pointer-events-none' : ''}`}>
                    {uploading && uploadClassId === cls.id ? 'Uploading...' : 'Upload CSV Roster'}
                    <input 
                      type="file" 
                      accept=".csv" 
                      className="hidden" 
                      onChange={(e) => handleUploadRoster(e, cls.id)}
                      ref={fileInputRef}
                    />
                  </label>
                  {uploadMessage && uploadClassId === cls.id && (
                    <p className={`text-[10px] mt-1 ${uploadMessage.type === 'success' ? 'text-green-500' : 'text-destructive'}`}>
                      {uploadMessage.text}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
