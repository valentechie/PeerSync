import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { AuthError, Session } from '@supabase/supabase-js';
import { ApiError, apiRequest } from '../services/api';
import { supabase } from '../services/supabase';

export interface User {
  id: string;
  name: string;
  email: string;
  bio: string;
  skillsOffering: string[];
  skillsSeeking: string[];
  /** null hasta recibir la primera valoración de un compañero. */
  reputation: number | null;
  completedSessions: number;
}

export type ProfileChanges = Partial<Pick<User, 'name' | 'bio' | 'skillsOffering' | 'skillsSeeking'>>;

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  /** true mientras se recupera la sesión guardada al abrir la app. */
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  /** Devuelve true si la cuenta debe confirmarse por correo antes de entrar. */
  register: (name: string, email: string, password: string) => Promise<boolean>;
  logout: () => void;
  updateProfile: (changes: ProfileChanges) => Promise<void>;
}

const PROFILE_PATH = '/profiles/me';

const AUTH_ERROR_MESSAGES: Record<string, string> = {
  invalid_credentials: 'Email o contraseña incorrectos.',
  email_not_confirmed: 'Confirma tu cuenta con el enlace que te enviamos por correo.',
  user_already_exists: 'Ya existe una cuenta con este correo.',
  email_exists: 'Ya existe una cuenta con este correo.',
  weak_password: 'La contraseña es demasiado débil. Prueba con una más larga.',
  email_address_invalid: 'El correo electrónico no es válido.',
  signup_disabled: 'El registro está desactivado en este momento.',
  over_email_send_rate_limit: 'Se han enviado demasiados correos. Inténtalo de nuevo más tarde.',
  over_request_rate_limit: 'Demasiados intentos. Espera un momento y vuelve a intentarlo.',
};

const authError = (error: AuthError) =>
  new Error(
    (error.code && AUTH_ERROR_MESSAGES[error.code]) ||
      (error.status ? 'No se pudo completar la operación. Inténtalo de nuevo.' : 'No se pudo conectar con el servidor. Inténtalo de nuevo.'),
  );

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    void supabase.auth.signOut({ scope: 'local' });
  }, []);

  // Recupera la sesión guardada. Si el servidor no responde se conserva la sesión,
  // para no cerrarla por un fallo temporal.
  useEffect(() => {
    let cancelled = false;
    const restore = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session || cancelled) return;
      setToken(session.access_token);
      try {
        const profile = await apiRequest<User>(PROFILE_PATH, { token: session.access_token });
        if (!cancelled) setUser(profile);
      } catch (error) {
        if (!cancelled && error instanceof ApiError && error.status === 401) logout();
      }
    };
    restore().finally(() => {
      if (!cancelled) setIsLoading(false);
    });

    // Supabase renueva el token por su cuenta; aquí solo se mantiene al día.
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_OUT') {
        setToken(null);
        setUser(null);
      } else if (session) {
        setToken(session.access_token);
      }
    });
    return () => {
      cancelled = true;
      subscription.unsubscribe();
    };
  }, [logout]);

  const startSession = async (session: Session) => {
    try {
      const profile = await apiRequest<User>(PROFILE_PATH, { token: session.access_token });
      setToken(session.access_token);
      setUser(profile);
    } catch (error) {
      await supabase.auth.signOut({ scope: 'local' });
      throw error;
    }
  };

  const login = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw authError(error);
    await startSession(data.session);
  };

  const register = async (name: string, email: string, password: string) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { name }, emailRedirectTo: `${window.location.origin}/login` },
    });
    if (error) throw authError(error);
    if (!data.session) return true;
    await startSession(data.session);
    return false;
  };

  const updateProfile = async (changes: ProfileChanges) => {
    try {
      const profile = await apiRequest<User>(PROFILE_PATH, { method: 'PATCH', body: changes, token: token ?? undefined });
      setUser(profile);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) logout();
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!user, isLoading, login, register, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
