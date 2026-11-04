import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ArrowRight, ArrowLeftRight, BookOpen, Lightbulb, MessageSquareQuote, Star } from 'lucide-react';
import { SkillList } from '../components/Swap';
import { EmptyState } from '../components/UIStates';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="page max-w-7xl space-y-6">
      {/* Welcome */}
      <section className="card p-6 sm:p-10 grid lg:grid-cols-2 gap-8 lg:gap-12 items-center">
        <div className="space-y-5">
          <h1 className="text-4xl sm:text-5xl text-ink leading-tight">
            Hola, {user?.name || 'Estudiante'}.
          </h1>
          <p className="text-lg text-muted leading-relaxed max-w-xl">
            Lo que tú sabes le sirve a alguien, y lo que te falta, alguien más lo sabe. Encuentra a tu compañero de estudio y aprendan juntos.
          </p>
          <div className="flex flex-wrap gap-3">
            <button onClick={() => navigate('/find-partners')} className="btn btn-primary">
              <span>Buscar compañeros</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button onClick={() => navigate('/my-sessions')} className="btn btn-secondary">
              Ver mis sesiones
            </button>
          </div>
        </div>

        {/* Your exchange */}
        <div className="space-y-3">
          <div className="grid sm:grid-cols-[1fr_auto_1fr] gap-4 items-center">
            <div className="rounded-2xl bg-teach-soft/50 p-5 h-full">
              <SkillList title="Puedes enseñar" skills={user?.skillsOffering} tone="teach" />
            </div>
            <ArrowLeftRight className="w-5 h-5 text-muted justify-self-center rotate-90 sm:rotate-0" aria-hidden="true" />
            <div className="rounded-2xl bg-learn-soft/50 p-5 h-full">
              <SkillList title="Quieres aprender" skills={user?.skillsSeeking} tone="learn" />
            </div>
          </div>
          <button onClick={() => navigate('/my-profile')} className="block ml-auto text-sm font-bold text-teach underline underline-offset-2 hover:text-teach-strong cursor-pointer">
            Editar mis habilidades
          </button>
        </div>
      </section>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Next session */}
          <EmptyState
            title="Aún no tienes sesiones"
            description="Las sesiones de estudio todavía no están disponibles. Mientras tanto, ya puedes buscar compañeros y enviarles solicitudes."
          />

          {/* Quick stats */}
          <div className="grid sm:grid-cols-2 gap-6">
            <div className="card p-6 flex items-center gap-4">
              <BookOpen className="w-6 h-6 text-teach shrink-0" />
              <div>
                <p className="font-display text-3xl font-semibold">{user?.completedSessions ?? 0}</p>
                <p className="text-sm text-muted">Sesiones completadas</p>
              </div>
            </div>
            <div className="card p-6 flex items-center gap-4">
              <Star className="w-6 h-6 fill-sun text-sun shrink-0" />
              <div>
                <p className="font-display text-3xl font-semibold">{user?.reputation?.toFixed(1) ?? '—'}</p>
                <p className="text-sm text-muted">
                  {user?.reputation == null ? 'Aún sin valoraciones de compañeros' : 'Reputación entre compañeros'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* AI support */}
        <section className="card p-6 sm:p-8 space-y-5">
          <div>
            <h2 className="text-2xl text-ink flex items-center gap-2">
              <span>Apoyo cuando lo pidas</span>
              <span className="chip chip-demo font-sans">Próximamente</span>
            </h2>
            <p className="text-sm text-muted mt-1">Tu compañero va primero. La IA ayuda solo si la necesitas.</p>
          </div>
          <div className="flex gap-3 border-t border-line pt-5">
            <Lightbulb className="w-5 h-5 text-guide shrink-0 mt-0.5" />
            <div>
              <h3 className="font-sans text-sm font-extrabold tracking-normal">StudyMind AI</h3>
              <p className="text-sm text-muted mt-0.5">Pistas progresivas bajo demanda sin revelar la solución completa.</p>
            </div>
          </div>
          <div className="flex gap-3">
            <MessageSquareQuote className="w-5 h-5 text-guide shrink-0 mt-0.5" />
            <div>
              <h3 className="font-sans text-sm font-extrabold tracking-normal">TeachBack AI</h3>
              <p className="text-sm text-muted mt-0.5">Feedback formativo sobre claridad, corrección y ejemplos.</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};
