import React from 'react';
import { ArrowRight, CheckCircle, Inbox, Users } from 'lucide-react';
import type { Partner } from '../services/matching';

const STATES = {
  sent: { label: 'Solicitud enviada', icon: CheckCircle },
  received: { label: 'Te envió una solicitud', icon: Inbox },
  connected: { label: 'Conectados', icon: Users },
};

/** Botón de solicitud, o el estado real de la relación si ya existe una. */
export const ConnectButton: React.FC<{
  status: Partner['requestStatus'];
  sending: boolean;
  onConnect: () => void;
  className?: string;
}> = ({ status, sending, onConnect, className = '' }) => {
  if (status) {
    const { label, icon: Icon } = STATES[status];
    return (
      <span className={`btn cursor-default! bg-teach-soft text-teach-strong ${className}`}>
        <Icon className="w-4 h-4 shrink-0" />
        <span>{label}</span>
      </span>
    );
  }
  return (
    <button onClick={onConnect} disabled={sending} className={`btn btn-primary ${className}`}>
      <span>{sending ? 'Enviando...' : 'Conectar'}</span>
      <ArrowRight className="w-4 h-4" />
    </button>
  );
};
