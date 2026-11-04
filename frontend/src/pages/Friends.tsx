import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Check, Search, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { acceptFriend, fetchFriends, removeFriend, searchPeople, type FriendsOverview, type Person } from '../services/people';
import { EmptyState, ErrorState, LoadingState } from '../components/UIStates';
import { Avatar } from '../components/Swap';
import { FriendButton } from '../components/FriendButton';

const MIN_SEARCH_LENGTH = 2;

export const Friends: React.FC = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [overview, setOverview] = useState<FriendsOverview | null>(null);
  const [loadError, setLoadError] = useState('');
  const [actionError, setActionError] = useState('');
  const [search, setSearch] = useState('');
  const [results, setResults] = useState<Person[] | null>(null);
  const [searching, setSearching] = useState(false);

  const load = useCallback(() => {
    if (!token) return;
    fetchFriends(token)
      .then(data => {
        setOverview(data);
        setLoadError('');
      })
      .catch((err: unknown) => setLoadError(errorMessage(err)));
  }, [token]);

  useEffect(load, [load]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setSearching(true);
    setActionError('');
    try {
      setResults(await searchPeople(token, search.trim()));
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setSearching(false);
    }
  };

  const run = async (action: () => Promise<unknown>) => {
    setActionError('');
    try {
      await action();
      load();
    } catch (err) {
      setActionError(errorMessage(err));
    }
  };

  const accept = (id: string) => token && run(() => acceptFriend(token, id));
  const remove = (id: string) => token && run(() => removeFriend(token, id));

  return (
    <div className="page max-w-5xl space-y-6">
      <div>
        <h1 className="page-title">Amigos</h1>
        <p className="page-subtitle">La gente con la que te sientes a gusto estudiando.</p>
      </div>

      {actionError && <ErrorState message={actionError} />}
      {loadError && <ErrorState message={loadError} onRetry={load} />}

      <section className="card p-5 sm:p-6 space-y-4" aria-labelledby="find-people">
        <h2 id="find-people" className="text-xl text-ink">Buscar personas</h2>
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1 min-w-0">
            <Search className="w-4 h-4 text-muted absolute left-3.5 top-3.5" aria-hidden="true" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              minLength={MIN_SEARCH_LENGTH}
              maxLength={100}
              required
              placeholder="Escribe un nombre"
              aria-label="Nombre de la persona"
              className="field pl-10"
            />
          </div>
          <button type="submit" disabled={searching || search.trim().length < MIN_SEARCH_LENGTH} className="btn btn-primary shrink-0">
            Buscar
          </button>
        </form>
        {results && results.length === 0 && <p className="text-sm text-muted">No hay nadie con ese nombre.</p>}
        {results && results.length > 0 && (
          <ul className="divide-y divide-line">
            {results.map(person => (
              <li key={person.id} className="flex items-center justify-between gap-3 py-3 min-w-0">
                <span className="flex items-center gap-3 min-w-0">
                  <Avatar name={person.name} className="w-10 h-10 text-base" />
                  <span className="min-w-0">
                    <span className="block font-bold truncate">{person.name}</span>
                    {person.study && <span className="block text-xs text-muted truncate">{person.study}</span>}
                  </span>
                </span>
                <FriendButton
                  personId={person.id}
                  status={person.friendStatus}
                  onError={setActionError}
                  onChange={friendStatus => {
                    setResults(current => current?.map(item => (item.id === person.id ? { ...item, friendStatus } : item)) ?? null);
                    load();
                  }}
                />
              </li>
            ))}
          </ul>
        )}
      </section>

      {!overview && !loadError && <LoadingState message="Cargando amigos..." />}

      {overview && overview.received.length > 0 && (
        <section className="card p-5 sm:p-6 space-y-3" aria-labelledby="received">
          <h2 id="received" className="text-xl text-ink">Solicitudes recibidas ({overview.received.length})</h2>
          <ul className="divide-y divide-line">
            {overview.received.map(person => (
              <li key={person.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <span className="flex items-center gap-3 min-w-0">
                  <Avatar name={person.name} tone="learn" className="w-10 h-10 text-base" />
                  <span className="font-bold truncate">{person.name}</span>
                </span>
                <span className="flex gap-2">
                  <button onClick={() => accept(person.id)} className="btn btn-primary py-2!">
                    <Check className="w-4 h-4" aria-hidden="true" />
                    <span>Aceptar</span>
                  </button>
                  <button onClick={() => remove(person.id)} className="btn btn-secondary py-2!">Rechazar</button>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {overview && overview.friends.length === 0 && (
        <EmptyState
          title="Aún no tienes amigos aquí"
          description="Búscalos por nombre, añádelos desde una sala o encuentra gente que quiere aprender lo mismo que tú."
          actionLabel="Ver quién aprende lo mismo"
          onAction={() => navigate('/learn')}
        />
      )}

      {overview && overview.friends.length > 0 && (
        <section className="space-y-3" aria-labelledby="friends">
          <h2 id="friends" className="text-2xl text-ink">Tus amigos ({overview.friends.length})</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {overview.friends.map(friend => (
              <article key={friend.id} className="card p-5 space-y-3 min-w-0">
                <div className="flex items-center gap-3 min-w-0">
                  <Avatar name={friend.name} className="w-12 h-12 text-xl" />
                  <div className="min-w-0 flex-1">
                    <h3 className="text-lg text-ink truncate">{friend.name}</h3>
                    {friend.study && <p className="text-sm text-muted truncate">{friend.study}</p>}
                  </div>
                  <button
                    onClick={() => remove(friend.id)}
                    title="Eliminar de amigos"
                    aria-label={`Eliminar a ${friend.name} de amigos`}
                    className="p-2 text-muted hover:text-learn-strong hover:bg-learn-soft rounded-lg transition-colors cursor-pointer shrink-0"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="border-t border-line pt-3">
                  <p className="eyebrow font-sans text-teach mb-2">Sus salas</p>
                  {friend.rooms.length === 0 && <p className="text-sm text-muted">Todavía no está en ninguna sala.</p>}
                  <ul className="space-y-1.5">
                    {friend.rooms.map(room => (
                      <li key={room.id}>
                        <Link to={`/rooms/${room.id}`} className="text-sm font-bold text-teach-strong hover:underline underline-offset-2 inline-flex items-center gap-1.5 max-w-full">
                          <span className="truncate">{room.title}</span>
                          <ArrowRight className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {overview && overview.sent.length > 0 && (
        <section className="card p-5 sm:p-6 space-y-3" aria-labelledby="sent">
          <h2 id="sent" className="text-xl text-ink">Solicitudes enviadas ({overview.sent.length})</h2>
          <ul className="divide-y divide-line">
            {overview.sent.map(person => (
              <li key={person.id} className="flex items-center justify-between gap-3 py-3 min-w-0">
                <span className="font-bold truncate">{person.name}</span>
                <button onClick={() => remove(person.id)} className="btn btn-secondary py-2! shrink-0">Cancelar</button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
};
