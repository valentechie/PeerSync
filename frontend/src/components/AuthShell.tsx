import React from 'react';
import logoFull from '../assets/logo-full.png';

export const AuthShell: React.FC<{
  title: string;
  subtitle: string;
  children: React.ReactNode;
}> = ({ title, subtitle, children }) => (
  <main className="min-h-screen flex items-center justify-center p-4">
    <div className="page max-w-md py-0! px-0!">
      <div className="auth-card p-6 sm:p-8 space-y-6">
        <div className="text-center space-y-2">
          {/* Placa blanca: el azul marino del logo no se distingue sobre el tema oscuro. */}
          <span className="inline-block rounded-2xl bg-white p-3">
            <img src={logoFull} alt="PeerSync" className="block h-28 w-auto" />
          </span>
          <h1 className="text-2xl font-extrabold text-ink">{title}</h1>
          <p className="text-sm text-muted">{subtitle}</p>
        </div>
        {children}
      </div>
      <p className="text-center text-xs font-bold uppercase tracking-widest text-muted mt-5">Hack4Edu 2026</p>
    </div>
  </main>
);
