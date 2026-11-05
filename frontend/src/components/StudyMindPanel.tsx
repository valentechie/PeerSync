import React, { useState } from 'react';
import { Lightbulb, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { MAX_HELP_STEP, requestHelp, type StudyMindHelp } from '../services/studymind';
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
    <section className="card p-5 space-y-3" aria-label="StudyMind">
      <h2 className="text-lg text-ink flex items-center gap-2">
        <Lightbulb className="w-5 h-5 text-guide" aria-hidden="true" />
        <span>StudyMind</span>
      </h2>
      <p className="text-sm text-muted">Tus compañeros van primero. Solo actúa si lo pides, con ayuda gradual y sin dar la solución.</p>

      <div className="space-y-2">
        <label htmlFor="studymind-difficulty" className="label">¿Dónde te has atascado?</label>
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
            <span className="chip chip-guide">{help.source === 'ai' ? 'Sugerencia de IA' : 'Ayuda preparada, sin IA'}</span>
            <span className="text-xs font-bold">Paso {help.step} de {MAX_HELP_STEP}</span>
          </div>
          <p className="font-bold break-words">{help.message}</p>
          <p className="break-words"><strong>Qué puedes hacer:</strong> {help.suggestedAction}</p>
          <p className="text-xs text-muted break-words">{help.uncertaintyNote}</p>
        </div>
      )}

      {error && <ErrorState message={error} onRetry={() => void ask(nextStep)} />}

      {nextStep <= MAX_HELP_STEP ? (
        <button onClick={() => void ask(nextStep)} disabled={loading || !difficulty.trim()} className="btn btn-secondary w-full">
          {loading && <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />}
          <span>{loading ? 'Pensando...' : help ? 'Necesito otra pista' : 'Estoy bloqueado'}</span>
        </button>
      ) : (
        <button onClick={() => setHelp(null)} className="btn btn-secondary w-full">Empezar de nuevo</button>
      )}
    </section>
  );
};
