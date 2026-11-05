import React, { useEffect, useState } from 'react';
import { CheckCircle2, Loader2, Scale } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import {
  fetchContrasta,
  requestFacilitation,
  startRound,
  submitAnswer,
  type ContrastaRound,
  type Facilitation,
} from '../services/contrasta';
import { CollapsiblePanel } from './CollapsiblePanel';
import { ErrorState } from './UIStates';

const POLL_INTERVAL_MS = 3000;
const MAX_TEXT_LENGTH = 2000;

const INTERVENTION_LABELS: Record<Facilitation['kind'], string> = {
  evidence_check: 'Look for evidence',
  edge_case: 'Try an edge case',
  missing_information: 'Information missing',
  open_question: 'Open question',
};

const Intervention: React.FC<{ intervention: Facilitation }> = ({ intervention }) => (
  <div className="rounded-2xl bg-guide-soft p-4 space-y-2 text-sm" aria-live="polite">
    <div className="flex flex-wrap items-center gap-2">
      <span className="chip chip-guide">{intervention.source === 'ai' ? 'AI suggestion' : 'Prepared question, no AI'}</span>
      <span className="text-xs font-bold">{INTERVENTION_LABELS[intervention.kind]}</span>
    </div>
    <p className="font-bold break-words">{intervention.messageToPeers}</p>
    <p className="break-words"><strong>What you can do:</strong> {intervention.suggestedAction}</p>
    <p className="break-words"><strong>What to check:</strong> {intervention.evidenceNeeded}</p>
    <p className="text-xs text-muted break-words">{intervention.uncertaintyNote}</p>
  </div>
);

