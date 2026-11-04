import React from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Clock, ArrowRight } from 'lucide-react';
import { Avatar, SwapTopic } from '../components/Swap';

interface SessionItem {
  id: string;
  topic: string;
  partnerName: string;
  time: string;
  status: 'upcoming' | 'completed';
}

const MOCK_SESSIONS: SessionItem[] = [
  {
    id: 'session-1',
    topic: 'React Avanzado ⇄ Machine Learning',
    partnerName: 'María González',
    time: 'Hoy, 18:00 hrs',
    status: 'upcoming'
  },
  {
    id: 'session-2',
    topic: 'FastAPI & Endpoints ⇄ Tailwind CSS',
    partnerName: 'Carlos Ruiz',
    time: 'Ayer, 16:00 hrs',
    status: 'completed'
  },
  {
    id: 'session-3',
    topic: 'Algoritmos y Estructuras de Datos',
    partnerName: 'Lucía Fernández',
    time: 'Hace 3 días',
    status: 'completed'
  }
];

export const MySessions: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="page max-w-5xl space-y-8">
      <div>
        <h1 className="page-title flex items-center gap-3">
          <span>Mis sesiones</span>
          <span className="chip chip-demo font-sans">Demo</span>
        </h1>
        <p className="page-subtitle">Historial de intercambios de conocimiento y salas de estudio activas.</p>
      </div>

      <div className="space-y-4">
        {MOCK_SESSIONS.map(session => (
          <article
            key={session.id}
            className={`card p-6 flex flex-col md:flex-row md:items-center justify-between gap-5 ${session.status === 'upcoming' ? 'border-l-4 border-l-teach' : ''}`}
          >
            <div className="flex items-start gap-4">
              <Avatar name={session.partnerName} tone="learn" />
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span className={`chip ${session.status === 'upcoming' ? 'chip-teach' : 'bg-line/60 text-muted'}`}>
                    {session.status === 'upcoming' ? 'Próxima' : 'Completada'}
                  </span>
                  <span className="text-sm text-muted flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{session.time}</span>
                  </span>
                </div>
                <h2 className="font-sans text-base sm:text-lg font-bold tracking-normal"><SwapTopic topic={session.topic} /></h2>
                <p className="text-sm text-muted">Compañero: <span className="font-bold text-ink">{session.partnerName}</span></p>
              </div>
            </div>

            <div className="shrink-0">
              {session.status === 'upcoming' ? (
                <button onClick={() => navigate(`/study-room/${session.id}`)} className="btn btn-primary">
                  <span>Entrar a la sala</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              ) : (
                <button onClick={() => navigate(`/session-summary/${session.id}`)} className="btn btn-secondary">
                  <BookOpen className="w-4 h-4" />
                  <span>Ver resumen</span>
                </button>
              )}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
};
