import React, { useCallback, useEffect, useState } from 'react';
import { Plus, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { fetchSameInterests, type Person } from '../services/people';
import { EmptyState, ErrorState, LoadingState } from '../components/UIStates';
import { Avatar } from '../components/Swap';
import { FriendButton } from '../components/FriendButton';

const MAX_INTERESTS = 20;

export const Learn: React.FC = () => {
  const { token, user, updateProfile } = useAuth();
  const interests = user?.skillsSeeking ?? [];
  const [draft, setDraft] = useState('');
  const [saving, setSaving] = useState(false);
  const [people, setPeople] = useState<Person[] | null>(null);
  const [error, setError] = useState('');

  const loadPeople = useCallback(() => {
    if (!token) return;
    fetchSameInterests(token)
      .then(setPeople)
      .catch((err: unknown) => setError(errorMessage(err)));
  }, [token]);

  useEffect(loadPeople, [loadPeople]);

  const save = async (skillsSeeking: string[]) => {
    setSaving(true);
    setError('');
    try {
      await updateProfile({ skillsSeeking });
      loadPeople();
      return true;
    } catch (err) {
      setError(errorMessage(err));
      return false;
    } finally {
      setSaving(false);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    const topic = draft.trim();
    if (!topic) return;
    if (interests.some(existing => existing.toLowerCase() === topic.toLowerCase())) {
      setDraft('');
      return;
    }
    if (await save([...interests, topic])) setDraft('');
  };

  return (
    <div className="page max-w-5xl space-y-6">
      <div>
        <h1 className="page-title">Aprender</h1>
        <p className="page-subtitle">Di qué quieres aprender y encuentra a quienes están en lo mismo. Nadie tiene que ser experto.</p>
      </div>

      {error && <ErrorState message={error} />}

      <section className="card p-5 sm:p-6 space-y-4" aria-labelledby="my-interests">
        <h2 id="my-interests" className="text-xl text-ink">Quiero aprender</h2>
        <div className="flex flex-wrap gap-1.5">
          {interests.length === 0 && <span className="text-sm text-muted">Aún no has añadido ningún tema.</span>}
          {interests.map(topic => (
            <span key={topic} className="chip chip-teach inline-flex items-center gap-1.5 max-w-full">
              <span className="truncate">{topic}</span>
              <button
                type="button"
                disabled={saving}
                onClick={() => save(interests.filter(item => item !== topic))}
                aria-label={`Quitar ${topic}`}
                className="cursor-pointer shrink-0"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </span>
          ))}
        </div>
        <form onSubmit={handleAdd} className="flex gap-2">
          <input
            value={draft}
            onChange={e => setDraft(e.target.value)}
            maxLength={100}
            disabled={interests.length >= MAX_INTERESTS}
            placeholder={interests.length >= MAX_INTERESTS ? `Máximo ${MAX_INTERESTS} temas` : 'Ej.: Cálculo, Python, Inglés...'}
            aria-label="Tema que quieres aprender"
            className="field flex-1 min-w-0"
          />
          <button type="submit" disabled={saving || !draft.trim() || interests.length >= MAX_INTERESTS} className="btn btn-primary shrink-0">
            <Plus className="w-4 h-4" aria-hidden="true" />
            <span>Añadir</span>
          </button>
        </form>
      </section>

      <section className="space-y-3" aria-labelledby="same-interests">
        <h2 id="same-interests" className="text-2xl text-ink">Quieren aprender lo mismo que tú</h2>
        {!people && !error && <LoadingState message="Buscando personas..." />}
        {people && people.length === 0 && (
          <EmptyState
            title={interests.length === 0 ? 'Añade un tema para empezar' : 'Aún no hay nadie con tus temas'}
            description={interests.length === 0 ? 'Aquí aparecerá la gente que quiere aprender lo mismo que tú.' : 'Prueba con otras palabras: solo coinciden los temas escritos igual.'}
          />
        )}
        {people && people.length > 0 && (
          <div className="grid sm:grid-cols-2 gap-4">
            {people.map(person => (
              <article key={person.id} className="card p-5 space-y-3 min-w-0">
                <div className="flex items-center justify-between gap-3 min-w-0">
                  <span className="flex items-center gap-3 min-w-0">
                    <Avatar name={person.name} tone="learn" className="w-12 h-12 text-xl" />
                    <h3 className="text-lg text-ink truncate">{person.name}</h3>
                  </span>
                  <FriendButton
                    personId={person.id}
                    status={person.friendStatus}
                    onError={setError}
                    onChange={friendStatus =>
                      setPeople(current => current?.map(item => (item.id === person.id ? { ...item, friendStatus } : item)) ?? null)
                    }
                  />
                </div>
                {person.study && <p className="text-sm text-muted break-words">{person.study}</p>}
                <div className="flex flex-wrap gap-1.5">
                  {person.sharedInterests.map(topic => (
                    <span key={topic} className="chip chip-learn">{topic}</span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
