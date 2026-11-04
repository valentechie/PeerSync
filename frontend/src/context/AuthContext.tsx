import React, { createContext, useContext, useState, useEffect } from 'react';

export interface User {
  id: string;
  name: string;
  email: string;
  bio: string;
  skillsOffering: string[];
  skillsSeeking: string[];
  reputation: number;
  completedSessions: number;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, pass: string) => Promise<boolean>;
  register: (name: string, email: string, pass: string) => Promise<boolean>;
  logout: () => void;
  updateProfile: (updatedData: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('skillswap_user');
    if (saved) {
      try { return JSON.parse(saved); } catch { return null; }
    }
    // Default demo user for seamless evaluation
    return {
      id: 'u-1',
      name: 'Alex Developer',
      email: 'alex@hack4edu.org',
      bio: 'Estudiante de Ingeniería de Software apasionado por React, Python y Algoritmos.',
      skillsOffering: ['React', 'TypeScript', 'Python'],
      skillsSeeking: ['Machine Learning', 'PostgreSQL', 'Docker'],
      reputation: 4.9,
      completedSessions: 12
    };
  });

  useEffect(() => {
    if (user) {
      localStorage.setItem('skillswap_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('skillswap_user');
    }
  }, [user]);

  const login = async (email: string, _pass: string): Promise<boolean> => {
    setUser({
      id: 'u-1',
      name: email.split('@')[0] || 'Estudiante Swap4Edu',
      email,
      bio: 'Apasionado por el aprendizaje colaborativo e inteligencia artificial.',
      skillsOffering: ['React', 'JavaScript'],
      skillsSeeking: ['Python', 'FastAPI'],
      reputation: 4.8,
      completedSessions: 8
    });
    return true;
  };

  const register = async (name: string, email: string, _pass: string): Promise<boolean> => {
    setUser({
      id: 'u-' + Date.now(),
      name,
      email,
      bio: 'Nuevo miembro en Swap4Edu.',
      skillsOffering: ['TypeScript'],
      skillsSeeking: ['React'],
      reputation: 5.0,
      completedSessions: 0
    });
    return true;
  };

  const logout = () => {
    setUser(null);
  };

  const updateProfile = (updatedData: Partial<User>) => {
    setUser(prev => prev ? { ...prev, ...updatedData } : null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, register, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
