import React, { useState } from 'react';
import { CheckCircle2, Lightbulb, Loader2, Scale, Search } from 'lucide-react';
import {
  answerCheck,
  answerRound,
  cancelRound,
  confirmConclusion,
  createCheck,
  finishRound,
  proposeActivity,
  recordConclusion,
  requestComparison,
  requestHelp,
  startPairRound,
  type Comparison,
  type Flow,
  type HelpCard,
  type Person,
} from '../services/contrastaFlow';
import { ErrorState } from './UIStates';
import { useDraft, useFlowAction, useFlowContext, type FormKey } from './contrastaFlowContext';

const COMPARISON_STALE_MS = 60_000;
const CARD = 'rounded-2xl border border-line bg-surface p-3 space-y-3 text-sm text-left w-full';
const GUIDANCE = 'text-sm text-muted';

export const ContrastaChip: React.FC = () => <span className="chip chip-teach">Contrasta</span>;

const ListBlock: React.FC<{ title: string; items: string[] }> = ({ title, items }) =>
  items.length === 0 ? null : (
    <div>
      <p className="font-bold">{title}</p>
      <ul className="list-disc pl-5">
        {items.map(item => <li key={item} className="break-words">{item}</li>)}
      </ul>
    </div>
  );

// Tarjetas de la ronda

export const RoundCard: React.FC<{ flow: Flow }> = ({ flow }) => {
  const { token, roomId, readOnly } = useFlowContext();
  const round = flow.round!;
  const [draft, setDraft] = useDraft(`answer:${round.id}`);
  const { busy, error, run } = useFlowAction();
  const cancelled = round.finishedAt !== null && round.status === 'individual';

  return (
    <article className={CARD} aria-label="Contrasta round">
      <div className="flex flex-wrap items-center gap-2">
        <ContrastaChip />
        <span className="text-xs font-bold">Round with {round.partner.name}</span>
      </div>
      <p className="font-bold whitespace-pre-wrap break-words">{round.prompt}</p>
      {cancelled && <p className={GUIDANCE}>This round was cancelled. The answers stay hidden.</p>}
      {!cancelled && round.status === 'individual' && (
        <>
          <p className={GUIDANCE}>First, each of you will answer independently. Your partner won't see your answer yet.</p>
          {round.myAnswer === null && !readOnly ? (
            <form
              onSubmit={e => {
                e.preventDefault();
                if (draft.trim()) void run(() => answerRound(token, roomId, draft), () => setDraft(''));
              }}
              className="space-y-2"
            >
              <label htmlFor={`answer-${round.id}`} className="label">Your answer and why</label>
              <textarea id={`answer-${round.id}`} value={draft} onChange={e => setDraft(e.target.value)} maxLength={2000} rows={3} className="field" />
              <button type="submit" disabled={busy || !draft.trim()} className="btn btn-primary w-full">
                {busy ? 'Sending...' : 'Send answer'}
              </button>
            </form>
          ) : round.myAnswer !== null && (
            <div className="rounded-xl bg-teach-soft p-3 space-y-1">
              <p className="font-bold">Your answer, hidden for now</p>
              <p className="whitespace-pre-wrap break-words">{round.myAnswer}</p>
            </div>
          )}
          <p className="text-xs text-muted" role="status">
            {!round.partnerPresent
              ? `${round.partner.name} has left the room, so this round can't be revealed.`
              : round.partnerHasAnswered
                ? `${round.partner.name} has answered. ${round.iHaveAnswered ? '' : 'Their answer stays hidden until you send yours.'}`
                : `Waiting for ${round.partner.name} to answer.`}
          </p>
          {error && <ErrorState message={error} />}
          {!readOnly && (
            <button type="button" onClick={() => void run(() => cancelRound(token, roomId))} disabled={busy} className="btn btn-secondary w-full">
              Cancel round
            </button>
          )}
        </>
      )}
    </article>
  );
};

