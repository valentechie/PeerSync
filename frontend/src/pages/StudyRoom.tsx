import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, Sparkles, CheckCircle2, Award, Flag } from 'lucide-react';

interface Message {
  id: string;
  sender: string;
  text: string;
  time: string;
}

export const StudyRoom: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [objective, setObjective] = useState('Dominar hooks avanzados de React y optimización con useCallback');
  const [messages, setMessages] = useState<Message[]>([
    { id: 'm-1', sender: 'María González', text: '¡Hola! ¿Listos para comenzar con el intercambio?', time: '18:00' },
    { id: 'm-2', sender: 'Alex Developer', text: '¡Hola María! Sí, tengo listo el ejemplo de código con custom hooks.', time: '18:01' }
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
      sender: 'Alex Developer',
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Top Bar with Objective and Finish Button */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 bg-indigo-100 text-indigo-700 text-xs font-bold rounded-md">Sala Activa</span>
            <span className="text-xs text-slate-400">ID: {id || 'session-1'}</span>
          </div>
          <div className="flex items-center space-x-2">
            <Flag className="w-4 h-4 text-indigo-600 shrink-0" />
            <input
              type="text"
              value={objective}
              onChange={e => setObjective(e.target.value)}
              className="text-lg font-bold text-slate-900 bg-transparent border-b border-transparent hover:border-slate-300 focus:border-indigo-500 focus:outline-none w-full sm:w-auto"
            />
          </div>
        </div>
        <button
          onClick={handleEndSession}
          className="px-5 py-2.5 bg-rose-600 hover:bg-rose-700 text-white font-semibold text-sm rounded-xl shadow-sm transition shrink-0"
        >
          Finalizar Sesión
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Section (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 flex flex-col h-[600px] shadow-xs">
          <div className="p-4 border-b border-slate-100 font-bold text-slate-900">
            💬 Chat en vivo de la Sala
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map(m => (
              <div key={m.id} className="flex flex-col space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold text-slate-900">{m.sender}</span>
                  <span className="text-[10px] text-slate-400">{m.time}</span>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 max-w-lg">
                  {m.text}
                </div>
              </div>
            ))}
          </div>

          <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-100 flex items-center space-x-2">
            <input
              type="text"
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              placeholder="Escribe un mensaje o comparte código..."
              className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="submit"
              className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-sm transition flex items-center space-x-1"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>

        {/* AI Assistants Sidebar (1 col) */}
        <div className="space-y-6">
          {/* StudyMind AI */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-violet-900 flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-violet-600" />
                <span>StudyMind AI (Pistas)</span>
              </h3>
              <span className="text-xs text-slate-400">Bajo demanda</span>
            </div>
            <p className="text-xs text-slate-600">¿Bloqueado en algún concepto? Pide pistas progresivas paso a paso.</p>

            <button
              onClick={handleRequestHint}
              disabled={loadingHint || hints.length >= 3}
              className="w-full py-2.5 bg-violet-600 hover:bg-violet-700 disabled:bg-violet-300 text-white font-semibold text-xs rounded-xl shadow-sm transition"
            >
              {loadingHint ? 'Generando pista...' : hints.length === 0 ? 'Solicitar Pista 1' : hints.length === 1 ? 'Solicitar Pista 2' : hints.length === 2 ? 'Solicitar Pista 3' : 'Máximo de pistas alcanzado'}
            </button>

            {hints.length > 0 && (
              <div className="space-y-2 pt-2">
                {hints.map((h, i) => (
                  <div key={i} className="p-3 bg-violet-50 border border-violet-100 rounded-xl text-xs text-violet-900">
                    {h}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* TeachBack AI */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-emerald-900 flex items-center space-x-2">
                <Award className="w-4 h-4 text-emerald-600" />
                <span>TeachBack AI (Feedback)</span>
              </h3>
              <span className="text-xs text-slate-400">Formativo</span>
            </div>
            <p className="text-xs text-slate-600">Explica el concepto con tus propias palabras para recibir feedback formativo.</p>

            <textarea
              rows={3}
              value={explanation}
              onChange={e => setExplanation(e.target.value)}
              placeholder="Explica el concepto aquí..."
              className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />

            <button
              onClick={handleTeachBackEval}
              disabled={loadingTeachBack || !explanation.trim()}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300 text-white font-semibold text-xs rounded-xl shadow-sm transition"
            >
              {loadingTeachBack ? 'Evaluando explicación...' : 'Evaluar con TeachBack'}
            </button>

            {feedback && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl space-y-2 text-xs">
                <div className="font-bold text-emerald-900 flex items-center space-x-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 inline" />
                  <span>{feedback.score}</span>
                </div>
                <p className="text-emerald-800"><strong>Claridad:</strong> {feedback.clarity}</p>
                <p className="text-emerald-800"><strong>Corrección:</strong> {feedback.correction}</p>
                <p className="text-emerald-800"><strong>Recomendación:</strong> {feedback.tips}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
