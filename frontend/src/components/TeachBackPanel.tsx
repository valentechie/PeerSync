import React, { useEffect, useState } from 'react';
import { Loader2, MessageSquareQuote } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import {
  createPeerReview,
  createSubmission,
  fetchSubmissions,
  requestFeedback,
  type TeachBackFeedback,
  type TeachBackSubmission,
} from '../services/teachback';
import { CollapsiblePanel } from './CollapsiblePanel';
import { ErrorState } from './UIStates';

const POLL_INTERVAL_MS = 3000;
const MAX_TEXT_LENGTH = 4000;

export const FeedbackList: React.FC<{ title: string; items: string[] }> = ({ title, items }) =>
  items.length === 0 ? null : (
    <div>
      <p className="font-bold">{title}</p>
      <ul className="list-disc pl-5">
        {items.map(item => <li key={item} className="break-words">{item}</li>)}
      </ul>
    </div>
  );

const SubmissionCard: React.FC<{
  roomId: string;
  submission: TeachBackSubmission;
  onChange: (submission: TeachBackSubmission) => void;
}> = ({ roomId, submission, onChange }) => {
  const { token, user } = useAuth();
  const [comment, setComment] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [feedback, setFeedback] = useState<TeachBackFeedback | null>(null);
  const [asking, setAsking] = useState(false);
  const isMine = submission.explainerId === user?.id;

  const handleReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !comment.trim()) return;
    setSaving(true);
    setError('');
    try {
      onChange(await createPeerReview(token, roomId, submission.id, comment));
      setComment('');
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleFeedback = async () => {
    if (!token || asking) return;
    setAsking(true);
    setError('');
    try {
      setFeedback(await requestFeedback(token, roomId, submission.id));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setAsking(false);
    }
  };

  return (
    <li className="rounded-2xl border border-line p-3 space-y-3 text-sm">
      <div className="space-y-1">
        <p className="font-bold break-words">{submission.concept}</p>
        <p className="text-xs text-muted truncate">Explained by {isMine ? 'you' : submission.explainerName}</p>
        <p className="whitespace-pre-wrap break-words">{submission.explanation}</p>
      </div>

      {submission.review ? (
        <div className="rounded-xl bg-teach-soft p-3 space-y-1">
          <span className="chip chip-teach">Review by {submission.review.reviewerId === user?.id ? 'you' : submission.review.reviewerName}</span>
          <p className="whitespace-pre-wrap break-words">{submission.review.comment}</p>
        </div>
      ) : isMine ? (
        <p className="text-muted">Waiting for a peer's review. The AI only comments afterwards.</p>
      ) : (
        <form onSubmit={handleReview} className="space-y-2">
          <label htmlFor={`review-${submission.id}`} className="label">Summarise what you understood and your questions</label>
          <textarea
            id={`review-${submission.id}`}
            value={comment}
            onChange={e => setComment(e.target.value)}
            maxLength={MAX_TEXT_LENGTH}
            rows={3}
            className="field"
          />
          <button type="submit" disabled={saving || !comment.trim()} className="btn btn-primary w-full">
            {saving ? 'Sending...' : 'Send review'}
          </button>
        </form>
      )}

      {error && <ErrorState message={error} onRetry={submission.review ? () => void handleFeedback() : undefined} />}

      {submission.review && !feedback && (
        <button onClick={() => void handleFeedback()} disabled={asking} className="btn btn-secondary w-full">
          {asking && <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />}
          <span>{asking ? 'Preparing suggestions...' : 'Ask for AI suggestions'}</span>
        </button>
      )}

      {feedback && (
        <div className="rounded-xl bg-guide-soft p-3 space-y-2" aria-live="polite">
          <span className="chip chip-guide">AI suggestion, not a grade</span>
          <FeedbackList title="Strengths" items={feedback.strengths} />
          <FeedbackList title="Possible gaps" items={feedback.possibleGaps} />
          <FeedbackList title="Questions for your peer" items={feedback.questionsForPeer} />
          <FeedbackList title="What to check" items={feedback.evidenceToCheck} />
          <p className="break-words"><strong>Activity:</strong> {feedback.suggestedPeerActivity}</p>
          <p className="text-xs text-muted break-words">{feedback.uncertaintyNote}</p>
        </div>
      )}
    </li>
  );
};

export const TeachBackPanel: React.FC<{ roomId: string }> = ({ roomId }) => {
  const { token, user } = useAuth();
  const [submissions, setSubmissions] = useState<TeachBackSubmission[]>([]);
  const [concept, setConcept] = useState('');
  const [explanation, setExplanation] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    const refresh = async () => {
      try {
        const latest = await fetchSubmissions(token, roomId);
        if (!cancelled) setSubmissions(latest);
      } catch {
        // La sala ya avisa de la conexión perdida; aquí se reintenta en la siguiente consulta.
      }
    };
    void refresh();
    const timer = setInterval(refresh, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [token, roomId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !concept.trim() || !explanation.trim()) return;
    setSaving(true);
    setError('');
    try {
      const created = await createSubmission(token, roomId, concept, explanation);
      setSubmissions(current => [created, ...current]);
      setConcept('');
      setExplanation('');
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const replace = (updated: TeachBackSubmission) =>
    setSubmissions(current => current.map(item => (item.id === updated.id ? updated : item)));

  // Con el panel plegado, las explicaciones pendientes de revisar no deben quedar ocultas.
  const awaitingReview = submissions.filter(item => !item.review && item.explainerId !== user?.id).length;

  return (
    <CollapsiblePanel
      label="TeachBack"
      title={
        <>
          <MessageSquareQuote className="w-5 h-5 text-guide" aria-hidden="true" />
          <span>TeachBack</span>
        </>
      }
      badge={awaitingReview > 0 ? <span className="chip chip-teach">{awaitingReview} to review</span> : undefined}
    >
      <div className="space-y-1">
        <p className="text-sm text-muted">Explain a concept. A peer reviews it first; then you can ask the AI for suggestions.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-2">
        <label htmlFor="teachback-concept" className="label">Concept</label>
        <input id="teachback-concept" value={concept} onChange={e => setConcept(e.target.value)} maxLength={200} className="field" />
        <label htmlFor="teachback-explanation" className="label">Your explanation</label>
        <textarea
          id="teachback-explanation"
          value={explanation}
          onChange={e => setExplanation(e.target.value)}
          maxLength={MAX_TEXT_LENGTH}
          rows={3}
          className="field"
        />
        <button type="submit" disabled={saving || !concept.trim() || !explanation.trim()} className="btn btn-primary w-full">
          {saving ? 'Sending...' : 'Send explanation'}
        </button>
      </form>

      {error && <ErrorState message={error} />}

      {submissions.length > 0 && (
        <ul className="space-y-3">
          {submissions.map(submission => (
            <SubmissionCard key={submission.id} roomId={roomId} submission={submission} onChange={replace} />
          ))}
        </ul>
      )}
    </CollapsiblePanel>
  );
};
