import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Send, Lightbulb, CheckCircle2, MessageSquareQuote, MessageCircle, Flag } from 'lucide-react';
import { Avatar } from '../components/Swap';

interface Message {
  id: string;
  sender: string;
  text: string;
  time: string;
}

export const StudyRoom: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const me = user?.name ?? 'Tú';

  const [objective, setObjective] = useState('Dominar hooks avanzados de React y optimización con useCallback');
  const [messages, setMessages] = useState<Message[]>([
    { id: 'm-1', sender: 'María González', text: '¡Hola! ¿Listos para comenzar con el intercambio?', time: '18:00' },
    { id: 'm-2', sender: me, text: '¡Hola María! Sí, tengo listo el ejemplo de código con custom hooks.', time: '18:01' }
  ]);
  const [inputText, setInputText] = useState('');

  // StudyMind state
  const [hints, setHints] = useState<string[]>([]);
  const [loadingHint, setLoadingHint] = useState(false);

  // TeachBack state
  const [explanation, setExplanation] = useState('');
  const [feedback, setFeedback] = useState<{ score: string; clarity: string; correction: string; tips: string } | null>(null);
  const [loadingTeachBack, setLoadingTeachBack] = useState(false);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    setMessages(prev => [...prev, {
      id: String(Date.now()),
      sender: me,
      text: inputText,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }]);
    setInputText('');
  };

  const handleRequestHint = () => {
    setLoadingHint(true);
    setTimeout(() => {
      const nextHintNum = hints.length + 1;
      const newHint = nextHintNum === 1
        ? 'Pista 1 (StudyMind): Recuerda que useCallback memoriza la función entre renders solo si sus dependencias no cambian.'
        : nextHintNum === 2
        ? 'Pista 2 (StudyMind): Analiza si estás pasando funciones inline como props a componentes hijos altamente renderizados.'
        : 'Pista 3 (StudyMind): Utiliza React.memo en el componente hijo combinado con useCallback para evitar renders innecesarios.';
      setHints(prev => [...prev, newHint]);
      setLoadingHint(false);
    }, 800);
  };

  const handleTeachBackEval = () => {
    if (!explanation.trim()) return;
    setLoadingTeachBack(true);
    setTimeout(() => {
      setFeedback({
        score: 'Sobresaliente (Formativo)',
        clarity: 'Tu explicación es clara y estructurada. Has comprendido el propósito principal del hook.',
        correction: 'Correcto en su mayor parte, aunque recuerda mencionar el impacto en memoria.',
        tips: 'Buen uso de ejemplos prácticos. Intenta contrastarlo con useMemo cuando hables de cálculos costosos.'
      });
      setLoadingTeachBack(false);
    }, 1000);
  };

  const handleEndSession = () => {
    navigate(`/session-summary/${id || 'session-1'}`);
  };

  return (
    <div className="page max-w-7xl space-y-6">
      {/* Top Bar with Objective and Finish Button */}
      <div className="card p-5 sm:p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1.5 flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="chip chip-teach">Sala activa</span>
            <span className="text-xs text-muted">ID: {id || 'session-1'}</span>
          </div>
          <div className="flex items-center gap-2">
            <Flag className="w-4 h-4 text-teach shrink-0" />
            <input
              type="text"
              value={objective}
              onChange={e => setObjective(e.target.value)}
              aria-label="Objetivo de la sesión"
              className="font-display text-lg sm:text-xl font-semibold text-ink bg-transparent border-b border-transparent hover:border-line focus:border-teach focus:outline-none w-full"
            />
          </div>
        </div>
        <button onClick={handleEndSession} className="btn btn-secondary shrink-0 hover:border-learn! hover:text-learn-strong!">
          Finalizar sesión
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Section (2 cols) */}
        <section className="card lg:col-span-2 flex flex-col h-[600px]">
          <h2 className="p-4 border-b border-line text-lg text-ink flex items-center gap-2">
            <MessageCircle className="w-5 h-5 text-teach" />
            <span>Conversación con tu compañero</span>
            <span className="chip chip-demo font-sans ml-auto">Demo</span>
          </h2>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map(m => {
              const mine = m.sender === me;
              return (
                <div key={m.id} className={`flex items-end gap-2 ${mine ? 'flex-row-reverse' : ''}`}>
                  <Avatar name={m.sender} tone={mine ? 'teach' : 'learn'} className="w-8 h-8 text-sm" />
                  <div className={`max-w-[80%] space-y-1 ${mine ? 'text-right' : ''}`}>
                    <div className="flex items-baseline gap-2 text-xs justify-[inherit]">
                      <span className="font-bold">{m.sender}</span>
                      <span className="text-muted">{m.time}</span>
                    </div>
                    <div className={`inline-block text-left px-3.5 py-2.5 rounded-2xl text-sm ${mine ? 'bg-teach-soft rounded-br-sm' : 'bg-learn-soft rounded-bl-sm'}`}>
                      {m.text}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <form onSubmit={handleSendMessage} className="p-4 border-t border-line flex items-center gap-2">
            <input
              type="text"
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              placeholder="Escribe un mensaje o comparte código..."
              aria-label="Mensaje"
              className="field flex-1"
            />
            <button type="submit" aria-label="Enviar mensaje" className="btn btn-primary px-4!">
              <Send className="w-4 h-4" />
            </button>
          </form>
        </section>

        {/* AI Assistants Sidebar (1 col) */}
        <aside className="space-y-6" aria-label="Apoyo de IA">
          {/* StudyMind AI */}
          <section className="card p-5 space-y-4">
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-lg text-ink flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-guide" />
                <span>StudyMind AI</span>
              </h3>
              <span className="chip chip-demo">Demo</span>
            </div>
            <p className="text-sm text-muted">¿Bloqueado en algún concepto? Pide pistas progresivas paso a paso, solo cuando las necesites.</p>

            <div className="flex gap-1.5" role="img" aria-label={`${hints.length} de 3 pistas usadas`}>
              {[0, 1, 2].map(i => (
                <span key={i} className={`h-1.5 flex-1 rounded-full ${i < hints.length ? 'bg-guide' : 'bg-guide-soft'}`} />
              ))}
            </div>

            <button
              onClick={handleRequestHint}
              disabled={loadingHint || hints.length >= 3}
              className="btn btn-guide w-full"
            >
              {loadingHint ? 'Generando pista...' : hints.length === 0 ? 'Solicitar pista 1' : hints.length === 1 ? 'Solicitar pista 2' : hints.length === 2 ? 'Solicitar pista 3' : 'Máximo de pistas alcanzado'}
            </button>

            {hints.length > 0 && (
              <div className="space-y-2">
                {hints.map((h, i) => (
                  <div key={i} className="p-3 bg-guide-soft rounded-xl text-sm">
                    {h}
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* TeachBack AI */}
          <section className="card p-5 space-y-4">
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-lg text-ink flex items-center gap-2">
                <MessageSquareQuote className="w-5 h-5 text-guide" />
                <span>TeachBack AI</span>
              </h3>
              <span className="chip chip-demo">Demo</span>
            </div>
            <p className="text-sm text-muted">Explica el concepto con tus propias palabras para recibir feedback formativo.</p>

            <textarea
              rows={3}
              value={explanation}
              onChange={e => setExplanation(e.target.value)}
              placeholder="Explica el concepto aquí..."
              aria-label="Tu explicación del concepto"
              className="field"
            />

            <button
              onClick={handleTeachBackEval}
              disabled={loadingTeachBack || !explanation.trim()}
              className="btn btn-guide w-full"
            >
              {loadingTeachBack ? 'Evaluando explicación...' : 'Evaluar con TeachBack'}
            </button>

            {feedback && (
              <div className="p-3 bg-guide-soft rounded-xl space-y-2 text-sm">
                <div className="font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-guide shrink-0" />
                  <span>{feedback.score}</span>
                </div>
                <p><strong>Claridad:</strong> {feedback.clarity}</p>
                <p><strong>Corrección:</strong> {feedback.correction}</p>
                <p><strong>Recomendación:</strong> {feedback.tips}</p>
              </div>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
};
