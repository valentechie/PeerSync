import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, BookOpen, Star } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { fetchPartner, sendMatchRequest, type Partner } from '../services/matching';
import { ErrorState, LoadingState, SuccessState } from '../components/UIStates';
import { Avatar, SkillList } from '../components/Swap';
import { ConnectButton } from '../components/ConnectButton';
import { MatchReasons } from '../components/MatchReasons';

const errorMessage = (err: unknown) => (err instanceof Error ? err.message : 'Ocurrió un error inesperado. Inténtalo de nuevo.');

export const PartnerProfile: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [partner, setPartner] = useState<Partner | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [sending, setSending] = useState(false);
  const [actionError, setActionError] = useState('');
  const [sent, setSent] = useState(false);

  useEffect(() => {
    if (!token || !id) return;
    let cancelled = false;
    fetchPartner(token, id)
      .then(result => {
        if (!cancelled) setPartner(result);
      })
      .catch((err: unknown) => {
        if (!cancelled) setLoadError(errorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token, id, attempt]);

  const retry = () => {
    setLoading(true);
    setLoadError('');
    setAttempt(current => current + 1);
  };

  const handleSendRequest = async () => {
    if (!token || !partner) return;
    setSending(true);
    setActionError('');
    try {
      await sendMatchRequest(token, partner.id);
      setPartner({ ...partner, requestStatus: 'sent' });
      setSent(true);
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="page max-w-4xl space-y-6">
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-2 text-sm font-bold text-muted hover:text-teach-strong transition-colors cursor-pointer"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Volver</span>
      </button>

      {loading && <LoadingState message="Cargando perfil..." />}
      {!loading && loadError && <ErrorState message={loadError} onRetry={retry} />}

      {sent && partner && (
        <SuccessState title="Solicitud enviada" message={`Tu solicitud le ha llegado a ${partner.name}.`} onDismiss={() => setSent(false)} />
      )}
      {actionError && <ErrorState message={actionError} />}

      {!loading && !loadError && partner && (
        <div className="card p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5 border-b border-line pb-6">
            <div className="flex items-center gap-4 min-w-0 w-full sm:w-auto">
              <Avatar name={partner.name} tone="learn" className="w-20 h-20 text-3xl" />
              <h1 className="page-title min-w-0 break-words">{partner.name}</h1>
            </div>
            <dl className="flex items-center gap-6 shrink-0">
              <div>
                <dt className="text-xs text-muted">Afinidad</dt>
                <dd className="font-display text-2xl font-semibold text-teach-strong">{partner.score}%</dd>
              </div>
              <div>
                <dt className="text-xs text-muted">Reputación</dt>
                <dd className="font-display text-2xl font-semibold flex items-center gap-1.5">
                  <Star className="w-4 h-4 fill-sun text-sun" />
                  <span>{partner.reputation?.toFixed(1) ?? 'Nuevo'}</span>
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted">Sesiones</dt>
                <dd className="font-display text-2xl font-semibold flex items-center gap-1.5">
                  <BookOpen className="w-4 h-4 text-teach" />
                  <span>{partner.completedSessions}</span>
                </dd>
              </div>
            </dl>
          </div>

          {partner.bio && (
            <div className="space-y-2">
              <h2 className="text-xl text-ink">Acerca de</h2>
              <p className="text-muted leading-relaxed whitespace-pre-line">{partner.bio}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-5 bg-learn-soft/50 rounded-2xl">
              <SkillList title="Habilidades que enseña" skills={partner.skillsOffering} tone="learn" />
            </div>
            <div className="p-5 bg-teach-soft/50 rounded-2xl">
              <SkillList title="Habilidades que busca" skills={partner.skillsSeeking} tone="teach" />
            </div>
          </div>

          <MatchReasons partner={partner} />

          <div className="flex justify-end">
            <ConnectButton status={partner.requestStatus} sending={sending} onConnect={handleSendRequest} />
          </div>
        </div>
      )}
    </div>
  );
};
