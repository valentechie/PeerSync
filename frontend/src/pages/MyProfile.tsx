import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Mail, Save } from 'lucide-react';
import { SuccessState } from '../components/UIStates';

export const MyProfile: React.FC = () => {
  const { user, updateProfile } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [success, setSuccess] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile({ name, bio });
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-black text-slate-900">Mi Perfil</h1>
        <p className="text-sm text-slate-500">Administra tu información personal y tus habilidades de intercambio</p>
      </div>

      {success && (
        <SuccessState title="Perfil actualizado" message="Los cambios se han guardado exitosamente." />
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-3xl border border-slate-200 p-8 shadow-xs space-y-6">
        <div className="flex items-center space-x-4 border-b border-slate-100 pb-6">
          <div className="w-20 h-20 bg-gradient-to-tr from-indigo-600 to-violet-600 text-white rounded-2xl flex items-center justify-center text-2xl font-black shadow-lg shadow-indigo-200">
            {name.charAt(0) || 'U'}
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">{name}</h2>
            <p className="text-sm text-slate-500 flex items-center space-x-1 mt-0.5">
              <Mail className="w-4 h-4 text-slate-400" />
              <span>{user?.email}</span>
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Nombre completo</label>
            <div className="relative">
              <User className="w-5 h-5 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Biografía / Descripción</label>
            <textarea
              rows={4}
              value={bio}
              onChange={e => setBio(e.target.value)}
              className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          <div className="p-5 bg-indigo-50/50 border border-indigo-100 rounded-2xl space-y-2">
            <h4 className="text-sm font-bold text-indigo-900">Habilidades que Ofreces</h4>
            <div className="flex flex-wrap gap-2">
              {user?.skillsOffering?.map(s => (
                <span key={s} className="px-3 py-1 bg-white text-indigo-700 text-xs font-semibold rounded-lg border border-indigo-200">
                  {s}
                </span>
              ))}
            </div>
          </div>

          <div className="p-5 bg-violet-50/50 border border-violet-100 rounded-2xl space-y-2">
            <h4 className="text-sm font-bold text-violet-900">Habilidades que Buscas</h4>
            <div className="flex flex-wrap gap-2">
              {user?.skillsSeeking?.map(s => (
                <span key={s} className="px-3 py-1 bg-white text-violet-700 text-xs font-semibold rounded-lg border border-violet-200">
                  {s}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="pt-4 flex justify-end">
          <button
            type="submit"
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-sm shadow-md shadow-indigo-200 transition flex items-center space-x-2"
          >
            <Save className="w-4 h-4" />
            <span>Guardar Cambios</span>
          </button>
        </div>
      </form>
    </div>
  );
};
