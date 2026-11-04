import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Mail, BookOpen, CheckCircle } from 'lucide-react';

export const PartnerProfile: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Demo partner lookup
  const partner = {
    id: id || 'p-1',
    name: 'María González',
    email: 'maria.gonzalez@hack4edu.org',
    bio: 'Estudiante de Ciencia de Datos en la Universidad Tecnológica. Apasionada por el análisis de datos, Python, Pandas y Machine Learning. Buscando dominar React y arquitecturas frontend modernas.',
    skillsOffering: ['Python', 'Machine Learning', 'Pandas', 'SQL', 'Estadística'],
    skillsSeeking: ['React', 'TypeScript', 'Tailwind CSS'],
    reputation: 4.9,
    completedSessions: 16
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center space-x-2 text-sm font-semibold text-slate-600 hover:text-indigo-600 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Volver</span>
      </button>

      <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-100 pb-6">
          <div className="flex items-center space-x-4">
            <div className="w-20 h-20 bg-gradient-to-tr from-indigo-600 to-violet-600 text-white rounded-2xl flex items-center justify-center text-2xl font-black shadow-lg shadow-indigo-200">
              {partner.name.charAt(0)}
            </div>
            <div>
              <h1 className="text-2xl font-black text-slate-900">{partner.name}</h1>
              <p className="text-sm text-slate-500 flex items-center space-x-2 mt-1">
                <Mail className="w-4 h-4 text-slate-400" />
                <span>{partner.email}</span>
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <div className="px-4 py-2 bg-amber-50 border border-amber-200 rounded-xl text-center">
              <span className="block text-xs font-semibold text-amber-600 uppercase">Reputación</span>
              <span className="text-lg font-black text-amber-900">⭐ {partner.reputation}</span>
            </div>
            <div className="px-4 py-2 bg-indigo-50 border border-indigo-200 rounded-xl text-center">
              <span className="block text-xs font-semibold text-indigo-600 uppercase">Sesiones</span>
              <span className="text-lg font-black text-indigo-900 flex items-center justify-center space-x-1">
                <BookOpen className="w-4 h-4 inline mr-1" />
                <span>{partner.completedSessions}</span>
              </span>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Acerca de</h3>
          <p className="text-sm text-slate-600 leading-relaxed">{partner.bio}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
          <div className="p-5 bg-indigo-50/50 border border-indigo-100 rounded-2xl space-y-3">
            <h4 className="text-sm font-bold text-indigo-900 uppercase tracking-wider">Habilidades que enseña</h4>
            <div className="flex flex-wrap gap-2">
              {partner.skillsOffering.map(s => (
                <span key={s} className="px-3 py-1 bg-white text-indigo-700 text-xs font-semibold rounded-lg shadow-xs border border-indigo-200">
                  {s}
                </span>
              ))}
            </div>
          </div>

          <div className="p-5 bg-violet-50/50 border border-violet-100 rounded-2xl space-y-3">
            <h4 className="text-sm font-bold text-violet-900 uppercase tracking-wider">Habilidades que busca</h4>
            <div className="flex flex-wrap gap-2">
              {partner.skillsSeeking.map(s => (
                <span key={s} className="px-3 py-1 bg-white text-violet-700 text-xs font-semibold rounded-lg shadow-xs border border-violet-200">
                  {s}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="pt-4 flex justify-end">
          <button
            onClick={() => alert(`Solicitud enviada a ${partner.name}`)}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-sm shadow-md shadow-indigo-200 transition flex items-center space-x-2"
          >
            <CheckCircle className="w-4 h-4" />
            <span>Enviar solicitud de intercambio</span>
          </button>
        </div>
      </div>
    </div>
  );
};
