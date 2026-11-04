import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Check, Send } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { CRITERIA, fetchPendingReviews, INITIAL_SCORE, submitReview, type PendingReview, type ReviewScores } from '../services/reviews';
import { ErrorState } from './UIStates';
import { Avatar } from './Swap';

const initialScores = (): ReviewScores => ({
  punctuality: INITIAL_SCORE,
  treatment: INITIAL_SCORE,
  participation: INITIAL_SCORE,
  clarity: INITIAL_SCORE,
});

const personKey = (review: PendingReview) => `${review.roomId}-${review.personId}`;

/**
 * Ventana obligatoria: aparece al salir de una sala, y también al volver si se cerró la
 * pestaña sin terminar, porque las evaluaciones pendientes las guarda el servidor.
 * Pide evaluar a todos los participantes, de uno en uno y mostrando a quién faltan.
 */
export const MandatoryFeedback: React.FC = () => {
  const { token, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [pending, setPending] = useState<PendingReview[]>([]);
  const [done, setDone] = useState<PendingReview[]>([]);
  const [scores, setScores] = useState<ReviewScores>(initialScores);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const dialogRef = useRef<HTMLDivElement>(null);

  const load = useCallback(() => {
    if (!token) return;
    fetchPendingReviews(token)
      .then(setPending)
      .catch(() => undefined);
  }, [token]);

  useEffect(load, [load, location.pathname]);

  const current = pending[0];
  const currentKey = current ? personKey(current) : null;

  useEffect(() => {
    if (currentKey) dialogRef.current?.querySelector('input')?.focus();
  }, [currentKey]);

  if (!current || !token) return null;

  const inThisRoom = (review: PendingReview) => review.roomId === current.roomId;
  const remaining = pending.filter(inThisRoom);
  const finished = done.filter(inThisRoom);
  const everyone = [...finished, ...remaining];
  const next = remaining[1] ?? pending.find(review => !inThisRoom(review));
  const roomsLeft = new Set(pending.map(review => review.roomId)).size;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    setError('');
    try {
      await submitReview(token, current.roomId, current.personId, scores);
      setDone(previous => [...previous, current]);
      setScores(initialScores());
      // La lista la decide siempre el servidor: nadie se queda fuera ni se pregunta dos veces.
      setPending(await fetchPendingReviews(token).catch(() => pending.slice(1)));
    } catch (err) {
      setError(errorMessage(err));
      load();
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] overflow-y-auto bg-night/85 backdrop-blur-sm p-4 flex items-start sm:items-center justify-center">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="mandatory-feedback-title"
        className="card w-full max-w-lg p-5 sm:p-7 space-y-4 my-auto"
      >
        <div>
          <p className="text-sm text-muted truncate">{current.roomTitle}{roomsLeft > 1 && ` · y ${roomsLeft - 1} sala más`}</p>
          <h2 id="mandatory-feedback-title" className="text-xl text-ink">Evalúa a todos los participantes</h2>
          <p className="text-sm text-muted mt-1">Es obligatorio para poder entrar en otra sala.</p>
        </div>

        <ul className="flex flex-wrap gap-2" aria-label={`Persona ${finished.length + 1} de ${everyone.length}`}>
          {everyone.map(person => {
            const isDone = finished.includes(person);
            const isCurrent = person === current;
            return (
              <li
                key={personKey(person)}
                aria-current={isCurrent ? 'step' : undefined}
                className={`flex items-center gap-1.5 rounded-full border py-1 pl-1 pr-3 max-w-44 text-xs font-bold ${
                  isCurrent ? 'border-teach bg-teach-soft text-teach-strong' : isDone ? 'border-line text-muted' : 'border-line'
                }`}
              >
                <Avatar name={person.personName} photoUrl={person.personPhotoUrl} tone="learn" className="w-6 h-6 text-[11px]" />
                <span className="truncate">{person.personName}</span>
                {isDone && <Check className="w-3.5 h-3.5 text-teach shrink-0" aria-label="evaluado" />}
              </li>
            );
          })}
        </ul>

        <div className="flex items-center gap-3 border-t border-line pt-4 min-w-0">
          <Avatar name={current.personName} photoUrl={current.personPhotoUrl} tone="learn" className="w-12 h-12 text-xl" />
          <div className="min-w-0">
            <p className="text-xs text-muted">Persona {finished.length + 1} de {everyone.length}</p>
            <h3 className="text-lg text-ink truncate">{current.personName}</h3>
          </div>
        </div>

        {error && <ErrorState message={error} />}

        <form onSubmit={handleSubmit} className="space-y-3">
          {CRITERIA.map(({ key, label, hint }) => (
            <div key={key}>
              <div className="flex items-baseline justify-between gap-3">
                <label htmlFor={`score-${key}`} className="text-sm font-bold">{label}</label>
                <output htmlFor={`score-${key}`} className="font-display text-xl font-bold text-teach-strong">{scores[key]}</output>
              </div>
              <p className="text-xs text-muted mb-1">{hint}</p>
              <input
                id={`score-${key}`}
                type="range"
                min={0}
                max={10}
                step={1}
                value={scores[key]}
                onChange={e => {
                  const value = Number(e.target.value);
                  setScores(previous => ({ ...previous, [key]: value }));
                }}
                className="w-full cursor-pointer accent-teach"
              />
            </div>
          ))}
          <button type="submit" disabled={sending} className="btn btn-primary w-full">
            <Send className="w-4 h-4 shrink-0" aria-hidden="true" />
            <span className="truncate">{sending ? 'Enviando...' : next ? `Enviar y seguir con ${next.personName}` : 'Enviar y terminar'}</span>
          </button>
        </form>

        <button
          type="button"
          onClick={() => {
            logout();
            navigate('/login');
          }}
          className="block mx-auto text-xs font-bold text-muted underline underline-offset-2 cursor-pointer"
        >
          Cerrar sesión
        </button>
      </div>
    </div>
  );
};
