import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ArrowRight, Lock, Mail, User } from 'lucide-react';
import { ErrorState } from '../components/UIStates';
import { AuthShell } from '../components/AuthShell';

export const Register: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !password) {
      setError('Por favor, completa todos los campos.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await register(name, email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ocurrió un error inesperado. Inténtalo de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Únete a Swap4Edu"
      subtitle="Comienza a intercambiar conocimientos con otros estudiantes."
      footer={
        <>
          ¿Ya tienes una cuenta?{' '}
          <Link to="/login" className="font-bold text-teach underline underline-offset-2 hover:text-teach-strong">
            Inicia sesión
          </Link>
        </>
      }
    >
      {error && <ErrorState message={error} />}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="name" className="label">Nombre completo</label>
          <div className="relative">
            <User className="w-4 h-4 text-muted absolute left-3.5 top-3.5" />
            <input
              id="name"
              type="text"
              required
              autoComplete="name"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Tu nombre"
              className="field pl-10"
            />
          </div>
        </div>

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
              autoComplete="new-password"
              minLength={8}
              aria-describedby="password-help"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              className="field pl-10"
            />
          </div>
          <p id="password-help" className="text-xs text-muted mt-1.5">Mínimo 8 caracteres.</p>
        </div>

        <button type="submit" disabled={loading} className="btn btn-primary w-full py-3">
          <span>{loading ? 'Creando cuenta...' : 'Registrarse'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>
    </AuthShell>
  );
};
