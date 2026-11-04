import React from 'react';
import { BookOpen, Star } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { EmptyState } from '../components/UIStates';

export const MyProgress: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="page max-w-5xl space-y-8">
      <div>
        <h1 className="page-title">Mi progreso</h1>
        <p className="page-subtitle">Lo que has enseñado, lo que has aprendido y cómo evolucionan tus habilidades.</p>
      </div>

      <div className="grid sm:grid-cols-2 gap-4 sm:gap-6">
        <div className="card p-5 sm:p-6 space-y-2">
          <BookOpen className="w-5 h-5 text-teach" />
          <p className="font-display text-3xl font-semibold">{user?.completedSessions ?? 0}</p>
          <p className="text-sm text-muted">Sesiones completadas</p>
        </div>
        <div className="card p-5 sm:p-6 space-y-2">
          <Star className="w-5 h-5 text-sun fill-sun" />
          <p className="font-display text-3xl font-semibold">{user?.reputation?.toFixed(1) ?? '—'}</p>
          <p className="text-sm text-muted">
            {user?.reputation == null ? 'Aún sin valoraciones de compañeros' : 'Reputación entre compañeros'}
          </p>
        </div>
      </div>

      <EmptyState
        title="Sin evolución de habilidades todavía"
        description="Tu evolución aparecerá aquí cuando completes sesiones de estudio."
      />
    </div>
  );
};
