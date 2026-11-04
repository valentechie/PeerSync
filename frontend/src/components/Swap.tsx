import React from 'react';
import { Sparkles } from 'lucide-react';

export const SwapMark: React.FC<{ className?: string }> = ({ className = 'w-11 h-11' }) => (
  <span className={`brand-tile ${className}`} aria-hidden="true">
    <Sparkles className="w-3/5 h-3/5" />
  </span>
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
