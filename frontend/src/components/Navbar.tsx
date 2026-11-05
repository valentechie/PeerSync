import React, { useEffect, useRef, useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BookOpen, Compass, GraduationCap, MessagesSquare, Mic, Share2, Users, User, LogOut } from 'lucide-react';
import { fetchInvitations } from '../services/invitations';
import { Avatar, SwapMark } from './Swap';

const INVITATION_POLL_MS = 15000;

export const Navbar: React.FC = () => {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [invitationCount, setInvitationCount] = useState(0);
  const mobileNavRef = useRef<HTMLElement>(null);

  // En móvil la barra se desplaza de lado: la pestaña activa debe quedar a la vista.
  useEffect(() => {
    mobileNavRef.current?.querySelector('.nav-active')?.scrollIntoView({ block: 'nearest', inline: 'center' });
  }, [pathname]);

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
      <span className="ml-0.5 min-w-4 h-4 px-1 rounded-full bg-sun text-night text-[10px] font-extrabold inline-flex items-center justify-center" aria-label={`${invitationCount} invitations`}>
        {invitationCount}
      </span>
    ) : null;

  const navItems = [
    { name: 'Rooms', short: 'Rooms', path: '/rooms', icon: MessagesSquare },
    { name: 'Classmates', short: 'Peers', path: '/classmates', icon: GraduationCap },
    { name: 'Friends', short: 'Friends', path: '/friends', icon: Users },
    { name: 'My network', short: 'Network', path: '/network', icon: Share2 },
    { name: 'Discover', short: 'Discover', path: '/discover', icon: Compass },
    { name: 'Learn', short: 'Learn', path: '/learn', icon: BookOpen },
    { name: 'Practice', short: 'Practice', path: '/practice', icon: Mic },
    { name: 'My profile', short: 'Profile', path: '/my-profile', icon: User },
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
          <nav className="hidden xl:flex items-center gap-1 bg-paper/70 p-1.5 rounded-2xl border border-line" aria-label="Main">
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
              <button onClick={() => navigate('/my-profile')} className="flex items-center gap-2 mr-2 min-w-0 cursor-pointer rounded-lg" aria-label="Go to my profile">
                <Avatar name={user.name} photoUrl={user.photoUrl} className="w-8 h-8 text-sm" />
                <span className="hidden sm:block text-sm font-bold text-ink truncate max-w-36">{user.name}</span>
              </button>
            )}
            <button
              onClick={() => { logout(); navigate('/login'); }}
              title="Log out"
              aria-label="Log out"
              className="p-2 text-muted hover:text-learn-strong hover:bg-learn-soft rounded-lg transition-colors cursor-pointer"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation bar */}
      <nav ref={mobileNavRef} className="xl:hidden flex overflow-x-auto border-t border-line px-0.5 py-1" aria-label="Main mobile">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex-1 shrink-0 min-w-16 flex flex-col items-center gap-0.5 py-1.5 rounded-lg text-[11px] tracking-tight font-bold transition-colors ${
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
