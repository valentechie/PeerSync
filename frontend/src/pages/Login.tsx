import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Sparkles, ArrowRight, Lock, Mail } from 'lucide-react';
import { ErrorState } from '../components/UIStates';

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
    } catch {
      setError('Credenciales inválidas. Intenta nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 animate-fadeIn">
      <div className="max-w-md w-full bg-slate-900/90 backdrop-blur-2xl border border-slate-800 rounded-3xl shadow-2xl p-8 space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex w-14 h-14 bg-gradient-to-tr from-indigo-600 to-violet-600 rounded-2xl items-center justify-center text-white shadow-lg shadow-indigo-500/30 border border-indigo-400/30">
            <Sparkles className="w-7 h-7 animate-pulse" />
          </div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight">Swap4Edu</h1>
          <p className="text-sm text-slate-400 font-medium">Inicia sesión en tu cuenta de aprendizaje colaborativo</p>
        </div>

        {error && <ErrorState message={error} />}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1">Correo electrónico</label>
            <div className="relative">
              <Mail className="w-5 h-5 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="tu@correo.com"
                className="w-full pl-11 pr-4 py-3 bg-slate-950/80 border border-slate-800 rounded-2xl text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1">Contraseña</label>
            <div className="relative">
              <Lock className="w-5 h-5 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-11 pr-4 py-3 bg-slate-950/80 border border-slate-800 rounded-2xl text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold rounded-2xl text-sm shadow-xl shadow-indigo-600/30 transition-all duration-200 hover:scale-[1.02] flex items-center justify-center space-x-2"
          >
            <span>{loading ? 'Iniciando sesión...' : 'Ingresar'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="text-center text-sm text-slate-400 font-medium">
          ¿No tienes una cuenta?{' '}
          <Link to="/register" className="font-bold text-indigo-400 hover:text-indigo-300 transition-colors">
            Regístrate aquí
          </Link>
        </div>
      </div>
    </div>
  );
};
