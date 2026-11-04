import React, { useState } from 'react';
import { Sparkles } from 'lucide-react';
import { apiAssetUrl } from '../services/api';

export const SwapMark: React.FC<{ className?: string }> = ({ className = 'w-11 h-11' }) => (
  <span className={`brand-tile ${className}`} aria-hidden="true">
    <Sparkles className="w-3/5 h-3/5" />
  </span>
);

export const Avatar: React.FC<{ name: string; photoUrl?: string | null; tone?: 'teach' | 'learn'; className?: string }> = ({
  name,
  photoUrl,
  tone = 'teach',
  className = 'w-12 h-12 text-xl',
}) => {
  // Se guarda qué dirección falló: si llega una foto nueva, se vuelve a intentar.
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  const showPhoto = Boolean(photoUrl) && photoUrl !== failedUrl;

  return (
    <div
      className={`${className} ${tone === 'teach' ? 'bg-teach-soft text-teach-strong' : 'bg-learn-soft text-learn-strong'} shrink-0 rounded-full flex items-center justify-center font-display font-semibold overflow-hidden`}
      aria-hidden="true"
    >
      {showPhoto ? (
        <img
          src={apiAssetUrl(photoUrl as string)}
          alt=""
          loading="lazy"
          onError={() => setFailedUrl(photoUrl ?? null)}
          className="w-full h-full object-cover"
        />
      ) : (
        name.charAt(0).toUpperCase() || 'U'
      )}
    </div>
  );
};
