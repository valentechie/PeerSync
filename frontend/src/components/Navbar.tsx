import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Home, Users, BookOpen, TrendingUp, User, Settings as SettingsIcon, LogOut, Star } from 'lucide-react';
import { SwapMark } from './Swap';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const navItems = [
    { name: 'Inicio', short: 'Inicio', path: '/dashboard', icon: Home },
    { name: 'Buscar compañeros', short: 'Compañeros', path: '/find-partners', icon: Users },
    { name: 'Mis sesiones', short: 'Sesiones', path: '/my-sessions', icon: BookOpen },
    { name: 'Mi progreso', short: 'Progreso', path: '/my-progress', icon: TrendingUp },
    { name: 'Mi perfil', short: 'Perfil', path: '/my-profile', icon: User },
  ];

  return (
    <header className="sticky top-0 z-50 bg-surface border-b border-line">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          {/* Logo */}
          <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2.5 cursor-pointer rounded-lg shrink-0">
            <SwapMark />
            <span className="font-display text-xl font-semibold text-ink">PeerSync</span>
          </button>

          {/* Navigation Links */}
          <nav className="hidden lg:flex items-center gap-1" aria-label="Principal">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `px-3 py-2 rounded-lg text-sm font-bold whitespace-nowrap transition-colors ${
                    isActive ? 'bg-teach-soft text-teach-strong' : 'text-muted hover:text-ink'
                  }`
                }
              >
                {item.name}
              </NavLink>
            ))}
          </nav>

          {/* User Profile & Settings */}
          <div className="flex items-center gap-1 min-w-0">
            {user && (
              <div className="hidden sm:flex flex-col text-right mr-2 min-w-0">
                <span className="text-sm font-bold text-ink truncate max-w-36">{user.name}</span>
                <span className="text-xs font-semibold text-muted flex items-center justify-end gap-1 whitespace-nowrap">
                  <Star className="w-3 h-3 fill-sun text-sun" />
                  <span>{user.reputation?.toFixed(1) ?? 'Nuevo'}</span>
                  <span aria-hidden="true">·</span>
                  <span>{user.completedSessions} ses.</span>
                </span>
              </div>
            )}
            <button
              onClick={() => navigate('/settings')}
              title="Configuración"
              aria-label="Configuración"
              className="p-2 text-muted hover:text-teach-strong hover:bg-teach-soft rounded-lg transition-colors cursor-pointer"
            >
              <SettingsIcon className="w-5 h-5" />
            </button>
            <button
              onClick={() => { logout(); navigate('/login'); }}
              title="Cerrar sesión"
              aria-label="Cerrar sesión"
              className="p-2 text-muted hover:text-learn-strong hover:bg-learn-soft rounded-lg transition-colors cursor-pointer"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation bar */}
      <nav className="lg:hidden grid grid-cols-5 border-t border-line px-1 py-1" aria-label="Principal móvil">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 py-1.5 rounded-lg text-[11px] font-bold transition-colors ${
                  isActive ? 'bg-teach-soft text-teach-strong' : 'text-muted'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span>{item.short}</span>
            </NavLink>
          );
        })}
      </nav>
    </header>
  );
};
