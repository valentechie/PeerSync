import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ArrowRight, Lock, Mail } from 'lucide-react';
import { ErrorState } from '../components/UIStates';
import { AuthShell } from '../components/AuthShell';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Por favor, completa todos los campos.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ocurrió un error inesperado. Inténtalo de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Hola de nuevo"
      subtitle="Tus compañeros de estudio te están esperando."
      footer={
        <>
          ¿No tienes una cuenta?{' '}
          <Link to="/register" className="font-bold text-teach underline underline-offset-2 hover:text-teach-strong">
            Regístrate aquí
          </Link>
        </>
      }
    >
      {error && <ErrorState message={error} />}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="label">Correo electrónico</label>
          <div className="relative">
            <Mail className="w-4 h-4 text-muted absolute left-3.5 top-3.5" />
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="tu@correo.com"
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
              required
              autoComplete="current-password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              className="field pl-10"
            />
          </div>
        </div>

        <button type="submit" disabled={loading} className="btn btn-primary w-full py-3">
          <span>{loading ? 'Iniciando sesión...' : 'Ingresar'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>
    </AuthShell>
  );
};
