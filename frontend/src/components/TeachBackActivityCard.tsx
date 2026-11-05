import React from 'react';
import { Loader2, MessageSquareQuote } from 'lucide-react';
import {
  advanceActivity,
  leaveActivity,
  requestActivityFeedback,
  respondToActivity,
  skipSecondTurn,
  submitExplanation,
  submitReview,
  type Activity,
  type ActivityTurn,
} from '../services/contrastaFlow';
import { FeedbackList } from './TeachBackPanel';
import { ErrorState } from './UIStates';
import { useDraft, useFlowAction, useFlowContext } from './contrastaFlowContext';

const CARD = 'rounded-2xl border border-line bg-surface p-3 space-y-3 text-sm text-left w-full';

const TurnBlock: React.FC<{ activity: Activity; turn: ActivityTurn }> = ({ activity, turn }) => {
  const { token, roomId, userId, readOnly } = useFlowContext();
  const { busy, error, run } = useFlowAction();
  const ask = () => void run(() => requestActivityFeedback(token, roomId, activity.id, turn.turn));
  return (
    <div className="space-y-2">
      <div className="rounded-xl bg-teach-soft p-3 space-y-1">
        <p className="font-bold truncate">{turn.explainer.id === userId ? 'Your explanation' : `${turn.explainer.name}'s explanation`}</p>
        <p className="whitespace-pre-wrap break-words">{turn.explanation}</p>
      </div>
      {turn.review && (
        <div className="rounded-xl border border-line p-3 space-y-1">
          <span className="chip chip-teach">Review by {turn.review.reviewer.id === userId ? 'you' : turn.review.reviewer.name}</span>
          <p className="whitespace-pre-wrap break-words">{turn.review.comment}</p>
        </div>
      )}
      {turn.feedback && (
        <div className="rounded-xl bg-guide-soft p-3 space-y-2">
          <span className="chip chip-guide">AI suggestion, not a grade</span>
          <FeedbackList title="Strengths" items={turn.feedback.strengths} />
          <FeedbackList title="Possible gaps" items={turn.feedback.possibleGaps} />
          <FeedbackList title="Questions for your peer" items={turn.feedback.questionsForPeer} />
          <FeedbackList title="What to check" items={turn.feedback.evidenceToCheck} />
          <p className="break-words"><strong>Activity:</strong> {turn.feedback.suggestedPeerActivity}</p>
          <p className="text-xs text-muted break-words">{turn.feedback.uncertaintyNote}</p>
        </div>
      )}
      {error && <ErrorState message={error} onRetry={ask} />}
      {turn.review && !turn.feedback && !error && !readOnly && (
        <button type="button" onClick={ask} disabled={busy} className="btn btn-secondary w-full">
          {busy && <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />}
          <span>{busy ? 'Preparing suggestions...' : 'Ask for AI suggestions (optional)'}</span>
        </button>
      )}
    </div>
  );
};

const TextForm: React.FC<{ draftKey: string; id: string; label: string; submit: string; onSubmit: (text: string) => Promise<unknown> }> = ({
  draftKey,
  id,
  label,
  submit,
  onSubmit,
}) => {
  const [text, setText] = useDraft(draftKey);
  const { busy, error, run } = useFlowAction();
  return (
    <form
      onSubmit={e => {
        e.preventDefault();
        if (text.trim()) void run(() => onSubmit(text), () => setText(''));
      }}
      className="space-y-2"
    >
      <label htmlFor={id} className="label">{label}</label>
      <textarea id={id} value={text} onChange={e => setText(e.target.value)} maxLength={4000} rows={3} className="field" />
      {error && <ErrorState message={error} />}
      <button type="submit" disabled={busy || !text.trim()} className="btn btn-primary w-full">{busy ? 'Sending...' : submit}</button>
    </form>
  );
};

