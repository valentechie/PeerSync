import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Plus, Sparkles, Users, Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { createRoom, fetchRooms, type RoomSummary } from '../services/rooms';
import { EmptyState, ErrorState, LoadingState } from '../components/UIStates';
import { InvitationsPanel } from '../components/InvitationsPanel';

export const Rooms: React.FC = () => {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [rooms, setRooms] = useState<RoomSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [title, setTitle] = useState('');
  const [objective, setObjective] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');

  const load = useCallback(() => {
    if (!token) return;
    fetchRooms(token)
      .then(setRooms)
      .catch((err: unknown) => setLoadError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(load, [load]);

  const retry = () => {
    setLoading(true);
    setLoadError('');
    load();
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setCreating(true);
    setCreateError('');
    try {
      const room = await createRoom(token, title, objective);
      navigate(`/rooms/${room.id}`);
    } catch (err) {
      setCreateError(errorMessage(err));
      setCreating(false);
    }
  };

  return (
    <div className="page max-w-7xl space-y-6">
      <section className="hero p-6 sm:p-10">
        <Sparkles className="absolute -right-12 -bottom-20 w-96 h-96 text-white/15 hidden md:block" aria-hidden="true" />
        <div className="relative max-w-2xl space-y-5">
          <p className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/15 border border-white/20 text-xs font-bold">
            <Zap className="w-3.5 h-3.5 text-amber-300" aria-hidden="true" />
            <span>Hack4Edu 2026 · PeerSync</span>
          </p>
          <h1 className="text-4xl sm:text-5xl font-extrabold leading-tight break-words">
            ¡Hola, {user?.name || 'Estudiante'}! 👋
          </h1>
          <p className="text-lg text-indigo-100 leading-relaxed">
            No hace falta ser experto para aprender con alguien. Entra en una sala, comparte lo que entiendes y resuelve en grupo lo que no.
          </p>
        </div>
      </section>

      <InvitationsPanel />

      <div className="grid lg:grid-cols-3 gap-6 items-start">
        <section className="card p-6 sm:p-8" aria-labelledby="create-room">
          <h2 id="create-room" className="text-2xl text-ink">Abre una sala</h2>
          <p className="text-sm text-muted mt-1 mb-5">¿Qué quieres estudiar hoy? Otros podrán unirse.</p>
          {createError && <div className="mb-4"><ErrorState message={createError} /></div>}
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label htmlFor="room-title" className="label">Tema</label>
              <input
                id="room-title"
                required
                maxLength={120}
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="Ej.: Integrales para el parcial"
                className="field"
              />
            </div>
            <div>
              <label htmlFor="room-objective" className="label">Objetivo (opcional)</label>
              <textarea
                id="room-objective"
                rows={2}
                maxLength={300}
                value={objective}
                onChange={e => setObjective(e.target.value)}
                placeholder="Ej.: Entender la integración por partes"
                className="field"
              />
            </div>
            <button type="submit" disabled={creating || !title.trim()} className="btn btn-primary w-full">
              <Plus className="w-4 h-4" />
              <span>{creating ? 'Abriendo...' : 'Abrir sala'}</span>
            </button>
          </form>
        </section>

        <section className="lg:col-span-2 space-y-4" aria-labelledby="open-rooms">
          <h2 id="open-rooms" className="text-2xl text-ink">Salas abiertas</h2>
          {loading && <LoadingState message="Cargando salas..." />}
          {!loading && loadError && <ErrorState message={loadError} onRetry={retry} />}
          {!loading && !loadError && rooms.length === 0 && (
            <EmptyState title="Aún no hay salas" description="Abre la primera y comparte el enlace con tus compañeros." />
          )}
          {!loading && !loadError && (
            <div className="grid sm:grid-cols-2 gap-4">
              {rooms.map(room => (
                <article key={room.id} className="card p-5 flex flex-col gap-3">
                  <div className="flex-1 space-y-1 min-w-0">
                    <h3 className="text-lg text-ink break-words">{room.title}</h3>
                    {room.objective && <p className="text-sm text-muted break-words">{room.objective}</p>}
                  </div>
                  <div className="flex items-center justify-between gap-3 border-t border-line pt-3">
                    <span className="text-sm font-semibold text-muted flex items-center gap-1.5">
                      <Users className="w-4 h-4" aria-hidden="true" />
                      <span>{room.participantCount} {room.participantCount === 1 ? 'persona' : 'personas'}</span>
                    </span>
                    <button onClick={() => navigate(`/rooms/${room.id}`)} className="btn btn-primary py-2!">
                      <span>{room.isMember ? 'Volver' : 'Entrar'}</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
