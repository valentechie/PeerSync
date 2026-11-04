import React from 'react';
import { TrendingUp, Award, BookOpen, Star } from 'lucide-react';

export const MyProgress: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-black text-slate-900">Mi Progreso</h1>
        <p className="text-sm text-slate-500">Métricas de aprendizaje, sesiones impartidas y recibidas, y evolución de habilidades</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-2">
          <div className="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center font-bold">
            <BookOpen className="w-5 h-5" />
          </div>
          <p className="text-xs font-semibold text-slate-400 uppercase">Horas de Intercambio</p>
          <p className="text-2xl font-black text-slate-900">24.5 hrs</p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-2">
          <div className="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center font-bold">
            <TrendingUp className="w-5 h-5" />
          </div>
          <p className="text-xs font-semibold text-slate-400 uppercase">Sesiones Exitosas</p>
          <p className="text-2xl font-black text-slate-900">12</p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-2">
          <div className="w-10 h-10 bg-amber-50 text-amber-600 rounded-xl flex items-center justify-center font-bold">
            <Star className="w-5 h-5" />
          </div>
          <p className="text-xs font-semibold text-slate-400 uppercase">Reputación Media</p>
          <p className="text-2xl font-black text-slate-900">⭐ 4.9</p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-2">
          <div className="w-10 h-10 bg-violet-50 text-violet-600 rounded-xl flex items-center justify-center font-bold">
            <Award className="w-5 h-5" />
          </div>
          <p className="text-xs font-semibold text-slate-400 uppercase">Evaluaciones TeachBack</p>
          <p className="text-2xl font-black text-slate-900">18</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs space-y-6">
        <h3 className="text-lg font-bold text-slate-900">Evolución de Habilidades</h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm font-semibold mb-1">
              <span className="text-slate-700">React & Frontend</span>
              <span className="text-indigo-600">85% Avanzado</span>
            </div>
            <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
              <div className="bg-indigo-600 h-full rounded-full" style={{ width: '85%' }}></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm font-semibold mb-1">
              <span className="text-slate-700">Python & FastAPI</span>
              <span className="text-indigo-600">75% Intermedio</span>
            </div>
            <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
              <div className="bg-indigo-600 h-full rounded-full" style={{ width: '75%' }}></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm font-semibold mb-1">
              <span className="text-slate-700">Machine Learning</span>
              <span className="text-violet-600">40% Iniciando</span>
            </div>
            <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
              <div className="bg-violet-600 h-full rounded-full" style={{ width: '40%' }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