const ComparisonBlock: React.FC<{ comparison: Comparison | null }> = ({ comparison }) => {
  const { token, roomId, readOnly, focusComposer } = useFlowContext();
  const { busy, error, run } = useFlowAction();
  const compare = () => void run(() => requestComparison(token, roomId));
  const stale = comparison?.status === 'pending' && Date.now() - Date.parse(comparison.updatedAt) > COMPARISON_STALE_MS;
  const inProgress = comparison?.status === 'pending' && !stale;

  if (comparison?.status === 'ready' && comparison.result) {
    const { result } = comparison;
    return (
      <div className="rounded-xl bg-guide-soft p-3 space-y-2">
        <span className="chip chip-guide">AI suggestion, not a verdict</span>
        <ListBlock title="Where the reasoning matches" items={result.agreements} />
        <ListBlock title="Differences worth examining" items={result.differences} />
        <ListBlock title="Questions to go deeper" items={result.questions} />
        <ListBlock title="Claims to verify" items={result.claimsToVerify} />
        <p className="text-xs text-muted break-words">{result.uncertaintyNote}</p>
        {!readOnly && (
          <button type="button" onClick={focusComposer} className="btn btn-secondary w-full">Discuss in chat</button>
        )}
      </div>
    );
  }
  if (readOnly) return null;
  return (
    <div className="space-y-2">
      {(error || comparison?.status === 'failed') && (
        <ErrorState message={error || "The AI isn't available right now. You can try again and keep talking."} onRetry={compare} />
      )}
      {inProgress ? (
        <p className="flex items-center gap-2 text-muted" role="status">
          <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
          <span>Comparison requested by {comparison.requestedByName}. You can keep talking.</span>
        </p>
      ) : (
        comparison?.status !== 'failed' && !error && (
          <>
            <button type="button" onClick={compare} disabled={busy} className="btn btn-secondary w-full">
              {busy && <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />}
              <span>Compare with AI</span>
            </button>
            <p className="text-xs text-muted">Optional. Your revealed answers are sent to DeepSeek, and both of you will see the result.</p>
          </>
        )
      )}
    </div>
  );
};

export const RevealCard: React.FC<{ flow: Flow }> = ({ flow }) => {
  const { userId, readOnly } = useFlowContext();
  const round = flow.round!;
  return (
    <article className={CARD} aria-label="Revealed answers">
      <ContrastaChip />
      <p className="font-bold">Both answers are ready. Read each other's reasoning. Where do you agree? What would you like to verify?</p>
      <ul className="space-y-2">
        {round.answers.map(answer => (
          <li key={answer.userId} className="rounded-xl bg-teach-soft p-3 space-y-1">
            <p className="font-bold truncate">{answer.userId === userId ? 'You' : answer.name}</p>
            <p className="whitespace-pre-wrap break-words">{answer.answer}</p>
          </li>
        ))}
      </ul>
      {!readOnly && !round.finishedAt && <p className={GUIDANCE}>Need another perspective? You can request a hint or a way to test your ideas.</p>}
      <ComparisonBlock comparison={flow.comparison} />
    </article>
  );
};

export const HelpResultCard: React.FC<{ card: HelpCard }> = ({ card }) => {
  const { userId } = useFlowContext();
  const Icon = card.kind === 'hint' ? Lightbulb : Search;
  return (
    <article className="rounded-2xl bg-guide-soft p-3 space-y-2 text-sm text-left w-full" aria-label="StudyMind">
      <div className="flex flex-wrap items-center gap-2">
        <Icon className="w-4 h-4 text-guide shrink-0" aria-hidden="true" />
        <span className="chip chip-guide">AI suggestion</span>
        <span className="text-xs font-bold">{card.kind === 'hint' ? 'Hint' : 'A way to check it'}</span>
        {card.private && <span className="text-xs font-bold">· Only you can see this</span>}
      </div>
      <p className="text-xs text-muted break-words">{card.author.id === userId ? 'You' : card.author.name} asked: {card.request}</p>
      <p className="font-bold break-words">{card.result.message}</p>
      <p className="break-words"><strong>What you can do:</strong> {card.result.suggestedAction}</p>
      <p className="text-xs text-muted break-words">{card.result.uncertaintyNote}</p>
    </article>
  );
};

