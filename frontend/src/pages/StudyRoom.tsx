import React from 'react';
import { useNavigate } from 'react-router-dom';
import { EmptyState } from '../components/UIStates';

export const StudyRoom: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="page max-w-3xl">
      <EmptyState
        title="Sala de estudio no disponible"
        description="Las salas de estudio todavía no están disponibles. Aquí podrás conversar con tu compañero y pedir ayuda a StudyMind y TeachBack."
        actionLabel="Volver a mis sesiones"
        onAction={() => navigate('/my-sessions')}
      />
    </div>
  );
};
