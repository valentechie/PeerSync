import React, { useEffect, useRef, useState } from 'react';
import { Mic, MicOff, Play, RotateCcw, Send, Square, Timer } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { fetchNextQuestion, type PracticeTurn } from '../services/practice';
import { ErrorState } from '../components/UIStates';

const MAX_HISTORY_TURNS = 40;

interface SpeechResultEvent {
  resultIndex: number;
  results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }>;
}

interface SpeechRecognizer {
  lang: string;
  continuous: boolean;
  onresult: ((event: SpeechResultEvent) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
}

type SpeechWindow = Window & {
  SpeechRecognition?: new () => SpeechRecognizer;
  webkitSpeechRecognition?: new () => SpeechRecognizer;
};

const formatSeconds = (seconds: number) => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;

export const Practice: React.FC = () => {
  const { token } = useAuth();
  const [topic, setTopic] = useState('');
  const [started, setStarted] = useState(false);
  const [finished, setFinished] = useState(false);
  const [history, setHistory] = useState<PracticeTurn[]>([]);
  const [draft, setDraft] = useState('');
  const [waiting, setWaiting] = useState(false);
  const [error, setError] = useState('');
  const [seconds, setSeconds] = useState(0);
  const [answerTimes, setAnswerTimes] = useState<number[]>([]);
  const [listening, setListening] = useState(false);
  const recognizer = useRef<SpeechRecognizer | null>(null);
  const chatRef = useRef<HTMLDivElement>(null);

  const speechWindow = window as SpeechWindow;
  const SpeechApi = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
  const awaitingAnswer = started && !finished && !waiting && history.length % 2 === 1;
  const reachedLimit = history.length >= MAX_HISTORY_TURNS - 1;

  useEffect(() => {
    if (!awaitingAnswer) return;
    const timer = setInterval(() => setSeconds(current => current + 1), 1000);
    return () => clearInterval(timer);
  }, [awaitingAnswer]);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [history, waiting]);

  useEffect(() => () => recognizer.current?.stop(), []);

  const stopListening = () => {
    recognizer.current?.stop();
    recognizer.current = null;
    setListening(false);
  };