export const ContrastaPanel: React.FC<{ roomId: string }> = ({ roomId }) => {
  const { token, user } = useAuth();
  const [round, setRound] = useState<ContrastaRound | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [promptDraft, setPromptDraft] = useState('');
  const [answerDraft, setAnswerDraft] = useState('');
  const [startingNew, setStartingNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [intervention, setIntervention] = useState<{ roundId: string; content: Facilitation } | null>(null);
  const [facilitating, setFacilitating] = useState(false);
  const [facilitateError, setFacilitateError] = useState('');

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    const refresh = async () => {
      try {
        const state = await fetchContrasta(token, roomId);
        if (cancelled) return;
        setRound(state.round);
        setLoaded(true);
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

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !promptDraft.trim()) return;
    setSaving(true);
    setError('');
    try {
      const state = await startRound(token, roomId, promptDraft);
      setRound(state.round);
      setPromptDraft('');
      setAnswerDraft('');
      setStartingNew(false);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !answerDraft.trim()) return;
    setSaving(true);
    setError('');
    try {
      const state = await submitAnswer(token, roomId, answerDraft);
      setRound(state.round);
      setAnswerDraft('');
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleFacilitate = async () => {
    if (!token || !round || facilitating) return;
    setFacilitating(true);
    setFacilitateError('');
    try {
      const content = await requestFacilitation(token, roomId);
      setIntervention({ roundId: round.id, content });
    } catch (err) {
      setFacilitateError(errorMessage(err));
    } finally {
      setFacilitating(false);
    }
  };

  const startForm = (
    <form onSubmit={handleStart} className="space-y-2">
      <label htmlFor="contrasta-prompt" className="label">Question or problem</label>
      <textarea
        id="contrasta-prompt"
        value={promptDraft}
        onChange={e => setPromptDraft(e.target.value)}
        maxLength={MAX_TEXT_LENGTH}
        rows={3}
        placeholder="What do you want to compare?"
        className="field"
      />
      <button type="submit" disabled={saving || !promptDraft.trim()} className="btn btn-primary w-full">
        {saving ? 'Starting...' : 'Start round'}
      </button>
    </form>
  );

  // Las rondas de pareja viven en la conversación; este panel es para comparar sin recorrido guiado.
  const pairInProgress = Boolean(round?.pairRound && !round.finishedAt);
  const compareOnlyRound = round?.pairRound ? null : round;
  const isRevealed = compareOnlyRound?.status === 'revealed';
  const currentIntervention = intervention && intervention.roundId === round?.id ? intervention.content : null;

  return (
    <CollapsiblePanel
      label="Compare answers only"
      openWhen={compareOnlyRound?.status === 'individual'}
      title={
        <>
          <Scale className="w-5 h-5 text-teach" aria-hidden="true" />
          <span>Compare answers only</span>
        </>
      }
      badge={compareOnlyRound?.status === 'individual' ? <span className="chip chip-teach">In progress</span> : undefined}
    >
      <p className="text-sm text-muted">
        Everyone in the room answers separately and compares, without guided steps. To learn with a partner, use "Start a round" in the chat menu.
      </p>

      {error && <ErrorState message={error} />}

      {!loaded && <p className="text-sm text-muted" role="status">Loading the round...</p>}

      {pairInProgress && <p className="text-sm font-bold">A pair round is in progress in the conversation.</p>}

      {loaded && !pairInProgress && !compareOnlyRound && startForm}

      {compareOnlyRound && (
        <p className="text-sm font-bold whitespace-pre-wrap break-words">{compareOnlyRound.prompt}</p>
      )}

      {compareOnlyRound && !isRevealed && (
        <>
          {compareOnlyRound.myAnswer === null ? (
            <form onSubmit={handleAnswer} className="space-y-2">
              <label htmlFor="contrasta-answer" className="label">Your answer and why</label>
              <textarea
                id="contrasta-answer"
                value={answerDraft}
                onChange={e => setAnswerDraft(e.target.value)}
                maxLength={MAX_TEXT_LENGTH}
                rows={4}
                placeholder="Nobody will see it until everyone has answered."
                className="field"
              />
              <button type="submit" disabled={saving || !answerDraft.trim()} className="btn btn-primary w-full">
                {saving ? 'Sending...' : 'Send answer'}
              </button>
            </form>
          ) : (
            <div className="rounded-2xl bg-teach-soft p-3 text-sm space-y-1">
              <p className="font-bold">Your answer, hidden for now</p>
              <p className="whitespace-pre-wrap break-words">{compareOnlyRound.myAnswer}</p>
            </div>
          )}
          <div className="text-sm text-muted space-y-1" aria-live="polite">
            {compareOnlyRound.answeredBy.map(person => (
              <p key={person.id} className="flex items-center gap-1.5 min-w-0">
                <CheckCircle2 className="w-4 h-4 text-teach shrink-0" aria-hidden="true" />
                <span className="truncate">{person.id === user?.id ? 'You have answered' : `${person.name} has answered`}</span>
              </p>
            ))}
            <p>
              {compareOnlyRound.waitingForCount === 1 ? 'Waiting for 1 person to answer.' : `Waiting for ${compareOnlyRound.waitingForCount} people to answer.`}
            </p>
          </div>
        </>
      )}

      {compareOnlyRound && isRevealed && (
        <>
          <ul className="space-y-2">
            {compareOnlyRound.answers.map(answer => (
              <li key={answer.userId} className="rounded-2xl bg-teach-soft p-3 text-sm space-y-1">
                <p className="font-bold truncate">{answer.userId === user?.id ? 'You' : answer.name}</p>
                <p className="whitespace-pre-wrap break-words">{answer.answer}</p>
              </li>
            ))}
          </ul>
          <p className="text-sm text-muted">Where do you agree, and where don't you? Talk it over in the chat. If it helps, ask for a comparison.</p>
          <button onClick={handleFacilitate} disabled={facilitating} className="btn btn-secondary w-full">
            {facilitating && <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />}
            <span>{facilitating ? 'Preparing the comparison...' : 'Suggest a comparison'}</span>
          </button>
          {facilitateError && <ErrorState message={facilitateError} onRetry={handleFacilitate} />}
          {currentIntervention && <Intervention intervention={currentIntervention} />}
          {startingNew ? startForm : (
            <button onClick={() => setStartingNew(true)} className="btn btn-secondary w-full">New round</button>
          )}
        </>
      )}
    </CollapsiblePanel>
  );
};
