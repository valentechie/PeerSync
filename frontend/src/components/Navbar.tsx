import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Users, BookOpen, TrendingUp, User, Settings as SettingsIcon, LogOut, Sparkles } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const navItems = [
    { name: 'Inicio', path: '/dashboard', icon: Sparkles },
    { name: 'Buscar compañeros', path: '/find-partners', icon: Users },
    { name: 'Mis sesiones', path: '/my-sessions', icon: BookOpen },
    { name: 'Mi progreso', path: '/my-progress', icon: TrendingUp },
    { name: 'Mi perfil', path: '/my-profile', icon: User },
  ];

  return (
    <header className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-2xl border-b border-slate-800 shadow-2xl transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <div className="flex items-center space-x-3 cursor-pointer group" onClick={() => navigate('/dashboard')}>
            <div className="w-12 h-12 bg-gradient-to-tr from-indigo-600 via-violet-600 to-fuchsia-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-500/30 group-hover:scale-105 transition-transform border border-indigo-400/30">
              <Sparkles className="w-6 h-6 text-white animate-pulse" />
            </div>
            <div>
              <span className="text-2xl font-black bg-gradient-to-r from-indigo-400 via-violet-400 to-fuchsia-400 bg-clip-text text-transparent tracking-tight">
                Swap4Edu
              </span>
              <span className="block text-[10px] uppercase font-bold text-indigo-400/70 tracking-widest">Hack4Edu 2026</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1.5 bg-slate-950/70 p-2 rounded-2xl border border-slate-800 shadow-inner">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all duration-200 ${
                      isActive
                        ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-600/30 scale-105'
                        : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/60'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* User Profile & Settings */}
          <div className="flex items-center space-x-3">
            {user && (
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-sm font-bold text-slate-200">{user.name}</span>
                <span className="text-xs font-medium text-indigo-400 flex items-center justify-end space-x-1.5">
                  <span>⭐ {user.reputation}</span>
                  <span className="text-slate-600">•</span>
                  <span>{user.completedSessions} ses.</span>
                </span>
              </div>
            )}
            <button
              onClick={() => navigate('/settings')}
              title="Configuración"
              className="p-2.5 text-slate-400 hover:text-indigo-400 hover:bg-slate-800/80 rounded-xl transition-colors border border-transparent hover:border-slate-700"
            >
              <SettingsIcon className="w-5 h-5" />
            </button>
            <button
              onClick={() => { logout(); navigate('/login'); }}
              title="Cerrar sesión"
              className="p-2.5 text-slate-400 hover:text-rose-400 hover:bg-rose-950/50 rounded-xl transition-colors border border-transparent hover:border-rose-900/50"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation bar */}
      <div className="md:hidden flex items-center justify-around border-t border-slate-800 bg-slate-900/95 backdrop-blur-md py-2.5 px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex flex-col items-center p-2 rounded-xl text-[11px] font-bold transition ${
                  isActive ? 'text-indigo-400 bg-indigo-950/60 border border-indigo-800/50' : 'text-slate-400 hover:text-slate-100'
                }`
              }
            >
              <Icon className="w-4 h-4 mb-1" />
              <span>{item.name.split(' ')[0]}</span>
            </NavLink>
          );
        })}
      </div>
    </header>
  );
};
