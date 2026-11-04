import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { ApiError, apiRequest } from '../services/api';

export interface User {
  id: string;
  name: string;
  email: string;
  bio: string;
  studyCode: string | null;
  study: string | null;
  skillsSeeking: string[];
}

export type ProfileChanges = Partial<Pick<User, 'name' | 'bio' | 'studyCode' | 'skillsSeeking'>>;

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  /** true mientras se recupera la sesión guardada al abrir la app. */
  isLoading: boolean;
  /** Modo demo: entra con cualquier usuario, sin comprobar contraseña. */
  login: (username: string) => Promise<void>;
  logout: () => void;
  updateProfile: (changes: ProfileChanges) => Promise<void>;
}

const TOKEN_KEY = 'peersync_token';
const PROFILE_PATH = '/profiles/me';

// sessionStorage: la sesión dura hasta cerrar la pestaña, así que cada visita pide login.
const readToken = (): string | null => {
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
};

const writeToken = (token: string | null) => {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
    // Limpia la sesión que guardaban las versiones anteriores.
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Sin almacenamiento la sesión dura hasta recargar la página.
  }
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(readToken);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(() => readToken() !== null);

  const logout = useCallback(() => {
    writeToken(null);
    setToken(null);
    setUser(null);
  }, []);

  // Recupera la sesión guardada. Si el servidor no responde se conserva el token,
  // para no cerrar la sesión por un fallo temporal.
  useEffect(() => {
    const savedToken = readToken();
    if (!savedToken) return;
    let cancelled = false;
    apiRequest<User>(PROFILE_PATH, { token: savedToken })
      .then(profile => {
        if (!cancelled) setUser(profile);
      })
      .catch((error: unknown) => {
        if (!cancelled && error instanceof ApiError && error.status === 401) logout();
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [logout]);

  const login = async (username: string) => {
    const { access_token: newToken } = await apiRequest<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: { email: username },
    });
    const profile = await apiRequest<User>(PROFILE_PATH, { token: newToken });
    writeToken(newToken);
    setToken(newToken);
    setUser(profile);
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
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!user, isLoading, login, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
