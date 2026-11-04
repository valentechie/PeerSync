import React, { useEffect, useRef, useState } from 'react';
import { Check, Search, UserPlus, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { fetchInviteCandidates, inviteToRoom, type InviteCandidate } from '../services/invitations';
import { ErrorState } from './UIStates';
import { Avatar } from './Swap';

const MIN_SEARCH_LENGTH = 2;
const SEARCH_DELAY_MS = 300;

const STATUS_LABEL = { member: 'En la sala', invited: 'Invitación enviada', declined: 'Rechazó la invitación' };

export const InviteDialog: React.FC<{ roomId: string; onClose: () => void }> = ({ roomId, onClose }) => {
  const { token } = useAuth();
  const [search, setSearch] = useState('');
  const [candidates, setCandidates] = useState<InviteCandidate[] | null>(null);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const query = search.trim();
  const searchable = query.length === 0 || query.length >= MIN_SEARCH_LENGTH;

  useEffect(() => {
    inputRef.current?.focus();
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  useEffect(() => {
    if (!token || !searchable) return;
    let cancelled = false;
    const timer = setTimeout(() => {
      fetchInviteCandidates(token, roomId, query)
        .then(result => {
          if (cancelled) return;
          setCandidates(result);
          setError('');
        })
        .catch((err: unknown) => {
          if (!cancelled) setError(errorMessage(err));
        });
    }, query ? SEARCH_DELAY_MS : 0);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [token, roomId, query, searchable]);

  const handleInvite = async (person: InviteCandidate) => {
    if (!token) return;
    setBusyId(person.id);
    setError('');
    try {
      await inviteToRoom(token, roomId, person.id);
      setCandidates(current => current?.map(item => (item.id === person.id ? { ...item, status: 'invited' } : item)) ?? null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[90] overflow-y-auto bg-night/80 backdrop-blur-sm p-4 flex items-start sm:items-center justify-center"
      onMouseDown={e => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div role="dialog" aria-modal="true" aria-labelledby="invite-title" className="card w-full max-w-lg p-5 sm:p-6 space-y-4 my-auto">
        <div className="flex items-center justify-between gap-3">
          <h2 id="invite-title" className="text-xl text-ink">Invitar a la sala</h2>
          <button onClick={onClose} aria-label="Cerrar" className="p-2 -m-2 text-muted hover:text-ink rounded-lg cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="relative">
          <Search className="w-4 h-4 text-muted absolute left-3.5 top-3.5" aria-hidden="true" />
          <input
            ref={inputRef}
            value={search}
            onChange={e => setSearch(e.target.value)}
            maxLength={100}
            placeholder="Busca a cualquier persona por su nombre"
            aria-label="Buscar personas"
            className="field pl-10"
          />
        </div>

        {error && <ErrorState message={error} />}

        <h3 className="eyebrow font-sans text-teach">{query ? 'Resultados' : 'Tus amigos'}</h3>

        {!searchable && <p className="text-sm text-muted">Escribe al menos {MIN_SEARCH_LENGTH} letras.</p>}
        {searchable && !candidates && !error && <p role="status" className="text-sm text-muted">Cargando...</p>}
        {searchable && candidates?.length === 0 && (
          <p className="text-sm text-muted">
            {query ? 'No hay nadie con ese nombre.' : 'Aún no tienes amigos aquí. Busca a cualquier persona por su nombre.'}
          </p>
        )}

        {searchable && candidates && candidates.length > 0 && (
          <ul className="divide-y divide-line max-h-80 overflow-y-auto">
            {candidates.map(person => (
              <li key={person.id} className="flex items-center justify-between gap-3 py-3 min-w-0">
                <span className="flex items-center gap-3 min-w-0">
                  <Avatar name={person.name} photoUrl={person.photoUrl} tone={person.isFriend ? 'teach' : 'learn'} className="w-10 h-10 text-base" />
                  <span className="min-w-0">
                    <span className="block font-bold truncate">
                      {person.name}
                      {person.isFriend && query && <span className="chip chip-teach ml-2 py-0.5!">Amigo</span>}
                    </span>
                    {person.study && <span className="block text-xs text-muted truncate">{person.study}</span>}
                  </span>
                </span>
                {person.status ? (
                  <span className={`chip shrink-0 inline-flex items-center gap-1 ${person.status === 'declined' ? 'chip-learn' : 'chip-teach'}`}>
                    {person.status !== 'declined' && <Check className="w-3.5 h-3.5" aria-hidden="true" />}
                    <span>{STATUS_LABEL[person.status]}</span>
                  </span>
                ) : (
                  <button
                    onClick={() => handleInvite(person)}
                    disabled={busyId === person.id}
                    aria-label={`Invitar a ${person.name}`}
                    className="btn btn-primary py-2! shrink-0"
                  >
                    <UserPlus className="w-4 h-4" aria-hidden="true" />
                    <span>Invitar</span>
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
