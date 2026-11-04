import React from 'react';
import type { Partner } from '../services/matching';

/** Explica de dónde sale la afinidad, con los puntos que la componen. */
export const MatchReasons: React.FC<{ partner: Partner }> = ({ partner }) => {
  const { breakdown, score, reputation } = partner;
  return (
    <details className="text-sm text-muted">
      <summary className="cursor-pointer font-bold text-teach hover:text-teach-strong">
        ¿Por qué {score}% de afinidad?
      </summary>
      <ul className="mt-2 space-y-1">
        <li className="flex justify-between gap-4">
          <span>Lo que buscas y puede enseñarte</span>
          <span className="font-bold text-ink shrink-0">{breakdown.learnPoints}/40</span>
        </li>
        <li className="flex justify-between gap-4">
          <span>Lo que busca y puedes enseñarle</span>
          <span className="font-bold text-ink shrink-0">{breakdown.teachPoints}/40</span>
        </li>
        <li className="flex justify-between gap-4">
          <span>{reputation === null ? 'Reputación (aún sin valoraciones)' : 'Reputación'}</span>
          <span className="font-bold text-ink shrink-0">{breakdown.reputationPoints}/20</span>
        </li>
      </ul>
    </details>
  );
};
