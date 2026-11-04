import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ErrorState } from '../components/UIStates';
import { AuthShell } from '../components/AuthShell';
import { GoogleSignInButton } from '../components/GoogleSignInButton';

export const Login: React.FC = () => {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { loginWithGoogle } = useAuth();
  const navigate = useNavigate();

  const handleCredential = async (credential: string) => {
    setError('');
    setLoading(true);
    try {
      await loginWithGoogle(credential);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ocurrió un error inesperado. Inténtalo de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Entra en PeerSync"
      subtitle="Usa tu cuenta de Google. Si es tu primera vez, crearemos tu cuenta automáticamente."
    >
      {error && <ErrorState message={error} />}

      <div className={loading ? 'opacity-50 pointer-events-none' : undefined} aria-busy={loading}>
        <GoogleSignInButton onCredential={handleCredential} />
      </div>
      {loading && <p role="status" className="text-sm text-muted">Iniciando sesión...</p>}
    </AuthShell>
  );
};
