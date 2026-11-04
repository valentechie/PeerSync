import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Star } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { CRITERIA, fetchFeedback, fetchPendingReviews, type FeedbackSummary, type PendingReview } from '../services/reviews';
import { ErrorState, LoadingState } from './UIStates';
import { Avatar } from './Swap';

const formatDate = (iso: string) => new Date(iso).toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' });

export const FeedbackSection: React.FC = () => {
  const { token } = useAuth();
  const [feedback, setFeedback] = useState<FeedbackSummary | null>(null);
  const [pending, setPending] = useState<PendingReview[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) return;
    Promise.all([fetchFeedback(token), fetchPendingReviews(token)])
      .then(([summary, reviews]) => {
        setFeedback(summary);
        setPending(reviews);
      })
      .catch((err: unknown) => setError(errorMessage(err)));
  }, [token]);

  if (error) return <ErrorState message={error} />;
  if (!feedback) return <LoadingState message="Cargando tu feedback..." />;

  return (
    <div className="space-y-6">
      {pending.length > 0 && (
        <section className="card p-6 sm:p-8 space-y-3" aria-labelledby="pending-reviews">
          <h2 id="pending-reviews" className="text-2xl text-ink">Evaluaciones pendientes ({pending.length})</h2>
          <ul className="divide-y divide-line">
            {pending.map(item => (
              <li key={`${item.roomId}-${item.personId}`}>
                <Link to={`/rooms/${item.roomId}`} className="flex items-center justify-between gap-3 py-3 min-w-0 hover:text-teach-strong">
                  <span className="min-w-0">
                    <span className="block font-bold truncate">{item.personName}</span>
                    <span className="block text-sm text-muted truncate">{item.roomTitle}</span>
                  </span>
                  <ArrowRight className="w-4 h-4 shrink-0" aria-hidden="true" />
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="card p-6 sm:p-8 space-y-5" aria-labelledby="my-feedback">
        <div>
          <h2 id="my-feedback" className="text-2xl text-ink">Feedback recibido</h2>
          <p className="text-sm text-muted mt-1">Lo que dicen de ti las personas con las que has estudiado. Solo lo ves tú.</p>
        </div>

        {feedback.count === 0 ? (
          <p className="text-sm text-muted">Aún no te han evaluado. Cuando se cierre una sala, sus participantes podrán hacerlo.</p>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="rounded-2xl bg-teach-soft/50 p-4">
                <p className="font-display text-3xl font-bold flex items-center gap-1.5">
                  <Star className="w-5 h-5 fill-sun text-sun" aria-hidden="true" />
                  <span>{feedback.average?.toFixed(1)}</span>
                </p>
                <p className="text-sm text-muted">{feedback.count} {feedback.count === 1 ? 'evaluación' : 'evaluaciones'}</p>
              </div>
              {CRITERIA.map(({ key, label }) => (
                <div key={key} className="rounded-2xl border border-line p-4">
                  <p className="font-display text-3xl font-bold">{feedback[key]?.toFixed(1)}</p>
                  <p className="text-sm text-muted">{label}</p>
                </div>
              ))}
            </div>

            <ul className="space-y-3">
              {feedback.items.map(item => (
                <li key={item.id} className="border-t border-line pt-4 space-y-2">
                  <div className="flex items-center gap-3 min-w-0">
                    <Avatar name={item.reviewerName} tone="learn" className="w-9 h-9 text-sm" />
                    <div className="min-w-0">
                      <p className="font-bold truncate">{item.reviewerName}</p>
                      <p className="text-xs text-muted truncate">{item.roomTitle} · {formatDate(item.createdAt)}</p>
                    </div>
                  </div>
                  <p className="text-sm whitespace-pre-wrap break-words">{item.comment}</p>
                  <p className="text-xs text-muted">
                    {CRITERIA.map(({ key, label }) => `${label}: ${item[key]}/5`).join(' · ')}
                  </p>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
    </div>
  );
};
