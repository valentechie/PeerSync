import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Star } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { fetchSuggestions, sendMatchRequest, type Partner } from '../services/matching';
import { EmptyState, ErrorState, LoadingState, SuccessState } from '../components/UIStates';
import { Avatar, SkillList } from '../components/Swap';
import { ConnectButton } from '../components/ConnectButton';
import { MatchReasons } from '../components/MatchReasons';

const errorMessage = (err: unknown) => (err instanceof Error ? err.message : 'Ocurrió un error inesperado. Inténtalo de nuevo.');

export const FindPartners: React.FC = () => {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [partners, setPartners] = useState<Partner[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [sendingId, setSendingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    fetchSuggestions(token)
      .then(result => {
        if (!cancelled) setPartners(result);
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
  }, [token, attempt]);

  const retry = () => {
    setLoading(true);
    setLoadError('');
    setAttempt(current => current + 1);
  };

  const handleSendRequest = async (partner: Partner) => {
    if (!token) return;
    setSendingId(partner.id);
    setActionError('');
    setSuccessMsg('');
    try {
      await sendMatchRequest(token, partner.id);
      setPartners(prev => prev.map(p => (p.id === partner.id ? { ...p, requestStatus: 'sent' } : p)));
      setSuccessMsg(`Tu solicitud le ha llegado a ${partner.name}.`);
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setSendingId(null);
    }
  };

  const term = searchTerm.trim().toLowerCase();
  const filteredPartners = partners.filter(p =>
    p.name.toLowerCase().includes(term) ||
    p.skillsOffering.some(s => s.toLowerCase().includes(term))
  );
  const hasSkills = Boolean(user?.skillsOffering.length || user?.skillsSeeking.length);

  return (
    <div className="page max-w-7xl space-y-8">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="page-title">Buscar compañeros</h1>
          <p className="page-subtitle">Estudiantes cuyas habilidades complementan las tuyas: cada uno enseña lo que el otro busca.</p>
        </div>
        <div className="relative w-full md:w-80 shrink-0">
          <Search className="w-4 h-4 text-muted absolute left-3.5 top-3.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Buscar por nombre o habilidad..."
            aria-label="Buscar por nombre o habilidad"
            className="field pl-10 bg-surface"
          />
        </div>
      </div>

      {successMsg && (
        <SuccessState title="Solicitud enviada" message={successMsg} onDismiss={() => setSuccessMsg('')} />
      )}
      {actionError && <ErrorState message={actionError} />}

      {loading && <LoadingState message="Buscando compañeros..." />}
      {!loading && loadError && <ErrorState message={loadError} onRetry={retry} />}

      {!loading && !loadError && partners.length === 0 && (
        hasSkills ? (
          <EmptyState
            title="Aún no hay compañeros compatibles"
            description="Cuando alguien ofrezca lo que buscas, o busque lo que ofreces, aparecerá aquí."
            actionLabel="Revisar mis habilidades"
            onAction={() => navigate('/my-profile')}
          />
        ) : (
          <EmptyState
            title="Cuéntanos qué sabes y qué buscas"
            description="Añade tus habilidades para encontrar compañeros que se complementen contigo."
            actionLabel="Añadir habilidades"
            onAction={() => navigate('/my-profile')}
          />
        )
      )}

      {!loading && !loadError && partners.length > 0 && filteredPartners.length === 0 && (
        <EmptyState title="Sin resultados" description="Prueba con otro nombre o habilidad." />
      )}

      {!loading && !loadError && filteredPartners.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPartners.map(partner => (
            <article key={partner.id} className="card p-6 flex flex-col justify-between gap-5">
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <Avatar name={partner.name} tone="learn" />
                  <div className="flex-1 min-w-0">
                    <h2 className="text-xl text-ink break-words">{partner.name}</h2>
                    <p className="text-sm text-muted flex items-center gap-1 mt-0.5">
                      <Star className="w-3.5 h-3.5 fill-sun text-sun" />
                      <span>{partner.reputation === null ? 'Nuevo en Swap4Edu' : `${partner.reputation.toFixed(1)} de reputación`}</span>
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-display text-2xl font-semibold text-teach-strong leading-none">{partner.score}%</p>
                    <p className="text-xs text-muted mt-1">afinidad</p>
                  </div>
                </div>

                {partner.bio && <p className="text-sm text-muted leading-relaxed line-clamp-3">{partner.bio}</p>}

                <div className="space-y-3">
                  {partner.breakdown.theyTeachYou.length > 0 && (
                    <SkillList title="Puede enseñarte" skills={partner.breakdown.theyTeachYou} tone="learn" />
                  )}
                  {partner.breakdown.youTeachThem.length > 0 && (
                    <SkillList title="Puedes enseñarle" skills={partner.breakdown.youTeachThem} tone="teach" />
                  )}
                </div>

                <MatchReasons partner={partner} />
              </div>

              <div className="flex items-center gap-3 pt-4 border-t border-line">
                <button onClick={() => navigate(`/partner/${partner.id}`)} className="btn btn-secondary flex-1">
                  Ver perfil
                </button>
                <ConnectButton
                  status={partner.requestStatus}
                  sending={sendingId === partner.id}
                  onConnect={() => handleSendRequest(partner)}
                  className="flex-1"
                />
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};
