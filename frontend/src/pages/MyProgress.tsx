import React from 'react';
import { TrendingUp, Award, BookOpen, Star } from 'lucide-react';

const STATS = [
  { label: 'Horas de intercambio', value: '24.5 hrs', icon: BookOpen, color: 'text-teach' },
  { label: 'Sesiones exitosas', value: '12', icon: TrendingUp, color: 'text-teach' },
  { label: 'Reputación media', value: '4.9', icon: Star, color: 'text-sun fill-sun' },
  { label: 'Evaluaciones TeachBack', value: '18', icon: Award, color: 'text-guide' },
];

const SKILLS = [
  { name: 'React & Frontend', level: 85, stage: 'Avanzado', bar: 'bg-teach', text: 'text-teach-strong' },
  { name: 'Python & FastAPI', level: 75, stage: 'Intermedio', bar: 'bg-teach', text: 'text-teach-strong' },
  { name: 'Machine Learning', level: 40, stage: 'Iniciando', bar: 'bg-learn', text: 'text-learn-strong' },
];

export const MyProgress: React.FC = () => {
  return (
    <div className="page max-w-5xl space-y-8">
      <div>
        <h1 className="page-title flex items-center gap-3">
          <span>Mi progreso</span>
          <span className="chip chip-demo font-sans">Demo</span>
        </h1>
        <p className="page-subtitle">Lo que has enseñado, lo que has aprendido y cómo evolucionan tus habilidades.</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {STATS.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card p-5 sm:p-6 space-y-2">
            <Icon className={`w-5 h-5 ${color}`} />
            <p className="font-display text-3xl font-semibold">{value}</p>
            <p className="text-sm text-muted">{label}</p>
          </div>
        ))}
      </div>

      <section className="card p-6 sm:p-8 space-y-6">
        <h2 className="text-2xl text-ink">Evolución de habilidades</h2>
        <div className="space-y-5">
          {SKILLS.map(skill => (
            <div key={skill.name}>
              <div className="flex justify-between gap-4 text-sm font-bold mb-1.5">
                <span>{skill.name}</span>
                <span className={skill.text}>{skill.level}% {skill.stage}</span>
              </div>
              <div
                className="w-full bg-line/60 h-2.5 rounded-full overflow-hidden"
                role="progressbar"
                aria-label={skill.name}
                aria-valuenow={skill.level}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                <div className={`${skill.bar} h-full rounded-full`} style={{ width: `${skill.level}%` }} />
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
