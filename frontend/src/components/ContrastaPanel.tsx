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
import { ErrorState } from './UIStates';

const POLL_INTERVAL_MS = 3000;
const MAX_TEXT_LENGTH = 2000;

const INTERVENTION_LABELS: Record<Facilitation['kind'], string> = {
  evidence_check: 'Buscad evidencias',
  edge_case: 'Probad un caso límite',
  missing_information: 'Falta información',
  open_question: 'Cuestión abierta',
};

const Intervention: React.FC<{ intervention: Facilitation }> = ({ intervention }) => (
  <div className="rounded-2xl bg-guide-soft p-4 space-y-2 text-sm" aria-live="polite">
    <div className="flex flex-wrap items-center gap-2">
      <span className="chip chip-guide">{intervention.source === 'ai' ? 'Sugerencia de IA' : 'Pregunta preparada, sin IA'}</span>
      <span className="text-xs font-bold">{INTERVENTION_LABELS[intervention.kind]}</span>
    </div>
    <p className="font-bold break-words">{intervention.messageToPeers}</p>
    <p className="break-words"><strong>Qué podéis hacer:</strong> {intervention.suggestedAction}</p>
    <p className="break-words"><strong>Qué comprobar:</strong> {intervention.evidenceNeeded}</p>
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
      <label htmlFor="contrasta-prompt" className="label">Pregunta o enunciado</label>
      <textarea
        id="contrasta-prompt"
        value={promptDraft}
        onChange={e => setPromptDraft(e.target.value)}
        maxLength={MAX_TEXT_LENGTH}
        rows={3}
        placeholder="¿Qué queréis contrastar?"
        className="field"
      />
      <button type="submit" disabled={saving || !promptDraft.trim()} className="btn btn-primary w-full">
        {saving ? 'Empezando...' : 'Empezar ronda'}
      </button>
    </form>
  );

  const isRevealed = round?.status === 'revealed';
  const currentIntervention = intervention && intervention.roundId === round?.id ? intervention.content : null;

  return (
    <section className="card p-5 space-y-4" aria-label="Contrasta">
      <div className="space-y-1">
        <h2 className="text-lg text-ink flex items-center gap-2">
          <Scale className="w-5 h-5 text-teach" aria-hidden="true" />
          <span>Contrasta</span>
        </h2>
        <p className="text-sm text-muted">Respondéis por separado y comparáis cuando todos hayan enviado.</p>
      </div>

      {error && <ErrorState message={error} />}

      {!loaded && <p className="text-sm text-muted" role="status">Cargando la ronda...</p>}

      {loaded && !round && startForm}

      {round && (
        <p className="text-sm font-bold whitespace-pre-wrap break-words">{round.prompt}</p>
      )}

      {round && !isRevealed && (
        <>
          {round.myAnswer === null ? (
            <form onSubmit={handleAnswer} className="space-y-2">
              <label htmlFor="contrasta-answer" className="label">Tu respuesta y por qué</label>
              <textarea
                id="contrasta-answer"
                value={answerDraft}
                onChange={e => setAnswerDraft(e.target.value)}
                maxLength={MAX_TEXT_LENGTH}
                rows={4}
                placeholder="Nadie la verá hasta que todos hayan respondido."
                className="field"
              />
              <button type="submit" disabled={saving || !answerDraft.trim()} className="btn btn-primary w-full">
                {saving ? 'Enviando...' : 'Enviar respuesta'}
              </button>
            </form>
          ) : (
            <div className="rounded-2xl bg-teach-soft p-3 text-sm space-y-1">
              <p className="font-bold">Tu respuesta, oculta por ahora</p>
              <p className="whitespace-pre-wrap break-words">{round.myAnswer}</p>
            </div>
          )}
          <div className="text-sm text-muted space-y-1" aria-live="polite">
            {round.answeredBy.map(person => (
              <p key={person.id} className="flex items-center gap-1.5 min-w-0">
                <CheckCircle2 className="w-4 h-4 text-teach shrink-0" aria-hidden="true" />
                <span className="truncate">{person.id === user?.id ? 'Tú has respondido' : `${person.name} ha respondido`}</span>
              </p>
            ))}
            <p>
              {round.waitingForCount === 1 ? 'Falta 1 persona por responder.' : `Faltan ${round.waitingForCount} personas por responder.`}
            </p>
          </div>
        </>
      )}

      {round && isRevealed && (
        <>
          <ul className="space-y-2">
            {round.answers.map(answer => (
              <li key={answer.userId} className="rounded-2xl bg-teach-soft p-3 text-sm space-y-1">
                <p className="font-bold truncate">{answer.userId === user?.id ? 'Tú' : answer.name}</p>
                <p className="whitespace-pre-wrap break-words">{answer.answer}</p>
              </li>
            ))}
          </ul>
          <p className="text-sm text-muted">¿En qué coincidís y en qué no? Hablad en el chat. Si os ayuda, pedid un contraste.</p>
          <button onClick={handleFacilitate} disabled={facilitating} className="btn btn-secondary w-full">
            {facilitating && <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />}
            <span>{facilitating ? 'Preparando el contraste...' : 'Proponer contraste'}</span>
          </button>
          {facilitateError && <ErrorState message={facilitateError} onRetry={handleFacilitate} />}
          {currentIntervention && <Intervention intervention={currentIntervention} />}
          {startingNew ? startForm : (
            <button onClick={() => setStartingNew(true)} className="btn btn-secondary w-full">Nueva ronda</button>
          )}
        </>
      )}
    </section>
  );
};
