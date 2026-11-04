import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Mail, Save, Plus, X } from 'lucide-react';
import { ErrorState, SuccessState } from '../components/UIStates';
import { Avatar } from '../components/Swap';

const MAX_SKILLS = 20;

const SkillEditor: React.FC<{
  id: string;
  title: string;
  placeholder: string;
  tone: 'teach' | 'learn';
  skills: string[];
  onChange: (skills: string[]) => void;
}> = ({ id, title, placeholder, tone, skills, onChange }) => {
  const [draft, setDraft] = useState('');
  const isFull = skills.length >= MAX_SKILLS;

  const addDraft = () => {
    const skill = draft.trim();
    if (!skill || isFull) return;
    if (!skills.some(existing => existing.toLowerCase() === skill.toLowerCase())) {
      onChange([...skills, skill]);
    }
    setDraft('');
  };

  return (
    <div className={`p-5 rounded-2xl space-y-3 ${tone === 'teach' ? 'bg-teach-soft/50' : 'bg-learn-soft/50'}`}>
      <label htmlFor={id} className={`eyebrow block ${tone === 'teach' ? 'text-teach' : 'text-learn'}`}>{title}</label>
      <div className="flex flex-wrap gap-1.5">
        {skills.length === 0 && <span className="text-sm text-muted">Aún no hay ninguna.</span>}
        {skills.map(skill => (
          <span key={skill} className={`chip chip-${tone} inline-flex items-center gap-1`}>
            {skill}
            <button
              type="button"
              onClick={() => onChange(skills.filter(s => s !== skill))}
              aria-label={`Quitar ${skill}`}
              className="cursor-pointer rounded hover:opacity-60"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <input
          id={id}
          type="text"
          value={draft}
          maxLength={100}
          disabled={isFull}
          onChange={e => setDraft(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') {
              e.preventDefault();
              addDraft();
            }
          }}
          placeholder={isFull ? `Máximo ${MAX_SKILLS} habilidades` : placeholder}
          className="field bg-surface flex-1 min-w-0"
        />
        <button type="button" onClick={addDraft} disabled={isFull} aria-label={`Añadir a ${title}`} className="btn btn-secondary px-3! shrink-0">
          <Plus className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export const MyProfile: React.FC = () => {
  const { user, updateProfile } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [skillsOffering, setSkillsOffering] = useState(user?.skillsOffering ?? []);
  const [skillsSeeking, setSkillsSeeking] = useState(user?.skillsSeeking ?? []);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setSaving(true);
    try {
      await updateProfile({ name, bio, skillsOffering, skillsSeeking });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudieron guardar los cambios.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page max-w-4xl space-y-8">
      <div>
        <h1 className="page-title">Mi perfil</h1>
        <p className="page-subtitle">Cuéntale a tus compañeros quién eres, qué puedes enseñar y qué quieres aprender.</p>
      </div>

      {success && (
        <SuccessState title="Perfil actualizado" message="Los cambios se han guardado exitosamente." />
      )}
      {error && <ErrorState message={error} />}

      <form onSubmit={handleSubmit} className="card p-6 sm:p-8 space-y-6">
        <div className="flex items-center gap-4 border-b border-line pb-6 min-w-0">
          <Avatar name={name} className="w-20 h-20 text-3xl" />
          <div className="min-w-0">
            <h2 className="text-2xl text-ink truncate">{name}</h2>
            <p className="text-sm text-muted flex items-center gap-1.5 mt-0.5 min-w-0">
              <Mail className="w-4 h-4 shrink-0" />
              <span className="truncate">{user?.email}</span>
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label htmlFor="name" className="label">Nombre completo</label>
            <div className="relative">
              <User className="w-4 h-4 text-muted absolute left-3.5 top-3.5" />
              <input
                id="name"
                type="text"
                required
                maxLength={100}
                value={name}
                onChange={e => setName(e.target.value)}
                className="field pl-10"
              />
            </div>
          </div>

          <div>
            <label htmlFor="bio" className="label">Biografía / Descripción</label>
            <textarea
              id="bio"
              rows={4}
              maxLength={1000}
              value={bio}
              onChange={e => setBio(e.target.value)}
              className="field"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SkillEditor
            id="skills-offering"
            title="Habilidades que ofreces"
            placeholder="Ej.: Python"
            tone="teach"
            skills={skillsOffering}
            onChange={setSkillsOffering}
          />
          <SkillEditor
            id="skills-seeking"
            title="Habilidades que buscas"
            placeholder="Ej.: Estadística"
            tone="learn"
            skills={skillsSeeking}
            onChange={setSkillsSeeking}
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
