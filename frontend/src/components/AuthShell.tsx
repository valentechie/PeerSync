import React from 'react';
import { SwapMark } from './Swap';

const STEPS = [
  'Enseñas lo que ya dominas.',
  'Aprendes de quien acaba de entender lo que te falta.',
  'Lo explicas con tus palabras para comprobar que lo entendiste.',
];

export const AuthShell: React.FC<{
  title: string;
  subtitle: string;
  footer: React.ReactNode;
  children: React.ReactNode;
}> = ({ title, subtitle, footer, children }) => (
  <div className="min-h-screen grid lg:grid-cols-2">
    <aside className="hidden lg:flex flex-col justify-between bg-teach-strong text-white p-12 xl:p-16">
      <div className="flex items-center gap-3">
        <span className="bg-surface rounded-xl p-1.5">
          <SwapMark className="w-8 h-8" />
        </span>
        <span className="font-display text-2xl font-semibold">Swap4Edu</span>
      </div>

      <div className="space-y-8 max-w-lg">
        <p className="font-display text-5xl font-medium leading-tight">
          Enseñar es la mejor forma de <span className="text-sun">aprender</span>.
        </p>
        <ol className="space-y-4">
          {STEPS.map((step, i) => (
            <li key={step} className="flex items-start gap-3 text-teach-soft">
              <span className="font-display text-sun text-lg leading-6 w-5 shrink-0">{i + 1}.</span>
              <span className="leading-6">{step}</span>
            </li>
          ))}
        </ol>
      </div>

      <p className="text-sm text-teach-soft">Hack4Edu 2026</p>
    </aside>

    <main className="flex items-center justify-center p-4 sm:p-8">
      <div className="page max-w-md py-8! px-0! space-y-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2 lg:hidden mb-6">
            <SwapMark className="w-8 h-8" />
            <span className="font-display text-xl font-semibold">Swap4Edu</span>
          </div>
          <h1 className="page-title">{title}</h1>
          <p className="text-muted">{subtitle}</p>
        </div>
        {children}
        <p className="text-sm text-muted">{footer}</p>
      </div>
    </main>
  </div>
);
