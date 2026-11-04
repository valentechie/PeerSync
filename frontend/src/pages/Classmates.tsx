import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GraduationCap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { fetchStudyMatches, type StudyMatch } from '../services/people';
import { EmptyState, ErrorState, LoadingState } from '../components/UIStates';
import { Avatar } from '../components/Swap';
import { FriendButton } from '../components/FriendButton';

type Filter = 'all' | 'direct' | 'similar';

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'all', label: 'Todos' },
  { value: 'direct', label: 'Mismo estudio' },
  { value: 'similar', label: 'Estudios parecidos' },
];

export const Classmates: React.FC = () => {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [matches, setMatches] = useState<StudyMatch[] | null>(null);
  const [filter, setFilter] = useState<Filter>('all');
  const [error, setError] = useState('');

  const load = useCallback(() => {
    if (!token) return;
    fetchStudyMatches(token)
      .then(data => {
        setMatches(data);
        setError('');
      })
      .catch((err: unknown) => setError(errorMessage(err)));
  }, [token]);

  useEffect(load, [load]);

  const visible = matches?.filter(match => filter === 'all' || match.matchType === filter) ?? [];

  return (
    <div className="page max-w-5xl space-y-6">
      <div>
        <h1 className="page-title">Compañeros</h1>
        <p className="page-subtitle">
          Gente que estudia lo mismo que tú o algo parecido, aunque sea en otro nivel: de un Grado Medio a una ingeniería.
        </p>
      </div>

      {error && <ErrorState message={error} onRetry={load} />}

      {!user?.studyCode && (
        <EmptyState
          title="Dinos qué estudias"
          description="Elige tus estudios en tu perfil y aquí aparecerá la gente con la que te relacionamos."
          actionLabel="Elegir mis estudios"
          onAction={() => navigate('/my-profile')}
        />
      )}

      {user?.studyCode && (
        <>
          <p className="text-sm text-muted flex items-center gap-2 min-w-0">
            <GraduationCap className="w-4 h-4 text-teach shrink-0" aria-hidden="true" />
            <span className="break-words min-w-0">Tus estudios: <strong className="text-ink">{user.study}</strong></span>
          </p>

          <div className="flex flex-wrap gap-1 bg-paper/70 p-1.5 rounded-2xl border border-line w-fit max-w-full" role="group" aria-label="Filtrar compañeros">
            {FILTERS.map(option => (
              <button
                key={option.value}
                onClick={() => setFilter(option.value)}
                aria-pressed={filter === option.value}
                className={`px-3 py-2 rounded-xl text-xs font-bold cursor-pointer transition-colors ${filter === option.value ? 'nav-active' : 'text-muted hover:text-ink'}`}
              >
                {option.label}
              </button>
            ))}
          </div>

          {!matches && !error && <LoadingState message="Buscando compañeros..." />}

          {matches && visible.length === 0 && (
            <EmptyState
              title="Aún no hay nadie aquí"
              description={filter === 'direct' ? 'Nadie más ha elegido tus mismos estudios todavía. Prueba con los estudios parecidos.' : 'Cuando alguien elija estudios relacionados con los tuyos, aparecerá aquí.'}
            />
          )}

          {visible.length > 0 && (
            <div className="grid sm:grid-cols-2 gap-4">
              {visible.map(match => (
                <article key={match.id} className="card p-5 space-y-3 min-w-0">
                  <div className="flex items-center justify-between gap-3 min-w-0">
                    <span className="flex items-center gap-3 min-w-0">
                      <Avatar name={match.name} tone={match.matchType === 'direct' ? 'teach' : 'learn'} className="w-12 h-12 text-xl" />
                      <h2 className="text-lg text-ink truncate">{match.name}</h2>
                    </span>
                    <FriendButton
                      personId={match.id}
                      status={match.friendStatus}
                      onError={setError}
                      onChange={friendStatus =>
                        setMatches(current => current?.map(item => (item.id === match.id ? { ...item, friendStatus } : item)) ?? null)
                      }
                    />
                  </div>
                  <p className="text-sm text-muted break-words">{match.study}</p>
                  <div className="flex flex-wrap gap-1.5">
                    <span className={`chip ${match.matchType === 'direct' ? 'chip-teach' : 'chip-guide'}`}>{match.matchReason}</span>
                    {match.sharedInterests.map(topic => (
                      <span key={topic} className="chip chip-learn">{topic}</span>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};
