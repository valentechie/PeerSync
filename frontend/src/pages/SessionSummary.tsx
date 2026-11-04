import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle2, MessageSquareQuote, ArrowRight, BookOpen } from 'lucide-react';

export const SessionSummary: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  return (
    <div className="page max-w-3xl">
      <div className="card p-6 sm:p-10 space-y-6 text-center">
        <div className="w-14 h-14 bg-teach-soft text-teach rounded-full flex items-center justify-center mx-auto">
          <CheckCircle2 className="w-7 h-7" />
        </div>

        <div className="space-y-2">
          <p className="text-sm text-muted">Sesión completada · ID: {id || 'session-1'}</p>
          <h1 className="page-title">Hoy aprendieron los dos</h1>
          <p className="text-muted max-w-lg mx-auto">
            Has completado exitosamente tu intercambio de conocimientos. Tu reputación ha incrementado y la sesión ha sido registrada.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left">
          <div className="p-5 bg-teach-soft/50 rounded-2xl space-y-2">
            <h2 className="font-sans text-sm font-extrabold tracking-normal flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-teach" />
              <span>Temas cubiertos</span>
            </h2>
            <p className="text-sm text-muted">React Avanzado, Custom Hooks, Optimización con useCallback y buenas prácticas.</p>
          </div>

          <div className="p-5 bg-guide-soft/60 rounded-2xl space-y-2">
            <h2 className="font-sans text-sm font-extrabold tracking-normal flex items-center gap-2">
              <MessageSquareQuote className="w-4 h-4 text-guide" />
              <span>Feedback de TeachBack AI</span>
              <span className="chip chip-demo ml-auto">Demo</span>
            </h2>
            <p className="text-sm text-muted">Evaluación formativa sobresaliente con excelente claridad en explicaciones.</p>
          </div>
        </div>

        <div className="flex flex-wrap justify-center gap-3">
          <button onClick={() => navigate('/my-sessions')} className="btn btn-secondary">
            Volver a mis sesiones
          </button>
          <button onClick={() => navigate('/dashboard')} className="btn btn-primary">
            <span>Ir al inicio</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
