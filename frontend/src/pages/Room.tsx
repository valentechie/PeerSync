import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Check, Flag, Lightbulb, Link2, LogOut, MessageSquareQuote, Send, Users } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import { fetchFriends, type FriendStatus } from '../services/people';
import { fetchMessages, fetchRoom, joinRoom, leaveRoom, sendMessage, type RoomDetail, type RoomMessage } from '../services/rooms';
import { ErrorState, LoadingState } from '../components/UIStates';
import { Avatar } from '../components/Swap';
import { FriendButton } from '../components/FriendButton';

const POLL_INTERVAL_MS = 3000;

const formatTime = (iso: string) => new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

export const Room: React.FC = () => {
  const { id = '' } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const [room, setRoom] = useState<RoomDetail | null>(null);
  const [messages, setMessages] = useState<RoomMessage[]>([]);
  const [loadError, setLoadError] = useState('');
  const [connectionLost, setConnectionLost] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState('');
  const [copied, setCopied] = useState(false);
  const [friendStatuses, setFriendStatuses] = useState<Record<string, FriendStatus>>({});
  const chatRef = useRef<HTMLDivElement>(null);
  const followChat = useRef(true);

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

    joinRoom(token, id)
      .then(joined => {
        if (cancelled) return;
        setRoom(joined);
        void refresh();
        timer = setInterval(refresh, POLL_INTERVAL_MS);
      })
      .catch((err: unknown) => {
        if (!cancelled) setLoadError(errorMessage(err));
      });

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [token, id, attempt]);

  // Si esto falla, la sala sigue funcionando: solo no se sabrá quién es amigo.
  useEffect(() => {
    if (!token) return;
    fetchFriends(token)
      .then(({ friends, received, sent }) => {
        setFriendStatuses(Object.fromEntries([...friends, ...received, ...sent].map(person => [person.id, person.friendStatus])));
      })
      .catch(() => undefined);
  }, [token]);

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

  const handleLeave = async () => {
    if (!token) return;
    try {
      await leaveRoom(token, id);
      navigate('/rooms');
    } catch (err) {
      setSendError(errorMessage(err));
    }
  };

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setSendError('No se pudo copiar el enlace. Cópialo desde la barra del navegador.');
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
          onRetry={() => {
            setLoadError('');
            setAttempt(current => current + 1);
          }}
        />
      </div>
    );
  }

  if (!room) return <LoadingState message="Entrando en la sala..." />;

  return (
    <div className="page max-w-7xl space-y-4">
      {backButton}

      <section className="hero p-5 sm:p-6">
        <div className="relative space-y-1.5">
          <p className="text-xs font-bold uppercase tracking-widest text-indigo-100">Sala de estudio</p>
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
                Nadie ha escrito todavía. Empieza con una duda: no hace falta saber la respuesta.
              </p>
            )}
            {messages.map(message => {
              const mine = message.senderId === user?.id;
              return (
                <div key={message.id} className={`flex items-end gap-2 ${mine ? 'flex-row-reverse' : ''}`}>
                  <Avatar name={message.senderName} tone={mine ? 'teach' : 'learn'} className="w-8 h-8 text-sm" />
                  <div className={`max-w-[80%] min-w-0 space-y-1 ${mine ? 'text-right' : ''}`}>
                    <p className="text-xs">
                      <span className="font-bold">{mine ? 'Tú' : message.senderName}</span>{' '}
                      <span className="text-muted">{formatTime(message.createdAt)}</span>
                    </p>
                    <p className={`inline-block text-left whitespace-pre-wrap break-words px-3.5 py-2.5 rounded-2xl text-sm ${mine ? 'bg-teach-soft rounded-br-sm' : 'bg-learn-soft rounded-bl-sm'}`}>
                      {message.content}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {sendError && <div className="px-4 pb-2"><ErrorState message={sendError} /></div>}

          <form onSubmit={handleSend} className="p-4 border-t border-line flex items-center gap-2">
            <input
              value={draft}
              onChange={e => setDraft(e.target.value)}
              maxLength={2000}
              placeholder="Escribe un mensaje..."
              aria-label="Mensaje"
              className="field flex-1 min-w-0"
            />
            <button type="submit" disabled={sending || !draft.trim()} aria-label="Enviar mensaje" className="btn btn-primary px-4!">
              <Send className="w-4 h-4" />
            </button>
          </form>
        </section>

        <aside className="space-y-6" aria-label="Información de la sala">
          <section className="card p-5 space-y-4">
            <h2 className="text-lg text-ink flex items-center gap-2">
              <Users className="w-5 h-5 text-teach" aria-hidden="true" />
              <span>En la sala ({room.participantCount})</span>
            </h2>
            <ul className="space-y-2">
              {room.participants.map(participant => (
                <li key={participant.id} className="flex items-center gap-2.5 min-w-0">
                  <Avatar name={participant.name} className="w-8 h-8 text-sm" />
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
            <button onClick={handleCopyLink} className="btn btn-secondary w-full">
              {copied ? <Check className="w-4 h-4" /> : <Link2 className="w-4 h-4" />}
              <span>{copied ? 'Enlace copiado' : 'Invitar con un enlace'}</span>
            </button>
            <button onClick={handleLeave} className="btn btn-secondary w-full">
              <LogOut className="w-4 h-4" />
              <span>Salir de la sala</span>
            </button>
          </section>

          <section className="card p-5 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-lg text-ink">Apoyo de IA</h2>
              <span className="chip chip-demo">Próximamente</span>
            </div>
            <p className="text-sm text-muted">Tus compañeros van primero. La IA ayudará solo cuando se lo pidas.</p>
            <p className="text-sm text-muted flex gap-2">
              <Lightbulb className="w-4 h-4 text-guide shrink-0 mt-0.5" aria-hidden="true" />
              <span><strong className="text-ink">StudyMind:</strong> pistas progresivas sin dar la solución.</span>
            </p>
            <p className="text-sm text-muted flex gap-2">
              <MessageSquareQuote className="w-4 h-4 text-guide shrink-0 mt-0.5" aria-hidden="true" />
              <span><strong className="text-ink">TeachBack:</strong> explica un concepto y recibe opinión de un compañero.</span>
            </p>
          </section>
        </aside>
      </div>
    </div>
  );
};