const FinishRoundButton: React.FC<{ flow: Flow }> = ({ flow }) => {
  const { token, roomId } = useFlowContext();
  const { busy, error, run } = useFlowAction();
  const round = flow.round!;
  if (round.status !== 'revealed' || round.finishedAt) return null;
  return (
    <div className="space-y-2">
      {error && <ErrorState message={error} />}
      {round.finishRequestedByMe ? (
        <p className="text-xs text-muted" role="status">Waiting for {round.partner.name} to agree to finish. You can keep talking.</p>
      ) : (
        <>
          {round.finishRequestedByPartner && <p className="text-xs text-muted">{round.partner.name} would like to finish this round.</p>}
          <button type="button" onClick={() => void run(() => finishRound(token, roomId))} disabled={busy} className="btn btn-secondary w-full">
            {round.finishRequestedByPartner ? 'Agree and finish round' : 'Finish round'}
          </button>
        </>
      )}
    </div>
  );
};

export const ConclusionCard: React.FC<{ flow: Flow }> = ({ flow }) => {
  const { token, roomId, userId, readOnly, openForm } = useFlowContext();
  const { busy, error, run } = useFlowAction();
  const round = flow.round!;
  const conclusion = round.conclusion!;
  const mine = conclusion.by.id === userId;
  return (
    <article className={CARD} aria-label="Conclusion">
      <div className="flex flex-wrap items-center gap-2">
        <CheckCircle2 className="w-4 h-4 text-teach shrink-0" aria-hidden="true" />
        <ContrastaChip />
        <span className="text-xs font-bold">{conclusion.confirmedAt ? 'Shared conclusion' : `Conclusion by ${mine ? 'you' : conclusion.by.name}`}</span>
      </div>
      <p className="whitespace-pre-wrap break-words">{conclusion.text}</p>
      {error && <ErrorState message={error} />}
      {!readOnly && !round.finishedAt && (
        <>
          {!conclusion.confirmedAt && (
            mine ? (
              <p className="text-xs text-muted" role="status">Waiting for {round.partner.name} to confirm it.</p>
            ) : (
              <>
                <button type="button" onClick={() => void run(() => confirmConclusion(token, roomId))} disabled={busy} className="btn btn-primary w-full">
                  I agree
                </button>
                <p className="text-xs text-muted">Not quite? Talk it over, or record another one from the menu.</p>
              </>
            )
          )}
          {!flow.check && (
            <button type="button" onClick={() => openForm('check')} className="btn btn-secondary w-full">Try a new question</button>
          )}
          <FinishRoundButton flow={flow} />
        </>
      )}
    </article>
  );
};

// Sugerencias

const suggestionKey = (userId: string, roundId: string, key: string) => `peersync_suggestion:${userId}:${roundId}:${key}`;

const readSuggestionState = (storageKey: string) => {
  try {
    return localStorage.getItem(storageKey);
  } catch {
    return null;
  }
};

const SUGGESTIONS = {
  teachback: {
    text: 'Would you like to check your understanding by explaining the concept to each other?',
    action: 'Propose explanation',
    form: 'practice',
  },
  check: {
    text: "Now try a new question individually to see what you've learned.",
    action: 'Try a question',
    form: 'check',
  },
} as const;

/** Cerrar o posponer solo afecta a quien lo hace: el estado compartido no cambia. */
export const SuggestionCard: React.FC<{ flow: Flow }> = ({ flow }) => {
  const { userId, readOnly, openForm } = useFlowContext();
  const suggestion = flow.suggestion!;
  const storageKey = suggestionKey(userId, flow.round!.id, suggestion.key);
  const [state, setState] = useState(() => readSuggestionState(storageKey));
  const content = SUGGESTIONS[suggestion.key];

  const remember = (next: string | null) => {
    setState(next);
    try {
      if (next) localStorage.setItem(storageKey, next);
      else localStorage.removeItem(storageKey);
    } catch {
      // Sin almacenamiento, la decisión dura hasta recargar.
    }
  };

  if (state === 'closed' || readOnly) return null;
  if (state === 'later') {
    return (
      <p className="flex flex-wrap items-center gap-2 text-xs text-muted text-left w-full">
        <Scale className="w-4 h-4 text-teach shrink-0" aria-hidden="true" />
        <span>Contrasta has a suggestion for later.</span>
        <button type="button" onClick={() => remember(null)} className="font-bold text-teach-strong cursor-pointer">Show it</button>
      </p>
    );
  }
  return (
    <article className={CARD} aria-label="Contrasta suggestion">
      <ContrastaChip />
      <p className="font-bold">{content.text}</p>
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => openForm(content.form)} className="btn btn-primary flex-1">{content.action}</button>
        <button type="button" onClick={() => remember('later')} className="btn btn-secondary">Later</button>
        <button type="button" onClick={() => remember('closed')} className="btn btn-secondary">Close</button>
      </div>
    </article>
  );
};

