import React from 'react';
import { useNavigate } from 'react-router-dom';
import { EmptyState } from '../components/UIStates';

export const MySessions: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="page max-w-5xl space-y-8">
      <div>
        <h1 className="page-title">Mis sesiones</h1>
        <p className="page-subtitle">Historial de intercambios de conocimiento y salas de estudio activas.</p>
      </div>

      <EmptyState
        title="Aún no hay sesiones"
        description="Las sesiones de estudio todavía no están disponibles. Mientras tanto, ya puedes buscar compañeros y enviarles solicitudes."
        actionLabel="Buscar compañeros"
        onAction={() => navigate('/find-partners')}
      />
    </div>
  );
};
