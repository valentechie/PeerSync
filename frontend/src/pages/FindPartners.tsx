import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Star, ArrowRight, CheckCircle, Sparkles } from 'lucide-react';
import { SuccessState } from '../components/UIStates';

interface Partner {
  id: string;
  name: string;
  bio: string;
  skillsOffering: string[];
  skillsSeeking: string[];
  matchScore: number;
  reputation: number;
}

const MOCK_PARTNERS: Partner[] = [
  {
    id: 'p-1',
    name: 'María González',
    bio: 'Estudiante de Ciencia de Datos. Experta en Python, Pandas y Machine Learning. Buscando dominar React.',
    skillsOffering: ['Python', 'Machine Learning', 'SQL'],
    skillsSeeking: ['React', 'TypeScript'],
    matchScore: 98,
    reputation: 4.9
  },
  {
    id: 'p-2',
    name: 'Carlos Ruiz',
    bio: 'Desarrollador Backend con Python y FastAPI. Buscando aprender arquitectura frontend moderna.',
    skillsOffering: ['FastAPI', 'PostgreSQL', 'Docker'],
    skillsSeeking: ['React', 'Tailwind CSS'],
    matchScore: 92,
    reputation: 4.8
  },
  {
    id: 'p-3',
    name: 'Lucía Fernández',
    bio: 'Diseñadora UX y Frontend developer. Apasionada por interfaces accesibles y limpias.',
    skillsOffering: ['UI/UX', 'Tailwind CSS', 'JavaScript'],
    skillsSeeking: ['Python', 'Algoritmos'],
    matchScore: 85,
    reputation: 5.0
  }
];

export const FindPartners: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sentRequests, setSentRequests] = useState<Record<string, boolean>>({});
  const [successMsg, setSuccessMsg] = useState('');
  const navigate = useNavigate();

  const filteredPartners = MOCK_PARTNERS.filter(p => 
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.skillsOffering.some(s => s.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleSendRequest = (id: string, name: string) => {
    setSentRequests(prev => ({ ...prev, [id]: true }));
    setSuccessMsg(`¡Solicitud enviada exitosamente a ${name}! Te notificaremos cuando acepte.`);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
            <Sparkles className="w-6 h-6 text-indigo-600" />
            <span>Buscar Compañeros (Swap4Edu AI)</span>
          </h1>
          <p className="text-sm text-slate-500 font-medium">Matching determinista basado en complementariedad de habilidades</p>
        </div>
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-4 top-3.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Buscar por nombre o habilidad..."
            className="w-full pl-11 pr-4 py-2.5 bg-white border border-slate-200 rounded-2xl text-sm shadow-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
          />
        </div>
      </div>

      {successMsg && (
        <SuccessState title="Solicitud enviada" message={successMsg} onDismiss={() => setSuccessMsg('')} />
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredPartners.map(partner => (
          <div key={partner.id} className="bg-white rounded-3xl border border-slate-200/80 p-7 shadow-xs hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-black text-slate-900">{partner.name}</h3>
                  <p className="text-xs text-amber-600 font-bold flex items-center space-x-1 mt-0.5">
                    <Star className="w-3.5 h-3.5 fill-current" />
                    <span>{partner.reputation} Reputación</span>
                  </p>
                </div>
                <span className="px-3.5 py-1.5 bg-gradient-to-r from-emerald-500 to-teal-600 text-white text-xs font-black rounded-full shadow-md shadow-emerald-500/20">
                  {partner.matchScore}% Match
                </span>
              </div>

              <p className="text-sm text-slate-600 leading-relaxed line-clamp-2 font-medium">{partner.bio}</p>

              <div className="space-y-3 pt-2">
                <div>
                  <span className="text-[10px] uppercase tracking-wider font-extrabold text-indigo-600">Ofrece enseñar:</span>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {partner.skillsOffering.map(skill => (
                      <span key={skill} className="px-3 py-1 bg-indigo-50/80 text-indigo-700 text-xs font-bold rounded-xl border border-indigo-100">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <span className="text-[10px] uppercase tracking-wider font-extrabold text-violet-600">Busca aprender:</span>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {partner.skillsSeeking.map(skill => (
                      <span key={skill} className="px-3 py-1 bg-violet-50/80 text-violet-700 text-xs font-bold rounded-xl border border-violet-100">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3 pt-4 border-t border-slate-100">
              <button
                onClick={() => navigate(`/partner/${partner.id}`)}
                className="flex-1 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-colors"
              >
                Ver Perfil
              </button>
              <button
                onClick={() => handleSendRequest(partner.id, partner.name)}
                disabled={sentRequests[partner.id]}
                className={`flex-1 py-3 font-bold text-xs rounded-xl transition-all duration-200 flex items-center justify-center space-x-1.5 shadow-sm ${
                  sentRequests[partner.id]
                    ? 'bg-emerald-100 text-emerald-800 cursor-not-allowed shadow-none'
                    : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-200 hover:scale-105'
                }`}
              >
                {sentRequests[partner.id] ? (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    <span>Enviado</span>
                  </>
                ) : (
                  <>
                    <span>Conectar</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