  const askNext = async (conversation: PracticeTurn[]) => {
    if (!token) return;
    setWaiting(true);
    setError('');
    try {
      const { question } = await fetchNextQuestion(token, topic, conversation);
      setHistory([...conversation, { role: 'coach', content: question }]);
      setSeconds(0);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setWaiting(false);
    }
  };

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    setStarted(true);
    await askNext([]);
  };

  const handleAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    const answer = draft.trim();
    if (!answer || !awaitingAnswer) return;
    stopListening();
    const conversation: PracticeTurn[] = [...history, { role: 'student', content: answer }];
    setHistory(conversation);
    setAnswerTimes(current => [...current, seconds]);
    setDraft('');
    if (reachedLimit) {
      setFinished(true);
      return;
    }
    await askNext(conversation);
  };

  const retry = () => askNext(history.length % 2 === 0 ? history : history.slice(0, -1));

  const toggleListening = () => {
    if (listening) {
      stopListening();
      return;
    }
    if (!SpeechApi) return;
    const speech = new SpeechApi();
    speech.lang = 'en-US';
    speech.continuous = true;
    speech.onresult = event => {
      let text = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        if (event.results[i].isFinal) text += event.results[i][0].transcript;
      }
      if (text) setDraft(current => `${current} ${text.trim()}`.trim());
    };
    speech.onerror = () => {
      setError("Couldn't use the microphone. Check your browser's permission or type your answer.");
      setListening(false);
    };
    speech.onend = () => setListening(false);
    recognizer.current = speech;
    speech.start();
    setListening(true);
  };

  const finish = () => {
    stopListening();
    setFinished(true);
  };

  const restart = () => {
    stopListening();
    setStarted(false);
    setFinished(false);
    setHistory([]);
    setDraft('');
    setError('');
    setSeconds(0);
    setAnswerTimes([]);
  };

  const totalSeconds = answerTimes.reduce((sum, value) => sum + value, 0);

  return (
    <div className="page max-w-4xl space-y-6">
      <div>
        <h1 className="page-title">Practice</h1>
        <p className="page-subtitle">Train how you explain before doing it live. The AI asks you questions like a curious peer: it won't give you the answer or a grade.</p>
      </div>

      {error && <ErrorState message={error} onRetry={started && !finished && !waiting && !awaitingAnswer ? retry : undefined} />}

      {!started && (
        <form onSubmit={handleStart} className="card p-6 sm:p-8 space-y-4">
          <div>
            <label htmlFor="practice-topic" className="label">What do you want to explain?</label>
            <input
              id="practice-topic"
              required
              maxLength={120}
              value={topic}
              onChange={e => setTopic(e.target.value)}
              placeholder="E.g.: How an IP address works"
              className="field"
            />
          </div>
          <p className="text-xs text-muted">The topic and your answers are sent to Gemini, Google's AI. Don't enter personal data. The session isn't saved.</p>
          <button type="submit" disabled={!topic.trim()} className="btn btn-primary w-full">
            <Play className="w-4 h-4" aria-hidden="true" />
            <span>Start practising</span>
          </button>
        </form>
      )}

      {started && (
        <section className="card flex flex-col h-[62vh] min-h-96" aria-label="Practice session">
          <div className="flex items-center justify-between gap-3 p-4 border-b border-line">
            <h2 className="text-lg text-ink truncate min-w-0">{topic}</h2>
            {!finished && (
              <span className="flex items-center gap-3 shrink-0">
                <span className="text-sm font-bold text-muted flex items-center gap-1.5" aria-label="Time for this answer">
                  <Timer className="w-4 h-4" aria-hidden="true" />
                  <span>{formatSeconds(seconds)}</span>
                </span>
                <button onClick={finish} className="btn btn-secondary py-2!">
                  <Square className="w-3.5 h-3.5" aria-hidden="true" />
                  <span>Finish</span>
                </button>
              </span>
            )}
          </div>

          <div ref={chatRef} className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4" aria-live="polite">
            {history.map((turn, index) => (
              <div key={index} className={`flex ${turn.role === 'student' ? 'justify-end' : ''}`}>
                <p className={`max-w-[85%] whitespace-pre-wrap break-words px-4 py-3 rounded-2xl text-sm ${turn.role === 'student' ? 'bg-teach-soft rounded-br-sm' : 'bg-guide-soft rounded-bl-sm'}`}>
                  {turn.content}
                </p>
              </div>
            ))}
            {waiting && <p role="status" className="text-sm text-muted">The AI is thinking of the next question...</p>}
          </div>

          {finished ? (
            <div className="p-4 sm:p-6 border-t border-line space-y-3">
              <p className="font-bold">Session finished</p>
              <p className="text-sm text-muted">
                You answered {answerTimes.length} {answerTimes.length === 1 ? 'question' : 'questions'} in {formatSeconds(totalSeconds)}. To check whether it makes sense, try explaining it to someone in a room.
              </p>
              <button onClick={restart} className="btn btn-primary">
                <RotateCcw className="w-4 h-4" aria-hidden="true" />
                <span>Practise another topic</span>
              </button>
            </div>
          ) : (
            <form onSubmit={handleAnswer} className="p-4 border-t border-line flex items-end gap-2">
              <textarea
                rows={2}
                value={draft}
                onChange={e => setDraft(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    e.currentTarget.form?.requestSubmit();
                  }
                }}
                maxLength={2000}
                disabled={!awaitingAnswer}
                placeholder={SpeechApi ? 'Explain it in your own words, or press the microphone and speak...' : 'Explain it in your own words...'}
                aria-label="Your answer"
                className="field flex-1 min-w-0 resize-none"
              />
              {SpeechApi && (
                <button
                  type="button"
                  onClick={toggleListening}
                  disabled={!awaitingAnswer}
                  aria-pressed={listening}
                  aria-label={listening ? 'Stop dictating' : 'Dictate with the microphone'}
                  title={listening ? 'Stop dictating' : 'Dictate with the microphone'}
                  className="btn btn-secondary px-4!"
                >
                  {listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>
              )}
              <button type="submit" disabled={!awaitingAnswer || !draft.trim()} aria-label="Send answer" className="btn btn-primary px-4!">
                <Send className="w-4 h-4" />
              </button>
            </form>
          )}
        </section>
      )}
    </div>
  );
};
