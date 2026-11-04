import React, { useEffect, useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BookOpen, GraduationCap, MessagesSquare, Mic, Users, User, LogOut } from 'lucide-react';
import { fetchInvitations } from '../services/invitations';
import { SwapMark } from './Swap';

const INVITATION_POLL_MS = 15000;

export const Navbar: React.FC = () => {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [invitationCount, setInvitationCount] = useState(0);

  useEffect(() => {
    if (!token) return;
    const load = () => {
      fetchInvitations(token)
        .then(invitations => setInvitationCount(invitations.length))
        .catch(() => undefined);
    };
    load();
    const timer = setInterval(load, INVITATION_POLL_MS);
    return () => clearInterval(timer);
  }, [token, pathname]);

  const badge = (path: string) =>
    path === '/rooms' && invitationCount > 0 ? (
      <span className="ml-0.5 min-w-4 h-4 px-1 rounded-full bg-sun text-night text-[10px] font-extrabold inline-flex items-center justify-center" aria-label={`${invitationCount} invitaciones`}>
        {invitationCount}
      </span>
    ) : null;

  const navItems = [
    { name: 'Salas', short: 'Salas', path: '/rooms', icon: MessagesSquare },
    { name: 'Compañeros', short: 'Compis', path: '/classmates', icon: GraduationCap },
    { name: 'Amigos', short: 'Amigos', path: '/friends', icon: Users },
    { name: 'Aprender', short: 'Aprender', path: '/learn', icon: BookOpen },
    { name: 'Practicar', short: 'Practicar', path: '/practice', icon: Mic },
    { name: 'Mi perfil', short: 'Perfil', path: '/my-profile', icon: User },
  ];

  return (
    <header className="sticky top-0 z-50 bg-surface/80 backdrop-blur-2xl border-b border-line">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20 gap-4">
          {/* Logo */}
          <button onClick={() => navigate('/rooms')} className="flex items-center gap-2.5 cursor-pointer rounded-lg shrink-0">
            <SwapMark />
            <span className="text-left">
              <span className="brand-text block text-2xl leading-7">PeerSync</span>
              <span className="hidden sm:block text-[10px] font-bold uppercase tracking-widest text-teach">Hack4Edu 2026</span>
            </span>
          </button>

          {/* Navigation Links */}
          <nav className="hidden lg:flex items-center gap-1 bg-paper/70 p-1.5 rounded-2xl border border-line" aria-label="Principal">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-colors ${
                      isActive ? 'nav-active' : 'text-muted hover:text-ink'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                  {badge(item.path)}
                </NavLink>
              );
            })}
          </nav>

          {/* User Profile & Settings */}
          <div className="flex items-center gap-1 min-w-0">
            {user && (
              <span className="hidden sm:block mr-2 text-sm font-bold text-ink truncate max-w-36">{user.name}</span>
            )}
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
      <nav className="lg:hidden grid grid-cols-6 border-t border-line px-0.5 py-1" aria-label="Principal móvil">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 py-1.5 rounded-lg text-[11px] tracking-tight font-bold transition-colors ${
                  isActive ? 'nav-active' : 'text-muted'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span className="inline-flex items-center">
                {item.short}
                {badge(item.path)}
              </span>
            </NavLink>
          );
        })}
      </nav>
    </header>
  );
};
