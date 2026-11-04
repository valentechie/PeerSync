import React, { useState } from 'react';
import { Mail, Save, User as UserIcon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ErrorState, SuccessState } from '../components/UIStates';
import { Avatar } from '../components/Swap';

export const MyProfile: React.FC = () => {
  const { user, updateProfile } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setSaving(true);
    try {
      await updateProfile({ name, bio });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudieron guardar los cambios.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page max-w-3xl space-y-8">
      <div>
        <h1 className="page-title">Mi perfil</h1>
        <p className="page-subtitle">Cuéntale a la gente de tus salas quién eres y qué estás aprendiendo.</p>
      </div>

      {success && <SuccessState title="Perfil actualizado" message="Los cambios se han guardado exitosamente." />}
      {error && <ErrorState message={error} />}

      <form onSubmit={handleSubmit} className="card p-6 sm:p-8 space-y-6">
        <div className="flex items-center gap-4 border-b border-line pb-6 min-w-0">
          <Avatar name={name || user?.name || 'U'} className="w-20 h-20 text-3xl" />
          <div className="min-w-0">
            <p className="font-display text-2xl font-bold break-words">{user?.name}</p>
            <p className="text-sm text-muted flex items-center gap-1.5 min-w-0">
              <Mail className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span className="truncate">{user?.email}</span>
            </p>
          </div>
        </div>

        <div>
          <label htmlFor="name" className="label">Nombre</label>
          <div className="relative">
            <UserIcon className="w-4 h-4 text-muted absolute left-3.5 top-3.5" />
            <input
              id="name"
              required
              maxLength={100}
              value={name}
              onChange={e => setName(e.target.value)}
              className="field pl-10"
            />
          </div>
        </div>

        <div>
          <label htmlFor="bio" className="label">Sobre ti</label>
          <textarea
            id="bio"
            rows={4}
            maxLength={1000}
            value={bio}
            onChange={e => setBio(e.target.value)}
            placeholder="Ej.: Estoy preparando Cálculo y me viene bien estudiar con gente."
            className="field"
          />
        </div>

        <div className="flex justify-end">
          <button type="submit" disabled={saving} className="btn btn-primary">
            <Save className="w-4 h-4" />
            <span>{saving ? 'Guardando...' : 'Guardar cambios'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
