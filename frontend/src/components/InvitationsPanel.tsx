import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Mail, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { acceptInvitation, declineInvitation, fetchInvitations, type RoomInvitation } from '../services/invitations';
import { ErrorState } from './UIStates';

const POLL_INTERVAL_MS = 10000;

export const InvitationsPanel: React.FC = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [invitations, setInvitations] = useState<RoomInvitation[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    if (!token) return;
    fetchInvitations(token)
      .then(setInvitations)
      .catch(() => undefined);
  }, [token]);

  useEffect(() => {
    load();
    const timer = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [load]);

  const handleAccept = async (invitation: RoomInvitation) => {
    if (!token) return;
    setBusyId(invitation.id);
    setError('');
    try {
      const { roomId } = await acceptInvitation(token, invitation.id);
      navigate(`/rooms/${roomId}`);
    } catch (err) {
      setError(errorMessage(err));
      load();
      setBusyId(null);
    }
  };

  const handleDecline = async (invitation: RoomInvitation) => {
    if (!token) return;
    setBusyId(invitation.id);
    setError('');
    try {
      await declineInvitation(token, invitation.id);
      setInvitations(current => current.filter(item => item.id !== invitation.id));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section className="space-y-3" aria-labelledby="my-invitations">
      <div>
        <h2 id="my-invitations" className="text-2xl text-ink flex items-center gap-2">
          <Mail className="w-6 h-6 text-teach-strong shrink-0" aria-hidden="true" />
          <span>Salas disponibles{invitations.length > 0 && ` (${invitations.length})`}</span>
        </h2>
        <p className="text-sm text-muted mt-1">
          {invitations.length > 0 ? 'Salas a las que te han invitado.' : 'Aquí aparecerán las salas a las que te inviten.'}
        </p>
      </div>
      {error && <ErrorState message={error} />}
      <div className="grid sm:grid-cols-2 gap-4">
        {invitations.map(invitation => (
          <article key={invitation.id} className="card p-5 space-y-3 min-w-0">
            <div className="min-w-0 space-y-1">
              <p className="text-sm text-muted break-words"><strong className="text-ink">{invitation.inviterName}</strong> te invita a:</p>
              <h3 className="text-lg text-ink break-words">{invitation.roomTitle}</h3>
              {invitation.roomObjective && <p className="text-sm text-muted break-words">{invitation.roomObjective}</p>}
            </div>
            <div className="flex gap-2">
              <button onClick={() => handleAccept(invitation)} disabled={busyId === invitation.id} className="btn btn-primary flex-1 py-2!">
                <Check className="w-4 h-4" aria-hidden="true" />
                <span>Aceptar</span>
              </button>
              <button onClick={() => handleDecline(invitation)} disabled={busyId === invitation.id} className="btn btn-secondary flex-1 py-2!">
                <X className="w-4 h-4" aria-hidden="true" />
                <span>Rechazar</span>
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
};
