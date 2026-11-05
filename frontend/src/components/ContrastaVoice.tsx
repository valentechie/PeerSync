import React, { useState } from 'react';
import { Scale } from 'lucide-react';
import { savePrediction, type Flow, type Voice } from '../services/contrastaFlow';
import { ErrorState } from './UIStates';
import { useDraft, useFlowAction, useFlowContext } from './contrastaFlowContext';

const STARTERS = ['I think ', 'What if ', 'Can you give an example of ', "So you're saying "];

const readDismissed = (key: string) => {
  try {
    return localStorage.getItem(key) === 'closed';
  } catch {
    return false;
  }
};

const rememberDismissed = (key: string) => {
  try {
    localStorage.setItem(key, 'closed');
  } catch {
    // Sin almacenamiento, la decisión dura hasta recargar.
  }
};

/** Mismo formato que un mensaje, pero con su propio icono y sin relleno: no parece una persona. */
const VoiceBubble: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="flex items-end gap-2">
    <span className="w-8 h-8 shrink-0 rounded-full bg-teach-soft text-teach flex items-center justify-center" aria-hidden="true">
      <Scale className="w-4 h-4" />
    </span>
    <div className="max-w-[85%] min-w-0 space-y-1">
      <p className="text-xs font-bold">Contrasta</p>
      <div className="border border-line rounded-2xl rounded-bl-sm px-3.5 py-2.5 text-sm space-y-2 break-words">{children}</div>
    </div>
  </div>
);

const PredictionForm: React.FC<{ voice: Voice; flow: Flow }> = ({ voice, flow }) => {
  const { token, roomId, userId } = useFlowContext();
  const round = flow.round!;
  const storageKey = `peersync_voice:${userId}:${voice.key}`;
  const [closed, setClosed] = useState(() => readDismissed(storageKey));
  const [text, setText] = useDraft(`prediction:${round.id}`);
  const { busy, error, run } = useFlowAction();

  if (round.myPrediction !== null) {
    return <p>Your prediction is saved. You'll both see it when the answers appear.</p>;
  }
  if (closed) return <p>No problem: {round.partner.name}'s answer will appear when it's ready.</p>;
  return (
    <>
      <p className="font-bold">{voice.text}</p>
      <form
        onSubmit={e => {
          e.preventDefault();
          if (text.trim()) void run(() => savePrediction(token, roomId, text), () => setText(''));
        }}
        className="space-y-2"
      >
        <label htmlFor="round-prediction" className="label">Your prediction</label>
        <textarea id="round-prediction" value={text} onChange={e => setText(e.target.value)} maxLength={1000} rows={2} className="field" />
        {error && <ErrorState message={error} />}
        <div className="flex flex-wrap gap-2">
          <button type="submit" disabled={busy || !text.trim()} className="btn btn-primary flex-1">Save prediction</button>
          <button
            type="button"
            onClick={() => {
              rememberDismissed(storageKey);
              setClosed(true);
            }}
            className="btn btn-secondary"
          >
            Not now
          </button>
        </div>
      </form>
    </>
  );
};

export const ContrastaVoice: React.FC<{ voice: Voice; flow: Flow }> = ({ voice, flow }) => {
  const { readOnly, insertInComposer } = useFlowContext();
  if (voice.kind === 'prediction') {
    return readOnly ? null : <VoiceBubble><PredictionForm voice={voice} flow={flow} /></VoiceBubble>;
  }
  return (
    <VoiceBubble>
      <p>{voice.text}</p>
      {voice.kind === 'debate' && !readOnly && !flow.round?.finishedAt && (
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Sentence starters for the chat">
          {STARTERS.map(starter => (
            <button key={starter} type="button" onClick={() => insertInComposer(starter)} className="chip chip-teach cursor-pointer">
              {starter.trim()}…
            </button>
          ))}
        </div>
      )}
    </VoiceBubble>
  );
};

/** Invita a empezar, sin obligar: quien no quiera lo cierra y sigue hablando. */
export const WelcomeVoice: React.FC<{ flow: Flow }> = ({ flow }) => {
  const { userId, openForm, readOnly } = useFlowContext();
  const welcome = flow.welcome;
  const storageKey = `peersync_voice:${userId}:${welcome?.key}`;
  const [closedKey, setClosedKey] = useState<string | null>(null);
  const canStart = flow.actions.some(action => action.key === 'start' && action.enabled);
  if (!welcome || readOnly || !canStart || closedKey === storageKey || readDismissed(storageKey)) return null;
  return (
    <VoiceBubble>
      <p>{welcome.text}</p>
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => openForm('start')} className="btn btn-primary flex-1">Start a round</button>
        <button
          type="button"
          onClick={() => {
            rememberDismissed(storageKey);
            setClosedKey(storageKey);
          }}
          className="btn btn-secondary"
        >
          Not now
        </button>
      </div>
    </VoiceBubble>
  );
};
