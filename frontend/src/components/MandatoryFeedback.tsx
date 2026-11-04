import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Send } from 'lucide-react';
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

/**
 * Ventana obligatoria: aparece al salir de una sala, y también al volver si se cerró la
 * pestaña sin terminar, porque las evaluaciones pendientes las guarda el servidor.
 */
export const MandatoryFeedback: React.FC = () => {
  const { token, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [pending, setPending] = useState<PendingReview[]>([]);
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
  const currentKey = current ? `${current.roomId}-${current.personId}` : null;

  useEffect(() => {
    if (currentKey) dialogRef.current?.querySelector('input')?.focus();
  }, [currentKey]);

  if (!current) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setSending(true);
    setError('');
    try {
      await submitReview(token, current.roomId, current.personId, scores);
      setPending(remaining => remaining.slice(1));
      setScores(initialScores());
    } catch (err) {
      setError(errorMessage(err));
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
        className="card w-full max-w-lg p-5 sm:p-7 space-y-5 my-auto"
      >
        <div className="flex items-center gap-3 min-w-0">
          <Avatar name={current.personName} tone="learn" className="w-12 h-12 text-xl" />
          <div className="min-w-0">
            <h2 id="mandatory-feedback-title" className="text-xl text-ink truncate">Evalúa a {current.personName}</h2>
            <p className="text-sm text-muted truncate">{current.roomTitle}</p>
          </div>
          {pending.length > 1 && <span className="chip chip-demo ml-auto shrink-0">Quedan {pending.length}</span>}
        </div>

        <p className="text-sm text-muted">Es obligatorio para poder entrar en otra sala. Mueve cada barra de 0 a 10.</p>

        {error && <ErrorState message={error} />}

        <form onSubmit={handleSubmit} className="space-y-4">
          {CRITERIA.map(({ key, label, hint }) => (
            <div key={key}>
              <div className="flex items-baseline justify-between gap-3">
                <label htmlFor={`score-${key}`} className="text-sm font-bold">{label}</label>
                <output htmlFor={`score-${key}`} className="font-display text-xl font-bold text-teach-strong">{scores[key]}</output>
              </div>
              <p className="text-xs text-muted mb-1.5">{hint}</p>
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
            <Send className="w-4 h-4" aria-hidden="true" />
            <span>{sending ? 'Enviando...' : pending.length > 1 ? 'Enviar y seguir' : 'Enviar evaluación'}</span>
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
