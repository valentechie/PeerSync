import React, { useEffect, useRef, useState } from 'react';
import { Camera, GraduationCap, Mail, Save, Trash2, User as UserIcon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { fetchStudies, removeMyPhoto, uploadMyPhoto, type StudyFamily } from '../services/people';
import { preparePhoto } from '../services/photo';
import { ErrorState, SuccessState } from '../components/UIStates';
import { Avatar } from '../components/Swap';
import { FeedbackSection } from '../components/FeedbackSection';

export const MyProfile: React.FC = () => {
  const { token, user, updateProfile, applyProfile } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [studyCode, setStudyCode] = useState(user?.studyCode ?? '');
  const [families, setFamilies] = useState<StudyFamily[] | null>(null);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [photoBusy, setPhotoBusy] = useState(false);
  const photoInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!token) return;
    fetchStudies(token)
      .then(setFamilies)
      .catch((err: unknown) => setError(errorMessage(err)));
  }, [token]);

  const handlePhoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!token || !file) return;
    setPhotoBusy(true);
    setError('');
    try {
      applyProfile(await uploadMyPhoto(token, await preparePhoto(file)));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPhotoBusy(false);
    }
  };

  const handleRemovePhoto = async () => {
    if (!token) return;
    setPhotoBusy(true);
    setError('');
    try {
      applyProfile(await removeMyPhoto(token));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPhotoBusy(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setSaving(true);
    try {
      // Sin catálogo cargado no se envía el estudio, para no borrar el que ya tiene.
      await updateProfile(families ? { name, bio, studyCode: studyCode || null } : { name, bio });
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
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 border-b border-line pb-6 min-w-0">
          <Avatar name={name || user?.name || 'U'} photoUrl={user?.photoUrl} className="w-24 h-24 text-4xl" />
          <div className="min-w-0 space-y-2">
            <p className="font-display text-2xl font-bold break-words">{user?.name}</p>
            <p className="text-sm text-muted flex items-center gap-1.5 min-w-0">
              <Mail className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span className="truncate">{user?.email}</span>
            </p>
            <input ref={photoInput} type="file" accept="image/*" onChange={handlePhoto} className="hidden" aria-label="Elegir foto de perfil" />
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={() => photoInput.current?.click()} disabled={photoBusy} className="btn btn-secondary py-2!">
                <Camera className="w-4 h-4" aria-hidden="true" />
                <span>{photoBusy ? 'Guardando...' : user?.photoUrl ? 'Cambiar foto' : 'Poner foto'}</span>
              </button>
              {user?.photoUrl && (
                <button type="button" onClick={handleRemovePhoto} disabled={photoBusy} className="btn btn-secondary py-2!">
                  <Trash2 className="w-4 h-4" aria-hidden="true" />
                  <span>Quitar</span>
                </button>
              )}
            </div>
            <p className="text-xs text-muted">Se recorta en cuadrado y se ve en toda la app.</p>
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
          <label htmlFor="study" className="label">¿Qué estudias?</label>
          <div className="relative">
            <GraduationCap className="w-4 h-4 text-muted absolute left-3.5 top-3.5 pointer-events-none" aria-hidden="true" />
            <select
              id="study"
              value={studyCode}
              onChange={e => setStudyCode(e.target.value)}
              disabled={!families}
              aria-describedby="study-help"
              className="field pl-10 cursor-pointer"
            >
              <option value="">{families ? 'Elige tus estudios' : 'Cargando estudios...'}</option>
              {families?.map(family => (
                <optgroup key={family.name} label={family.name}>
                  {family.studies.map(study => (
                    <option key={study.code} value={study.code}>{study.label}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
          <p id="study-help" className="text-xs text-muted mt-1.5">
            Te relacionamos con quien estudia lo mismo o algo parecido. Si no aparece el tuyo, elige "Otros estudios" de tu área.
          </p>
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

      <FeedbackSection />
    </div>
  );
};
