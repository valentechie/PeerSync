import React, { useState } from 'react';
import { Lightbulb, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { MAX_HELP_STEP, requestHelp, type StudyMindHelp } from '../services/studymind';
import { CollapsiblePanel } from './CollapsiblePanel';
import { ErrorState } from './UIStates';

export const StudyMindPanel: React.FC<{ roomId: string }> = ({ roomId }) => {
  const { token } = useAuth();
  const [difficulty, setDifficulty] = useState('');
  const [help, setHelp] = useState<StudyMindHelp | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const nextStep = help ? help.step + 1 : 1;

  const ask = async (step: number) => {
    if (!token || !difficulty.trim() || loading) return;
    setLoading(true);
    setError('');
    try {
      setHelp(await requestHelp(token, roomId, difficulty, step));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <CollapsiblePanel
      label="StudyMind"
      bodyClassName="space-y-3"
      title={
        <>
          <Lightbulb className="w-5 h-5 text-guide" aria-hidden="true" />
          <span>StudyMind</span>
        </>
      }
    >
      <p className="text-sm text-muted">Your peers come first. It only steps in if you ask, with gradual help and without giving the solution.</p>

      <div className="space-y-2">
        <label htmlFor="studymind-difficulty" className="label">Where are you stuck?</label>
        <textarea
          id="studymind-difficulty"
          value={difficulty}
          onChange={e => {
            setDifficulty(e.target.value);
            setHelp(null);
          }}
          maxLength={1000}
          rows={2}
          className="field"
        />
      </div>

      {help && (
        <div className="rounded-2xl bg-guide-soft p-4 space-y-2 text-sm" aria-live="polite">
          <div className="flex flex-wrap items-center gap-2">
            <span className="chip chip-guide">{help.source === 'ai' ? 'AI suggestion' : 'Prepared help, no AI'}</span>
            <span className="text-xs font-bold">Step {help.step} of {MAX_HELP_STEP}</span>
          </div>
          <p className="font-bold break-words">{help.message}</p>
          <p className="break-words"><strong>What you can do:</strong> {help.suggestedAction}</p>
          <p className="text-xs text-muted break-words">{help.uncertaintyNote}</p>
        </div>
      )}

      {error && <ErrorState message={error} onRetry={() => void ask(nextStep)} />}

      {nextStep <= MAX_HELP_STEP ? (
        <button onClick={() => void ask(nextStep)} disabled={loading || !difficulty.trim()} className="btn btn-secondary w-full">
          {loading && <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />}
          <span>{loading ? 'Thinking...' : help ? 'I need another hint' : "I'm stuck"}</span>
        </button>
      ) : (
        <button onClick={() => setHelp(null)} className="btn btn-secondary w-full">Start over</button>
      )}
    </CollapsiblePanel>
  );
};
