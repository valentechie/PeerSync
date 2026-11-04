import React from 'react';
import { ArrowLeftRight } from 'lucide-react';

/** Logo: dos personas dentro de un ciclo de enseñar y aprender. */
export const SwapMark: React.FC<{ className?: string }> = ({ className = 'w-9 h-9' }) => (
  <svg viewBox="0 0 48 48" fill="none" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
    <path d="M8 24A16 16 0 0 1 38 16M40.1 8.2 38 16l-7.8-2.1" stroke="var(--color-teach)" />
    <path d="M40 24A16 16 0 0 1 10 32M7.9 39.8 10 32l7.8 2.1" stroke="var(--color-learn)" />
    <circle cx="19" cy="24" r="4" fill="var(--color-teach)" stroke="none" />
    <circle cx="29" cy="24" r="4" fill="var(--color-learn)" stroke="none" />
  </svg>
);

export const Avatar: React.FC<{ name: string; tone?: 'teach' | 'learn'; className?: string }> = ({
  name,
  tone = 'teach',
  className = 'w-12 h-12 text-xl',
}) => (
  <div
    className={`${className} ${tone === 'teach' ? 'bg-teach-soft text-teach-strong' : 'bg-learn-soft text-learn-strong'} shrink-0 rounded-full flex items-center justify-center font-display font-semibold`}
    aria-hidden="true"
  >
    {name.charAt(0).toUpperCase() || 'U'}
  </div>
);

/** Muestra "A ⇄ B" con cada lado del intercambio en su color. */
export const SwapTopic: React.FC<{ topic: string }> = ({ topic }) => {
  const [first, second] = topic.split(' ⇄ ');
  if (!second) return <span>{topic}</span>;
  return (
    <span className="inline-flex flex-wrap items-center gap-x-2">
      <span className="text-teach-strong">{first}</span>
      <ArrowLeftRight className="w-4 h-4 text-muted" role="img" aria-label="a cambio de" />
      <span className="text-learn-strong">{second}</span>
    </span>
  );
};

export const SkillList: React.FC<{ title: string; skills?: string[]; tone: 'teach' | 'learn' }> = ({ title, skills, tone }) => (
  <div>
    <h4 className={`eyebrow font-sans ${tone === 'teach' ? 'text-teach' : 'text-learn'}`}>{title}</h4>
    <div className="flex flex-wrap gap-1.5 mt-2">
      {skills?.length ? skills.map(skill => (
        <span key={skill} className={`chip chip-${tone}`}>{skill}</span>
      )) : <span className="text-sm text-muted">Aún no hay ninguna.</span>}
    </div>
  </div>
);
