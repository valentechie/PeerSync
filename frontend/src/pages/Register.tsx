import React, { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ArrowRight, Lock, Mail, User } from 'lucide-react';
import { ErrorState, SuccessState } from '../components/UIStates';
import { AuthShell } from '../components/AuthShell';

const MIN_PASSWORD_LENGTH = 8;

export const Register: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingConfirmation, setPendingConfirmation] = useState(false);
  const { register, isAuthenticated } = useAuth();

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      setPendingConfirmation(await register(name.trim(), email.trim(), password));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ocurrió un error inesperado. Inténtalo de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Únete a PeerSync"
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

      {pendingConfirmation ? (
        <SuccessState
          title="Revisa tu correo"
          message={`Si ${email.trim()} no tiene cuenta todavía, te hemos enviado un enlace para confirmarla. Después podrás iniciar sesión.`}
        />
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="name" className="label">Nombre completo</label>
            <div className="relative">
              <User className="w-4 h-4 text-muted absolute left-3.5 top-3.5" />
              <input
                id="name"
                type="text"
                required
                maxLength={100}
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
                minLength={MIN_PASSWORD_LENGTH}
                aria-describedby="password-help"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="field pl-10"
              />
            </div>
            <p id="password-help" className="text-xs text-muted mt-1.5">Mínimo {MIN_PASSWORD_LENGTH} caracteres.</p>
          </div>

          <button type="submit" disabled={loading} className="btn btn-primary w-full py-3">
            <span>{loading ? 'Creando cuenta...' : 'Registrarse'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>
      )}
    </AuthShell>
  );
};
