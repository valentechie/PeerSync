import React, { useState } from 'react';
import { Check, Clock, UserPlus } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { acceptFriend, addFriend, type FriendStatus } from '../services/people';

/** Añade a alguien como amigo o acepta su solicitud, según el estado actual. */
export const FriendButton: React.FC<{
  personId: string;
  status: FriendStatus;
  onChange: (status: FriendStatus) => void;
  onError: (message: string) => void;
}> = ({ personId, status, onChange, onError }) => {
  const { token } = useAuth();
  const [busy, setBusy] = useState(false);

  if (status === 'friend') {
    return (
      <span className="chip chip-teach inline-flex items-center gap-1.5 shrink-0">
        <Check className="w-3.5 h-3.5" aria-hidden="true" />
        <span>Amigos</span>
      </span>
    );
  }
  if (status === 'sent') {
    return (
      <span className="chip chip-demo inline-flex items-center gap-1.5 shrink-0">
        <Clock className="w-3.5 h-3.5" aria-hidden="true" />
        <span>Solicitud enviada</span>
      </span>
    );
  }

  const handleClick = async () => {
    if (!token) return;
    setBusy(true);
    try {
      const updated = await (status === 'received' ? acceptFriend(token, personId) : addFriend(token, personId));
      onChange(updated.friendStatus);
    } catch (err) {
      onError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <button onClick={handleClick} disabled={busy} className="btn btn-secondary py-2! shrink-0">
      <UserPlus className="w-4 h-4" aria-hidden="true" />
      <span>{status === 'received' ? 'Aceptar' : 'Añadir'}</span>
    </button>
  );
};
