import React from 'react';
import { useNavigate } from 'react-router-dom';
import { EmptyState } from '../components/UIStates';

export const SessionSummary: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="page max-w-3xl">
      <EmptyState
        title="Resumen no disponible"
        description="Los resúmenes aparecerán aquí cuando las sesiones de estudio estén disponibles."
        actionLabel="Volver a mis sesiones"
        onAction={() => navigate('/my-sessions')}
      />
    </div>
  );
};
