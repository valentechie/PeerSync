import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Check, Flag, Link2, LogOut, Paperclip, Send, UserPlus, Users } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ApiError, errorMessage } from '../services/api';
import { fetchFriends, type FriendStatus } from '../services/people';
import { fetchInviteLink, fetchMessages, fetchRoom, joinRoom, leaveRoom, sendMessage, uploadAttachment, type RoomDetail, type RoomMessage } from '../services/rooms';
import { ErrorState, LoadingState } from '../components/UIStates';
import { Avatar } from '../components/Swap';
import { FriendButton } from '../components/FriendButton';
import { AttachmentView } from '../components/AttachmentView';
import { InviteDialog } from '../components/InviteDialog';
import { ContrastaPanel } from '../components/ContrastaPanel';
import { StudyMindPanel } from '../components/StudyMindPanel';
import { TeachBackPanel } from '../components/TeachBackPanel';
import { findYouTubeId, YouTubeEmbed } from '../components/YouTubeEmbed';

const POLL_INTERVAL_MS = 3000;
const MAX_FILE_BYTES = 4 * 1024 * 1024;
const ACCEPTED_FILES = 'image/png,image/jpeg,image/gif,image/webp,audio/mpeg,audio/ogg,audio/wav,audio/mp4,audio/x-m4a,video/mp4,video/webm,application/pdf';

const formatTime = (iso: string) => new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

