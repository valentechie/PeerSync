import React, { useState } from 'react';
import { Send, Star } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { CRITERIA, MIN_COMMENT_LENGTH, submitReview, type ReviewScores } from '../services/reviews';
import { ErrorState } from './UIStates';
import { Avatar } from './Swap';

const StarInput: React.FC<{ label: string; value: number; onChange: (value: number) => void }> = ({ label, value, onChange }) => (
  <div role="radiogroup" aria-label={label} className="flex gap-0.5">
    {[1, 2, 3, 4, 5].map(score => (
      <button
        key={score}
        type="button"
        role="radio"
        aria-checked={value === score}
        aria-label={`${score} de 5`}
        onClick={() => onChange(score)}
        className="p-1 rounded cursor-pointer"
      >
        <Star className={`w-6 h-6 ${score <= value ? 'fill-sun text-sun' : 'text-line'}`} aria-hidden="true" />
      </button>
    ))}
  </div>
);

export const ReviewForm: React.FC<{
  roomId: string;
  person: { id: string; name: string };
  onDone: () => void;
}> = ({ roomId, person, onDone }) => {
  const { token } = useAuth();
  const [scores, setScores] = useState<ReviewScores>({ clarity: 0, listening: 0, preparation: 0 });
  const [comment, setComment] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const commentLength = comment.trim().length;
  const complete = CRITERIA.every(({ key }) => scores[key] > 0) && commentLength >= MIN_COMMENT_LENGTH;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !complete) return;
    setSending(true);
    setError('');
    try {
      await submitReview(token, roomId, person.id, scores, comment);
      onDone();
    } catch (err) {
      setError(errorMessage(err));
      setSending(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} aria-label={`Evaluar a ${person.name}`} className="rounded-2xl border border-line p-4 sm:p-5 space-y-4">
      <div className="flex items-center gap-3 min-w-0">
        <Avatar name={person.name} tone="learn" className="w-10 h-10 text-base" />
        <h3 className="text-lg text-ink truncate">Evalúa a {person.name}</h3>
      </div>

      {error && <ErrorState message={error} />}

      <div className="space-y-3">
        {CRITERIA.map(({ key, label, hint }) => (
          <div key={key} className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
            <div className="min-w-0">
              <p className="text-sm font-bold">{label}</p>
              <p className="text-xs text-muted">{hint}</p>
            </div>
            <StarInput
              label={label}
              value={scores[key]}
              onChange={value => setScores(current => ({ ...current, [key]: value }))}
            />
          </div>
        ))}
      </div>

      <div>
        <label htmlFor={`comment-${person.id}`} className="label">Comentario</label>
        <textarea
          id={`comment-${person.id}`}
          rows={3}
          maxLength={1000}
          value={comment}
          onChange={e => setComment(e.target.value)}
          placeholder="¿Qué hizo bien? ¿Qué podría mejorar?"
          aria-describedby={`comment-help-${person.id}`}
          className="field"
        />
        <p id={`comment-help-${person.id}`} className="text-xs text-muted mt-1.5">
          {commentLength < MIN_COMMENT_LENGTH
            ? `Mínimo ${MIN_COMMENT_LENGTH} caracteres: te faltan ${MIN_COMMENT_LENGTH - commentLength}.`
            : 'Lo verá con tu nombre, y no podrás cambiarlo después.'}
        </p>
      </div>

      <button type="submit" disabled={!complete || sending} className="btn btn-primary w-full">
        <Send className="w-4 h-4" aria-hidden="true" />
        <span>{sending ? 'Enviando...' : 'Enviar evaluación'}</span>
      </button>
    </form>
  );
};
