import React from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Clock, ArrowRight } from 'lucide-react';

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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-black text-slate-900">Mis Sesiones</h1>
        <p className="text-sm text-slate-500">Historial de intercambios de conocimiento y salas de estudio activas</p>
      </div>

      <div className="space-y-4">
        {MOCK_SESSIONS.map(session => (
          <div key={session.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-3">
                <span className={`px-2.5 py-0.5 text-xs font-bold rounded-md ${
                  session.status === 'upcoming' 
                    ? 'bg-indigo-100 text-indigo-700' 
                    : 'bg-slate-100 text-slate-600'
                }`}>
                  {session.status === 'upcoming' ? 'Próxima' : 'Completada'}
                </span>
                <span className="text-xs text-slate-400 flex items-center space-x-1">
                  <Clock className="w-3.5 h-3.5 inline mr-1" />
                  <span>{session.time}</span>
                </span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 mt-1">{session.topic}</h3>
              <p className="text-sm text-slate-600">Compañero: <span className="font-semibold">{session.partnerName}</span></p>
            </div>

            <div className="flex items-center space-x-3">
              {session.status === 'upcoming' ? (
                <button
                  onClick={() => navigate(`/study-room/${session.id}`)}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl shadow-sm transition flex items-center space-x-2"
                >
                  <span>Entrar a la Sala</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  onClick={() => navigate(`/session-summary/${session.id}`)}
                  className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-sm rounded-xl transition flex items-center space-x-2"
                >
                  <BookOpen className="w-4 h-4" />
                  <span>Ver Resumen</span>
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
