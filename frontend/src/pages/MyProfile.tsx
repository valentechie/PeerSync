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
      setError(err instanceof Error ? err.message : "Couldn't save the changes.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page max-w-3xl space-y-8">
      <div>
        <h1 className="page-title">My profile</h1>
        <p className="page-subtitle">Tell the people in your rooms who you are and what you're learning.</p>
      </div>

      {success && <SuccessState title="Profile updated" message="Your changes have been saved." />}
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
            <input ref={photoInput} type="file" accept="image/*" onChange={handlePhoto} className="hidden" aria-label="Choose profile photo" />
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={() => photoInput.current?.click()} disabled={photoBusy} className="btn btn-secondary py-2!">
                <Camera className="w-4 h-4" aria-hidden="true" />
                <span>{photoBusy ? 'Saving...' : user?.photoUrl ? 'Change photo' : 'Add photo'}</span>
              </button>
              {user?.photoUrl && (
                <button type="button" onClick={handleRemovePhoto} disabled={photoBusy} className="btn btn-secondary py-2!">
                  <Trash2 className="w-4 h-4" aria-hidden="true" />
                  <span>Remove</span>
                </button>
              )}
            </div>
            <p className="text-xs text-muted">It's cropped to a square and shown across the app.</p>
          </div>
        </div>

        <div>
          <label htmlFor="name" className="label">Name</label>
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
          <label htmlFor="study" className="label">What do you study?</label>
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
              <option value="">{families ? 'Choose your studies' : 'Loading studies...'}</option>
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
            We connect you with people studying the same or something similar. If yours isn't listed, choose "Other" for your area.
          </p>
        </div>

        <div>
          <label htmlFor="bio" className="label">About you</label>
          <textarea
            id="bio"
            rows={4}
            maxLength={1000}
            value={bio}
            onChange={e => setBio(e.target.value)}
            placeholder="E.g.: I'm preparing for Calculus and it helps me to study with others."
            className="field"
          />
        </div>

        <div className="flex justify-end">
          <button type="submit" disabled={saving} className="btn btn-primary">
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving...' : 'Save changes'}</span>
          </button>
        </div>
      </form>

      <FeedbackSection />
    </div>
  );
};
