import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle2, Award, ArrowRight, BookOpen } from 'lucide-react';

export const SessionSummary: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8">
      <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-xl space-y-6 text-center">
        <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto shadow-inner">
          <CheckCircle2 className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <span className="px-3 py-1 bg-indigo-50 text-indigo-700 text-xs font-bold rounded-full">
            Sesión Completada (ID: {id || 'session-1'})
          </span>
          <h1 className="text-2xl font-black text-slate-900">¡Resumen de Sesión y Progreso Actualizado!</h1>
          <p className="text-sm text-slate-500 max-w-lg mx-auto">
            Has completado exitosamente tu intercambio de conocimientos. Tu reputación ha incrementado y la sesión ha sido registrada.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left pt-4">
          <div className="p-5 bg-indigo-50/50 border border-indigo-100 rounded-2xl space-y-2">
            <h4 className="text-sm font-bold text-indigo-900 flex items-center space-x-2">
              <BookOpen className="w-4 h-4 text-indigo-600" />
              <span>Temas Cubiertos</span>
            </h4>
            <p className="text-xs text-slate-600">React Avanzado, Custom Hooks, Optimización con useCallback y buenas prácticas.</p>
          </div>

          <div className="p-5 bg-emerald-50/50 border border-emerald-100 rounded-2xl space-y-2">
            <h4 className="text-sm font-bold text-emerald-900 flex items-center space-x-2">
              <Award className="w-4 h-4 text-emerald-600" />
              <span>TeachBack AI Feedback</span>
            </h4>
            <p className="text-xs text-slate-600">Evaluación formativa sobresaliente con excelente claridad en explicaciones.</p>
          </div>
        </div>

        <div className="pt-4 flex flex-wrap justify-center gap-4">
          <button
            onClick={() => navigate('/my-sessions')}
            className="px-6 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-sm rounded-xl transition"
          >
            Volver a Mis Sesiones
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl shadow-md shadow-indigo-200 transition flex items-center space-x-2"
          >
            <span>Ir al Inicio</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