// Comprobación individual

export const CheckCard: React.FC<{ flow: Flow }> = ({ flow }) => {
  const { token, roomId, userId, readOnly } = useFlowContext();
  const check = flow.check!;
  const round = flow.round!;
  const [answer, setAnswer] = useDraft(`check:${round.id}`);
  const [reflection, setReflection] = useDraft(`reflection:${round.id}`);
  const { busy, error, run } = useFlowAction();
  const both = check.iHaveAnswered && check.partnerHasAnswered;
  const firstAnswer = (id: string) => round.answers.find(item => item.userId === id)?.answer;

  return (
    <article className={CARD} aria-label="Individual check">
      <div className="flex flex-wrap items-center gap-2">
        <ContrastaChip />
        {check.source === 'ai'
          ? <span className="chip chip-guide">AI-generated question, it may contain mistakes</span>
          : <span className="text-xs font-bold">Question written by a peer</span>}
      </div>
      <p className="font-bold whitespace-pre-wrap break-words">{check.question}</p>
      <p className="text-xs text-muted">Answer on your own. This isn't a grade or an objective measure of learning.</p>
      {!check.iHaveAnswered && !readOnly && (
        <form
          onSubmit={e => {
            e.preventDefault();
            if (answer.trim()) {
              void run(() => answerCheck(token, roomId, answer, reflection), () => {
                setAnswer('');
                setReflection('');
              });
            }
          }}
          className="space-y-2"
        >
          <label htmlFor="check-answer" className="label">Your answer</label>
          <textarea id="check-answer" value={answer} onChange={e => setAnswer(e.target.value)} maxLength={4000} rows={3} className="field" />
          <label htmlFor="check-reflection" className="label">What changed in your reasoning? (optional)</label>
          <textarea id="check-reflection" value={reflection} onChange={e => setReflection(e.target.value)} maxLength={1000} rows={2} className="field" />
          <button type="submit" disabled={busy || !answer.trim()} className="btn btn-primary w-full">{busy ? 'Sending...' : 'Send answer'}</button>
        </form>
      )}
      {error && <ErrorState message={error} />}
      {check.iHaveAnswered && !both && (
        <p className="text-xs text-muted" role="status">Your answer is saved. {round.partner.name}'s stays hidden until they answer too.</p>
      )}
      {check.answers.length > 0 && (
        <ul className="space-y-2">
          {check.answers.map(item => (
            <li key={item.person.id} className="rounded-xl bg-teach-soft p-3 space-y-1">
              <p className="font-bold truncate">{item.person.id === userId ? 'You' : item.person.name}</p>
              {firstAnswer(item.person.id) && (
                <p className="text-xs text-muted whitespace-pre-wrap break-words">First answer: {firstAnswer(item.person.id)}</p>
              )}
              <p className="whitespace-pre-wrap break-words">{item.answer}</p>
              {item.reflection && <p className="text-xs whitespace-pre-wrap break-words"><strong>What changed:</strong> {item.reflection}</p>}
            </li>
          ))}
        </ul>
      )}
      {both && <p className={GUIDANCE}>Compare what you wrote at the start and now. What would you explain differently?</p>}
    </article>
  );
};

// Formulario que abre el menú, al final de la conversación

const FORM_TEXT: Record<Exclude<FormKey, 'check' | 'start'>, { title: string; label: string; submit: string; max: number }> = {
  hint: { title: 'We need a hint', label: 'Where are you stuck?', submit: 'Ask for a hint', max: 1000 },
  idea: { title: 'Check an idea', label: 'What idea do you want to check?', submit: 'Suggest a way to check it', max: 1000 },
  practice: { title: 'Practice an explanation', label: 'What concept will you explain?', submit: 'Propose to your partner', max: 200 },
  conclusion: { title: "We've reached a conclusion", label: 'What have you concluded together?', submit: 'Record conclusion', max: 4000 },
};

