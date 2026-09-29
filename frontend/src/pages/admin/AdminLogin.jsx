import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Eye, EyeOff, Loader2 } from 'lucide-react';

export default function AdminLogin() {
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState('');
  const navigate = useNavigate();
  const { adminLogin, loading } = useAuth();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const handleChange = (e) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setFormError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    const result = await adminLogin(formData.email, formData.password);

    if (result.success) {
      navigate('/admin/dashboard', { replace: true });
    } else {
      setFormError(typeof result.error === 'string' ? result.error : 'An error occurred.');
    }
  };

  return (
    <div className="relative w-full h-screen flex items-center justify-center overflow-hidden bg-black text-white font-sans">
      {/* Vignette overlay */}
      <div
        className="absolute inset-0 z-[1] pointer-events-none"
        style={{ background: 'radial-gradient(circle at center, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0) 100%)' }}
      />

      {/* Auth Card */}
      <div className="relative z-[2] w-full max-w-[420px] mx-4 animate-fade-in">
        <div className="rounded-2xl border border-white/10 bg-[#121212]/95 backdrop-blur-xl p-8 shadow-2xl">
          {/* Logo */}
          <div className="flex flex-col items-center mb-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-600 text-white font-bold text-lg mb-3 shadow-lg shadow-purple-600/20">
              AD
            </div>
            <h1 className="text-xl font-bold tracking-tight">
              Admin Portal
            </h1>
            <p className="text-sm text-white/50 mt-1">
              Sign in with your administrator account
            </p>
          </div>

          {/* Error */}
          {formError && (
            <div className="mb-4 rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 animate-fade-in">
              {formError}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-3.5">

            <input
              name="email"
              type="email"
              placeholder="Admin Email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-white/30 outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/30 transition-all"
            />

            <div className="relative">
              <input
                name="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Password"
                value={formData.password}
                onChange={handleChange}
                required
                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 pr-11 text-sm text-white placeholder-white/30 outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/30 transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-purple-600 py-3 text-sm font-semibold text-white transition-all hover:bg-purple-600/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-purple-600/20"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              Access Portal
            </button>
          </form>

        </div>
      </div>
    </div>
  );
}