export const Room: React.FC = () => {
  const { id = '' } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const [searchParams] = useSearchParams();
  const inviteToken = useRef(searchParams.get('invite'));
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [room, setRoom] = useState<RoomDetail | null>(null);
  const [messages, setMessages] = useState<RoomMessage[]>([]);
  const [loadError, setLoadError] = useState('');
  const [canRetryLoad, setCanRetryLoad] = useState(true);
  const [connectionLost, setConnectionLost] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [sendError, setSendError] = useState('');
  const [copied, setCopied] = useState(false);
  const [inviting, setInviting] = useState(false);
  const closeInvite = useCallback(() => setInviting(false), []);
  const [confirmingLeave, setConfirmingLeave] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const [friendStatuses, setFriendStatuses] = useState<Record<string, FriendStatus>>({});
  const chatRef = useRef<HTMLDivElement>(null);
  const followChat = useRef(true);
  const fileInput = useRef<HTMLInputElement>(null);

  // Al abrir la sala se entra en ella; después se consulta cada pocos segundos.
  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    let timer: ReturnType<typeof setInterval> | undefined;

    const refresh = async () => {
      try {
        const [latestRoom, latestMessages] = await Promise.all([fetchRoom(token, id), fetchMessages(token, id)]);
        if (cancelled) return;
        setRoom(latestRoom);
        setMessages(latestMessages);
        setConnectionLost(false);
      } catch {
        if (!cancelled) setConnectionLost(true);
      }
    };

    joinRoom(token, id, inviteToken.current)
      .then(joined => {
        if (cancelled) return;
        setRoom(joined);
        // Ya dentro, el enlace sobra: se quita de la barra para no compartirlo sin querer.
        if (inviteToken.current) navigate(`/rooms/${id}`, { replace: true });
        void refresh();
        timer = setInterval(refresh, POLL_INTERVAL_MS);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setLoadError(errorMessage(err));
        // Sin invitación, reintentar no cambia nada.
        setCanRetryLoad(!(err instanceof ApiError && [403, 404, 409].includes(err.status)));
      });

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [token, id, attempt, navigate]);

  // Si esto falla, la sala sigue funcionando: solo no se sabrá quién es amigo.
  useEffect(() => {
    if (!token) return;
    fetchFriends(token)
      .then(({ friends, received, sent }) => {
        setFriendStatuses(Object.fromEntries([...friends, ...received, ...sent].map(person => [person.id, person.friendStatus])));
      })
      .catch(() => undefined);
  }, [token]);

  const roomId = room?.id;
  const roomIsClosed = room?.isClosed;
  useEffect(() => {
    if (!token || !roomId || roomIsClosed) return;
    fetchInviteLink(token, roomId)
      .then(link => setInviteUrl(`${window.location.origin}/rooms/${roomId}?invite=${encodeURIComponent(link.token)}`))
      .catch(() => undefined);
  }, [token, roomId, roomIsClosed]);

  useEffect(() => {
    const chat = chatRef.current;
    if (chat && followChat.current) chat.scrollTop = chat.scrollHeight;
  }, [messages]);

  const handleScroll = () => {
    const chat = chatRef.current;
    if (chat) followChat.current = chat.scrollHeight - chat.scrollTop - chat.clientHeight < 80;
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !draft.trim()) return;
    setSending(true);
    setSendError('');
    try {
      const message = await sendMessage(token, id, draft);
      followChat.current = true;
      setMessages(current => (current.some(m => m.id === message.id) ? current : [...current, message]));
      setDraft('');
    } catch (err) {
      setSendError(errorMessage(err));
    } finally {
      setSending(false);
    }
  };

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!token || !file) return;
    if (file.size > MAX_FILE_BYTES) {
      setSendError('El archivo no puede superar los 4 MB. Para vídeos largos, pega un enlace de YouTube.');
      return;
    }
    setUploading(true);
    setSendError('');
    try {
      const message = await uploadAttachment(token, id, file);
      followChat.current = true;
      setMessages(current => (current.some(m => m.id === message.id) ? current : [...current, message]));
    } catch (err) {
      setSendError(errorMessage(err));
    } finally {
      setUploading(false);
    }
  };

  // Al navegar, la ventana obligatoria de feedback detecta lo que quedó pendiente.
  const handleLeave = async () => {
    if (!token) return;
    setLeaving(true);
    try {
      await leaveRoom(token, id);
      navigate('/rooms');
    } catch (err) {
      setSendError(errorMessage(err));
      setLeaving(false);
      setConfirmingLeave(false);
    }
  };

  const handleCopyLink = async () => {
    if (!inviteUrl) {
      setSendError('El enlace aún no está listo. Inténtalo de nuevo en un momento.');
      return;
    }
    try {
      await navigator.clipboard.writeText(inviteUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setSendError('No se pudo copiar el enlace. Prueba a invitar a la persona desde "Invitar personas".');
    }
  };

  const backButton = (
    <button
      onClick={() => navigate('/rooms')}
      className="inline-flex items-center gap-2 text-sm font-bold text-muted hover:text-ink transition-colors cursor-pointer"
    >
      <ArrowLeft className="w-4 h-4" />
      <span>Salas</span>
    </button>
  );

  if (loadError) {
    return (
      <div className="page max-w-3xl space-y-4">
        {backButton}
        <ErrorState
          message={loadError}
          onRetry={
            canRetryLoad
              ? () => {
                  setLoadError('');
                  setAttempt(current => current + 1);
                }
              : undefined
          }
        />
      </div>
    );
  }

  if (!room) return <LoadingState message="Entrando en la sala..." />;

  const othersInRoom = room.participants.filter(participant => participant.id !== user?.id).length;

  return (
    <div className="page max-w-7xl space-y-4">
      {backButton}

      {inviting && !room.isClosed && <InviteDialog roomId={id} onClose={closeInvite} />}

      <section className="hero p-5 sm:p-6">
        <div className="relative space-y-1.5">
          <p className="text-xs font-bold uppercase tracking-widest text-indigo-100">{room.isClosed ? 'Sala cerrada' : 'Sala de estudio'}</p>
          <h1 className="text-2xl sm:text-3xl font-extrabold break-words">{room.title}</h1>
          {room.objective && (
            <p className="text-indigo-100 flex items-start gap-2">
              <Flag className="w-4 h-4 shrink-0 mt-1" aria-hidden="true" />
              <span className="break-words min-w-0">{room.objective}</span>
            </p>
          )}
        </div>
      </section>

      {connectionLost && <ErrorState message="Se perdió la conexión. Reintentando..." />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <section className="card lg:col-span-2 flex flex-col h-[60vh] min-h-96" aria-label="Conversación">
          <div ref={chatRef} onScroll={handleScroll} className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4" aria-live="polite">
            {messages.length === 0 && (
              <p className="text-center text-sm text-muted py-12">
                Nadie ha escrito todavía. Empieza con una duda o comparte un archivo: no hace falta saber la respuesta.
              </p>
            )}
            {messages.map(message => {
              const mine = message.senderId === user?.id;
              const youTubeId = findYouTubeId(message.content);
              return (
                <div key={message.id} className={`flex items-end gap-2 ${mine ? 'flex-row-reverse' : ''}`}>
                  <Avatar name={message.senderName} photoUrl={message.senderPhotoUrl} tone={mine ? 'teach' : 'learn'} className="w-8 h-8 text-sm" />
                  <div className={`max-w-[80%] min-w-0 space-y-1 ${mine ? 'text-right' : ''}`}>
                    <p className="text-xs">
                      <span className="font-bold">{mine ? 'Tú' : message.senderName}</span>{' '}
                      <span className="text-muted">{formatTime(message.createdAt)}</span>
                    </p>
                    {message.content && (
                      <p className={`inline-block text-left whitespace-pre-wrap break-words px-3.5 py-2.5 rounded-2xl text-sm ${mine ? 'bg-teach-soft rounded-br-sm' : 'bg-learn-soft rounded-bl-sm'}`}>
                        {message.content}
                      </p>
                    )}
                    {message.attachment && <AttachmentView roomId={id} attachment={message.attachment} />}
                    {youTubeId && <YouTubeEmbed videoId={youTubeId} />}
                  </div>
                </div>
              );
            })}
          </div>

          {sendError && <div className="px-4 pb-2"><ErrorState message={sendError} /></div>}

          {!room.isClosed && (
          <form onSubmit={handleSend} className="p-4 border-t border-line flex items-center gap-2">
            <input ref={fileInput} type="file" accept={ACCEPTED_FILES} onChange={handleFile} className="hidden" aria-label="Archivo para compartir" />
            <button
              type="button"
              onClick={() => fileInput.current?.click()}
              disabled={uploading}
              aria-label="Compartir imagen, audio, vídeo o PDF"
              title="Compartir imagen, audio, vídeo o PDF (hasta 4 MB)"
              className="btn btn-secondary px-4!"
            >
              <Paperclip className="w-4 h-4" />
            </button>
            <input
              value={draft}
              onChange={e => setDraft(e.target.value)}
              maxLength={2000}
              placeholder={uploading ? 'Subiendo archivo...' : 'Escribe un mensaje o pega un enlace de YouTube...'}
              aria-label="Mensaje"
              className="field flex-1 min-w-0"
            />
            <button type="submit" disabled={sending || !draft.trim()} aria-label="Enviar mensaje" className="btn btn-primary px-4!">
              <Send className="w-4 h-4" />
            </button>
          </form>
          )}
        </section>

        <aside className="space-y-6" aria-label="Información de la sala">
          {!room.isClosed && <ContrastaPanel roomId={id} />}

          <section className="card p-5 space-y-4">
            <h2 className="text-lg text-ink flex items-center gap-2">
              <Users className="w-5 h-5 text-teach" aria-hidden="true" />
              <span>En la sala ({room.participantCount})</span>
            </h2>
            <ul className="space-y-2">
              {room.participants.map(participant => (
                <li key={participant.id} className="flex items-center gap-2.5 min-w-0">
                  <Avatar name={participant.name} photoUrl={participant.photoUrl} className="w-8 h-8 text-sm" />
                  <span className="text-sm font-semibold truncate flex-1 min-w-0">
                    {participant.name}{participant.id === user?.id && <span className="text-muted font-normal"> (tú)</span>}
                  </span>
                  {participant.id !== user?.id && (
                    <FriendButton
                      personId={participant.id}
                      status={friendStatuses[participant.id] ?? null}
                      onError={setSendError}
                      onChange={status => setFriendStatuses(current => ({ ...current, [participant.id]: status }))}
                    />
                  )}
                </li>
              ))}
            </ul>
            {!room.isClosed && (
              <>
                <button onClick={() => setInviting(true)} className="btn btn-primary w-full">
                  <UserPlus className="w-4 h-4" aria-hidden="true" />
                  <span>Invitar personas</span>
                </button>
                <button onClick={handleCopyLink} className="btn btn-secondary w-full">
                  {copied ? <Check className="w-4 h-4" /> : <Link2 className="w-4 h-4" />}
                  <span>{copied ? 'Enlace copiado' : 'Invitar con un enlace'}</span>
                </button>
                {!confirmingLeave && (
                  <button onClick={() => setConfirmingLeave(true)} className="btn btn-secondary w-full">
                    <LogOut className="w-4 h-4" />
                    <span>Salir de la sala</span>
                  </button>
                )}
                {confirmingLeave && (
                  <div className="rounded-2xl bg-learn-soft p-4 space-y-3" role="alertdialog" aria-label="Confirmar salida">
                    <p className="text-sm font-bold text-learn-strong">
                      {othersInRoom === 0
                        ? 'Eres la última persona: la sala se cerrará y ya nadie podrá ver sus mensajes ni archivos.'
                        : `Dejarás de ver sus mensajes y archivos, y para volver necesitarás otra invitación. Tendrás que evaluar a ${othersInRoom === 1 ? 'la otra persona' : `las ${othersInRoom} personas`} de la sala.`}
                    </p>
                    <div className="flex gap-2">
                      <button onClick={handleLeave} disabled={leaving} className="btn btn-primary flex-1">
                        {leaving ? 'Saliendo...' : 'Sí, salir'}
                      </button>
                      <button onClick={() => setConfirmingLeave(false)} disabled={leaving} className="btn btn-secondary flex-1">Cancelar</button>
                    </div>
                  </div>
                )}
              </>
            )}
          </section>

          {!room.isClosed && (
            <>
              <StudyMindPanel roomId={id} />
              <TeachBackPanel roomId={id} />
            </>
          )}
        </aside>
      </div>
    </div>
  );
};