export const ActionForm: React.FC<{ form: FormKey; flow: Flow; others: Person[]; onClose: () => void }> = ({ form, flow, others, onClose }) => {
  const { token, roomId } = useFlowContext();
  const [text, setText] = useDraft(`form:${roomId}:${form}`, form === 'conclusion' ? flow.round?.conclusion?.text ?? '' : '');
  const [partnerId, setPartnerId] = useState(others[0]?.id ?? '');
  const { busy, error, run } = useFlowAction();
  const done = () => {
    setText('');
    onClose();
  };

  const submit = () => {
    if (!text.trim()) return;
    if (form === 'start') void run(() => startPairRound(token, roomId, text, partnerId), done);
    else if (form === 'hint' || form === 'idea') void run(() => requestHelp(token, roomId, form, text), done);
    else if (form === 'practice') void run(() => proposeActivity(token, roomId, text), done);
    else if (form === 'conclusion') void run(() => recordConclusion(token, roomId, text), done);
    else void run(() => createCheck(token, roomId, text), done);
  };

  const content =
    form === 'start'
      ? { title: 'Start a round', label: 'Question or problem', submit: 'Start round', max: 2000 }
      : form === 'check'
        ? { title: 'Try a new question', label: 'Write a question that applies the same idea to a new case', submit: 'Use this question', max: 1000 }
        : FORM_TEXT[form];
  const isPrivateHint = form === 'hint' && flow.round?.status === 'individual';

  return (
    <form
      onSubmit={e => {
        e.preventDefault();
        submit();
      }}
      className={CARD}
      aria-label={content.title}
    >
      <div className="flex flex-wrap items-center gap-2">
        <ContrastaChip />
        <span className="text-xs font-bold">{content.title}</span>
      </div>
      {form === 'start' && others.length > 1 && (
        <div>
          <label htmlFor="round-partner" className="label">Your partner</label>
          <select id="round-partner" value={partnerId} onChange={e => setPartnerId(e.target.value)} className="field">
            {others.map(person => <option key={person.id} value={person.id}>{person.name}</option>)}
          </select>
        </div>
      )}
      <div>
        <label htmlFor={`action-${form}`} className="label">{content.label}</label>
        <textarea id={`action-${form}`} autoFocus value={text} onChange={e => setText(e.target.value)} maxLength={content.max} rows={form === 'practice' ? 1 : 3} className="field" />
      </div>
      {form === 'start' && <p className="text-xs text-muted">You and your partner will each answer separately, then compare.</p>}
      {isPrivateHint && <p className="text-xs text-muted">Only you will see this hint. It won't use your partner's answer.</p>}
      {error && (
        <ErrorState
          message={error}
          onRetry={form === 'hint' || form === 'idea' ? submit : undefined}
        />
      )}
      <div className="flex flex-wrap gap-2">
        <button type="submit" disabled={busy || !text.trim()} className="btn btn-primary flex-1">
          {busy && <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />}
          <span>{content.submit}</span>
        </button>
        {form === 'check' && (
          <button type="button" onClick={() => void run(() => createCheck(token, roomId), done)} disabled={busy} className="btn btn-secondary flex-1">
            Suggest with AI
          </button>
        )}
        <button type="button" onClick={onClose} disabled={busy} className="btn btn-secondary">Cancel</button>
      </div>
    </form>
  );
};

// Lateral

export const SessionCard: React.FC<{ flow: Flow }> = ({ flow }) => {
  const { readOnly } = useFlowContext();
  const round = flow.round;
  const active = round && !round.finishedAt;
  if (!active && !flow.otherPairInProgress) return null;
  return (
    <section className="card p-5 space-y-3" aria-label="Session">
      <h2 className="text-lg text-ink flex items-center gap-2">
        <Scale className="w-5 h-5 text-teach" aria-hidden="true" />
        <span>Session</span>
      </h2>
      {flow.otherPairInProgress && <p className="text-sm text-muted">Two people in this room are working on a round. You can keep chatting.</p>}
      {active && (
        <>
          {flow.step && <span className="chip chip-teach">Step {flow.step.number} of 6 · {flow.step.label}</span>}
          <p className="text-sm font-bold whitespace-pre-wrap break-words">{round.prompt}</p>
          <p className="text-sm text-muted">With {round.partner.name}{round.partnerPresent ? '' : ', who has left the room'}</p>
          {!readOnly && <FinishRoundButton flow={flow} />}
        </>
      )}
    </section>
  );
};
