import React, { useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ArrowRight, Lock, User } from 'lucide-react';
import { ErrorState } from '../components/UIStates';
import { AuthShell } from '../components/AuthShell';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const location = useLocation();

  // Vuelve a la página pedida: así funcionan los enlaces de invitación a una sala.
  if (isAuthenticated) return <Navigate to={location.state?.from ?? '/rooms'} replace />;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      // Modo demo: la contraseña no se comprueba ni se envía.
      await login(username.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Log in to PeerSync"
      subtitle="Demo mode: type any username and password. If it doesn't exist, we'll create it."
    >
      {error && <ErrorState message={error} />}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="username" className="label">Username or email</label>
          <div className="relative">
            <User className="w-4 h-4 text-muted absolute left-3.5 top-3.5" />
            <input
              id="username"
              type="text"
              required
              maxLength={320}
              autoComplete="username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Make one up"
              className="field pl-10"
            />
          </div>
        </div>

        <div>
          <label htmlFor="password" className="label">Password</label>
          <div className="relative">
            <Lock className="w-4 h-4 text-muted absolute left-3.5 top-3.5" />
            <input
              id="password"
              type="password"
              autoComplete="off"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Whatever you like"
              className="field pl-10"
            />
          </div>
        </div>

        <button type="submit" disabled={loading} className="btn btn-primary w-full py-3">
          <span>{loading ? 'Logging in...' : 'Log in'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>
    </AuthShell>
  );
};