const ActiveStep: React.FC<{ activity: Activity }> = ({ activity }) => {
  const { token, roomId, userId } = useFlowContext();
  const { busy, error, run } = useFlowAction();
  const explainer = activity.turn === 1 ? activity.proposer : activity.partner;
  const reviewer = activity.turn === 1 ? activity.partner : activity.proposer;
  const current = activity.turns.find(turn => turn.turn === activity.turn);
  const iExplain = explainer.id === userId;

  return (
    <div className="space-y-3">
      {!current && iExplain && (
        <TextForm
          draftKey={`explanation:${activity.id}:${activity.turn}`}
          id={`explanation-${activity.id}`}
          label="Your own explanation"
          submit="Send explanation"
          onSubmit={text => submitExplanation(token, roomId, activity.id, text)}
        />
      )}
      {!current && !iExplain && <p className="text-muted" role="status">{explainer.name} is writing an explanation. You can keep chatting.</p>}
      {current && !current.review && !iExplain && (
        <TextForm
          draftKey={`review:${activity.id}:${activity.turn}`}
          id={`review-${activity.id}`}
          label="What did you understand? What would you ask?"
          submit="Send review"
          onSubmit={text => submitReview(token, roomId, activity.id, text)}
        />
      )}
      {current && !current.review && iExplain && <p className="text-muted" role="status">Waiting for {reviewer.name}'s review. The AI only comments afterwards.</p>}
      {error && <ErrorState message={error} />}
      {current?.review && (
        <button type="button" onClick={() => void run(() => advanceActivity(token, roomId, activity.id))} disabled={busy} className="btn btn-primary w-full">
          {activity.turn === 1 ? 'Switch roles' : 'Finish activity'}
        </button>
      )}
      {current?.review && activity.turn === 1 && (
        activity.skipRequestedByMe ? (
          <p className="text-xs text-muted" role="status">You suggested skipping the second turn. Waiting for your partner.</p>
        ) : (
          <button type="button" onClick={() => void run(() => skipSecondTurn(token, roomId, activity.id))} disabled={busy} className="btn btn-secondary w-full">
            {activity.skipRequestedByPartner ? 'Agree to skip the second turn' : 'Suggest skipping the second turn'}
          </button>
        )
      )}
      <button type="button" onClick={() => void run(() => leaveActivity(token, roomId, activity.id))} disabled={busy} className="btn btn-secondary w-full">
        Leave activity
      </button>
    </div>
  );
};

export const TeachBackActivityCard: React.FC<{ activity: Activity }> = ({ activity }) => {
  const { token, roomId, userId, readOnly, openForm, flow } = useFlowContext();
  const { busy, error, run } = useFlowAction();
  const iProposed = activity.proposer.id === userId;
  const other = iProposed ? activity.partner : activity.proposer;
  const respond = (decision: 'accept' | 'decline' | 'cancel') => void run(() => respondToActivity(token, roomId, activity.id, decision));

  return (
    <article id={`activity-${activity.id}`} className={CARD} aria-label="TeachBack activity">
      <div className="flex flex-wrap items-center gap-2">
        <MessageSquareQuote className="w-4 h-4 text-guide shrink-0" aria-hidden="true" />
        <span className="chip chip-teach">TeachBack</span>
        <span className="text-xs font-bold break-words min-w-0">{activity.concept}</span>
        {activity.status === 'active' && <span className="text-xs text-muted">Turn {activity.turn} of 2</span>}
      </div>

      {activity.status === 'pending' && (
        iProposed ? (
          <>
            <p className="text-muted" role="status">You proposed practising an explanation. Waiting for {other.name}. You can keep chatting.</p>
            {!readOnly && <button type="button" onClick={() => respond('cancel')} disabled={busy} className="btn btn-secondary w-full">Cancel proposal</button>}
          </>
        ) : (
          <>
            <p className="font-bold">{other.name} proposes practising an explanation. Will you join?</p>
            {!readOnly && (
              <div className="flex gap-2">
                <button type="button" onClick={() => respond('accept')} disabled={busy} className="btn btn-primary flex-1">Accept</button>
                <button type="button" onClick={() => respond('decline')} disabled={busy} className="btn btn-secondary flex-1">Not now</button>
              </div>
            )}
          </>
        )
      )}
      {activity.status === 'declined' && <p className="text-muted">{iProposed ? `${other.name} said not now.` : 'You said not now.'} No problem: the debate carries on.</p>}
      {activity.status === 'cancelled' && <p className="text-muted">This proposal was cancelled.</p>}
      {activity.status === 'stopped' && <p className="text-muted">This activity was stopped. What you wrote is still here.</p>}
      {activity.status === 'completed' && <p className="text-muted">Activity completed.</p>}

      {activity.turns.map(turn => <TurnBlock key={turn.turn} activity={activity} turn={turn} />)}

      {activity.status === 'active' && !readOnly && <ActiveStep activity={activity} />}
      {activity.status === 'completed' && !readOnly && !flow.check && (
        <button type="button" onClick={() => openForm('check')} className="btn btn-secondary w-full">Try a new question</button>
      )}
      {error && <ErrorState message={error} />}
    </article>
  );
};
