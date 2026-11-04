import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
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

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      // Modo demo: la contraseña no se comprueba ni se envía.
      await login(username.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ocurrió un error inesperado. Inténtalo de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Entra en PeerSync"
      subtitle="Modo demo: escribe cualquier usuario y contraseña. Si no existe, lo creamos."
    >
      {error && <ErrorState message={error} />}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="username" className="label">Usuario o correo</label>
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
              placeholder="Inventa uno"
              className="field pl-10"
            />
          </div>
        </div>

        <div>
          <label htmlFor="password" className="label">Contraseña</label>
          <div className="relative">
            <Lock className="w-4 h-4 text-muted absolute left-3.5 top-3.5" />
            <input
              id="password"
              type="password"
              autoComplete="off"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="La que quieras"
              className="field pl-10"
            />
          </div>
        </div>

        <button type="submit" disabled={loading} className="btn btn-primary w-full py-3">
          <span>{loading ? 'Entrando...' : 'Entrar'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>
    </AuthShell>
  );
};
