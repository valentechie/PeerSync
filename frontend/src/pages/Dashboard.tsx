import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Sparkles, Users, BookOpen, TrendingUp, ArrowRight, Star, Clock, Zap } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-indigo-600 via-violet-600 to-fuchsia-600 rounded-3xl p-8 sm:p-10 text-white shadow-2xl shadow-indigo-500/20 relative overflow-hidden">
        <div className="absolute right-0 bottom-0 opacity-15 transform translate-x-12 translate-y-12">
          <Sparkles className="w-96 h-96" />
        </div>
        <div className="relative z-10 max-w-2xl space-y-5">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 bg-white/15 backdrop-blur-md rounded-full text-xs font-semibold text-white border border-white/20 shadow-xs">
            <Zap className="w-3.5 h-3.5 text-amber-300 animate-bounce" />
            <span>Hack4Edu 2026 · Swap4Edu AI Engine</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            ¡Hola, {user?.name || 'Estudiante'}! 👋
          </h1>
          <p className="text-indigo-100 text-base sm:text-lg font-medium leading-relaxed">
            Conecta con compañeros complementarios, potencia tu aprendizaje con StudyMind AI y evalúa tus conocimientos con TeachBack AI.
          </p>
          <div className="pt-2 flex flex-wrap gap-4">
            <button
              onClick={() => navigate('/find-partners')}
              className="px-7 py-3.5 bg-white text-indigo-700 font-bold rounded-2xl text-sm shadow-xl hover:bg-indigo-50 hover:scale-105 transition-all duration-200 flex items-center space-x-2.5"
            >
              <span>Buscar compañeros</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate('/my-sessions')}
              className="px-7 py-3.5 bg-white/10 hover:bg-white/20 text-white font-bold rounded-2xl text-sm border border-white/25 backdrop-blur-md transition-all duration-200 hover:scale-105"
            >
              Ver mis sesiones
            </button>
          </div>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex items-center space-x-4 group">
          <div className="w-14 h-14 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center font-bold group-hover:bg-indigo-600 group-hover:text-white transition-colors shadow-sm">
            <BookOpen className="w-7 h-7" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Sesiones Completadas</p>
            <p className="text-2xl font-black text-slate-900 mt-0.5">{user?.completedSessions || 12}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex items-center space-x-4 group">
          <div className="w-14 h-14 bg-amber-50 text-amber-600 rounded-2xl flex items-center justify-center font-bold group-hover:bg-amber-500 group-hover:text-white transition-colors shadow-sm">
            <Star className="w-7 h-7" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Reputación</p>
            <p className="text-2xl font-black text-slate-900 mt-0.5">⭐ {user?.reputation || 4.9}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex items-center space-x-4 group">
          <div className="w-14 h-14 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center font-bold group-hover:bg-emerald-600 group-hover:text-white transition-colors shadow-sm">
            <Users className="w-7 h-7" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Ofreces</p>
            <p className="text-sm font-black text-slate-900 truncate max-w-[150px] mt-0.5">
              {user?.skillsOffering?.join(', ') || 'React, Python'}
            </p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex items-center space-x-4 group">
          <div className="w-14 h-14 bg-violet-50 text-violet-600 rounded-2xl flex items-center justify-center font-bold group-hover:bg-violet-600 group-hover:text-white transition-colors shadow-sm">
            <TrendingUp className="w-7 h-7" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Buscas</p>
            <p className="text-sm font-black text-slate-900 truncate max-w-[150px] mt-0.5">
              {user?.skillsSeeking?.join(', ') || 'ML, PostgreSQL'}
            </p>
          </div>
        </div>
      </div>

      {/* Recent Activity / Next Recommended Action */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200/80 p-8 shadow-xs space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-black text-slate-900">Sesión Programada Reciente</h2>
            <button onClick={() => navigate('/my-sessions')} className="text-xs font-bold text-indigo-600 hover:text-indigo-700 bg-indigo-50 px-3 py-1.5 rounded-xl transition">
              Ver todas
            </button>
          </div>

          <div className="p-6 bg-gradient-to-r from-indigo-50/70 via-violet-50/50 to-indigo-50/70 border border-indigo-100 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 shadow-inner">
            <div className="space-y-2">
              <span className="px-3 py-1 bg-indigo-600 text-white text-[11px] font-black rounded-lg shadow-sm">
                Próxima sesión
              </span>
              <h3 className="text-lg font-black text-slate-900">Intercambio: React Avanzado ⇄ Machine Learning</h3>
              <p className="text-sm text-slate-600 flex items-center space-x-2 font-medium">
                <Clock className="w-4 h-4 text-indigo-500" />
                <span>Hoy a las 18:00 hrs con María González</span>
              </p>
            </div>
            <button
              onClick={() => navigate('/study-room/session-1')}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-xl shadow-lg shadow-indigo-200 hover:scale-105 transition-all duration-200 shrink-0"
            >
              Entrar a la Sala
            </button>
          </div>
        </div>

        {/* AI Assistants Teaser */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-8 shadow-xs space-y-6">
          <h2 className="text-lg font-black text-slate-900 flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-indigo-600" />
            <span>Asistentes IA 360</span>
          </h2>
          <div className="space-y-4">
            <div className="p-4 bg-gradient-to-br from-violet-50 to-indigo-50/50 border border-violet-100 rounded-2xl space-y-1.5 shadow-xs">
              <h4 className="text-sm font-black text-violet-900 flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-violet-600" />
                <span>StudyMind AI</span>
              </h4>
              <p className="text-xs text-violet-700 font-medium leading-relaxed">Pistas progresivas bajo demanda sin revelar la solución completa.</p>
            </div>
            <div className="p-4 bg-gradient-to-br from-emerald-50 to-teal-50/50 border border-emerald-100 rounded-2xl space-y-1.5 shadow-xs">
              <h4 className="text-sm font-black text-emerald-900 flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-emerald-600" />
                <span>TeachBack AI</span>
              </h4>
              <p className="text-xs text-emerald-700 font-medium leading-relaxed">Feedback formativo sobre claridad, corrección y ejemplos.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
