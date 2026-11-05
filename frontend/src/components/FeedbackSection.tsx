import React, { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Star } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { CRITERIA, fetchFeedback, type FeedbackSummary } from '../services/reviews';
import { ErrorState, LoadingState } from './UIStates';
import { Avatar } from './Swap';

const formatDate = (iso: string) => new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

const MAX_PAGES_WITHOUT_GAPS = 5;

/** Todas si son pocas. Si no, primera, última y vecinas de la actual, con el resto en "…". */
const visiblePages = (current: number, total: number): (number | 'gap')[] => {
  if (total <= MAX_PAGES_WITHOUT_GAPS) return Array.from({ length: total }, (_, index) => index + 1);
  const pages: (number | 'gap')[] = [];
  for (let page = 1; page <= total; page += 1) {
    if (page === 1 || page === total || Math.abs(page - current) <= 1) pages.push(page);
    else if (pages[pages.length - 1] !== 'gap') pages.push('gap');
  }
  return pages;
};

export const FeedbackSection: React.FC = () => {
  const { token } = useAuth();
  const [feedback, setFeedback] = useState<FeedbackSummary | null>(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    fetchFeedback(token, page)
      .then(summary => {
        if (!cancelled) {
          setFeedback(summary);
          setError('');
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(errorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [token, page]);

  if (error && !feedback) return <ErrorState message={error} />;
  if (!feedback) return <LoadingState message="Loading your feedback..." />;

  const totalPages = Math.ceil(feedback.count / feedback.pageSize);
  const loadingPage = feedback.page !== page;
  const firstShown = (feedback.page - 1) * feedback.pageSize + 1;

  return (
    <section className="card p-6 sm:p-8 space-y-5" aria-labelledby="my-feedback">
      <div>
        <h2 id="my-feedback" className="text-2xl text-ink">Feedback received</h2>
        <p className="text-sm text-muted mt-1">How the people you've studied with rate you. Only you can see this.</p>
      </div>

      {error && <ErrorState message={error} />}

      {feedback.count === 0 ? (
        <p className="text-sm text-muted">Nobody has rated you yet. Your peers will do so when they leave a room.</p>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <div className="col-span-2 sm:col-span-1 rounded-2xl bg-teach-soft/50 p-4">
              <p className="font-display text-3xl font-bold flex items-center gap-1.5">
                <Star className="w-5 h-5 fill-sun text-sun" aria-hidden="true" />
                <span>{feedback.average?.toFixed(1)}</span>
              </p>
              <p className="text-sm text-muted">{feedback.count} {feedback.count === 1 ? 'review' : 'reviews'}</p>
            </div>
            {CRITERIA.map(({ key, label }) => (
              <div key={key} className="rounded-2xl border border-line p-4 min-w-0">
                <p className="font-display text-3xl font-bold">{feedback[key]?.toFixed(1)}</p>
                <p className="text-xs text-muted">{label}</p>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-t border-line pt-4">
              <p className="text-xs text-muted" role="status">
                {firstShown}–{firstShown + feedback.items.length - 1} of {feedback.count}
              </p>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  aria-label="Previous page"
                  className="p-1.5 rounded-lg text-muted hover:text-ink disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <div role="tablist" aria-label="Feedback pages" className="flex items-center gap-1 rounded-xl bg-paper border border-line p-1">
                  {visiblePages(page, totalPages).map((item, index) =>
                    item === 'gap' ? (
                      <span key={`gap-${index}`} className="px-1 text-xs text-muted" aria-hidden="true">…</span>
                    ) : (
                      <button
                        key={item}
                        role="tab"
                        aria-selected={item === page}
                        aria-label={`Page ${item}`}
                        onClick={() => setPage(item)}
                        className={`min-w-7 h-7 px-1.5 rounded-lg text-xs font-bold cursor-pointer transition-colors ${item === page ? 'nav-active' : 'text-muted hover:text-ink'}`}
                      >
                        {item}
                      </button>
                    ),
                  )}
                </div>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page === totalPages}
                  aria-label="Next page"
                  className="p-1.5 rounded-lg text-muted hover:text-ink disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          <ul className={`space-y-3 transition-opacity ${loadingPage ? 'opacity-50' : ''}`} aria-busy={loadingPage}>
            {feedback.items.map(item => (
              <li key={item.id} className="border-t border-line pt-4 space-y-2 first:border-t-0 first:pt-0">
                <div className="flex items-center gap-3 min-w-0">
                  <Avatar name={item.reviewerName} photoUrl={item.reviewerPhotoUrl} tone="learn" className="w-9 h-9 text-sm" />
                  <div className="min-w-0">
                    <p className="font-bold truncate">{item.reviewerName}</p>
                    <p className="text-xs text-muted truncate">{item.roomTitle} · {formatDate(item.createdAt)}</p>
                  </div>
                </div>
                <p className="text-sm text-muted">
                  {CRITERIA.map(({ key, label }) => `${label}: ${item[key]}/10`).join(' · ')}
                </p>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
};
