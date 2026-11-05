import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
import { ContrastaActionMenu } from '../components/ContrastaActionMenu';
import { ActionForm, CheckCard, ConclusionCard, HelpResultCard, RevealCard, RoundCard, SessionCard, SuggestionCard } from '../components/ContrastaCards';
import { TeachBackActivityCard } from '../components/TeachBackActivityCard';
import { FlowContext, useContrastaFlow, type FlowContextValue, type FormKey } from '../components/contrastaFlowContext';
import type { Activity, Flow } from '../services/contrastaFlow';

const POLL_INTERVAL_MS = 3000;
const MAX_FILE_BYTES = 4 * 1024 * 1024;
const ACCEPTED_FILES = 'image/png,image/jpeg,image/gif,image/webp,audio/mpeg,audio/ogg,audio/wav,audio/mp4,audio/x-m4a,video/mp4,video/webm,application/pdf';

const formatTime = (iso: string) => new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

type TimelineItem =
  | { key: string; at: string; type: 'message'; message: RoomMessage }
  | { key: string; at: string; type: 'card'; render: () => React.ReactNode };

/** Mezcla mensajes y tarjetas por orden cronológico, sin tocar los mensajes. */
const buildTimeline = (messages: RoomMessage[], flow: Flow | null): TimelineItem[] => {
  const items: TimelineItem[] = messages.map(message => ({ key: `message:${message.id}`, at: message.createdAt, type: 'message', message }));
  const round = flow?.round;
  if (flow && round) {
    const card = (key: string, at: string, render: () => React.ReactNode) => items.push({ key, at, type: 'card', render });
    card(`round:${round.id}`, round.createdAt, () => <RoundCard flow={flow} />);
    if (round.revealedAt) card(`reveal:${round.id}`, round.revealedAt, () => <RevealCard flow={flow} />);
    flow.cards.forEach(help => card(`help:${help.id}`, help.createdAt, () => <HelpResultCard card={help} />));
    if (round.conclusion) card(`conclusion:${round.id}`, round.conclusion.at, () => <ConclusionCard flow={flow} />);
    flow.activities.forEach(activity => card(`activity:${activity.id}`, activity.createdAt, () => <TeachBackActivityCard activity={activity} />));
    if (flow.check) card(`check:${round.id}`, flow.check.createdAt, () => <CheckCard flow={flow} />);
    if (flow.suggestion) card(`suggestion:${round.id}:${flow.suggestion.key}`, flow.suggestion.at, () => <SuggestionCard key={`${round.id}:${flow.suggestion?.key}`} flow={flow} />);
  }
  return items.sort((a, b) => Date.parse(a.at) - Date.parse(b.at) || a.key.localeCompare(b.key));
};

const isEditing = (container: HTMLElement) => {
  const active = document.activeElement;
  return Boolean(active && container.contains(active) && ['TEXTAREA', 'INPUT', 'SELECT'].includes(active.tagName));
};

/** Lo que espera a esta persona: permite volver a una tarjeta que ha quedado arriba. */
const pendingForMe = (flow: Flow | null, userId?: string): { text: string; target: string } | null => {
  const round = flow?.round;
  if (!flow || !round || round.finishedAt) return null;
  const open = flow.activities.find(activity => activity.status === 'pending' || activity.status === 'active');
  const step = flow.step ? `Step ${flow.step.number} of 6 · ` : '';
  if (open) return { text: `${step}${activityStatusText(open, userId)}`, target: `activity:${open.id}` };
  if (round.status === 'individual' && !round.iHaveAnswered) return { text: `${step}Your answer is pending`, target: `round:${round.id}` };
  if (flow.check && !flow.check.iHaveAnswered) return { text: `${step}A new question is waiting`, target: `check:${round.id}` };
  return null;
};

const activityStatusText = (activity: Activity, userId?: string) => {
  if (activity.status === 'pending') {
    return activity.partner.id === userId ? `${activity.proposer.name} proposed TeachBack` : 'TeachBack proposal pending';
  }
  const explainer = activity.turn === 1 ? activity.proposer : activity.partner;
  const current = activity.turns.find(turn => turn.turn === activity.turn);
  if (!current) return explainer.id === userId ? 'Your turn to explain' : `${explainer.name} is explaining`;
  if (!current.review) return explainer.id === userId ? 'Waiting for a review' : 'Your turn to review';
  return 'TeachBack turn reviewed';
};

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
  const composerInput = useRef<HTMLInputElement>(null);
  const [hasNew, setHasNew] = useState(false);
  const [announcement, setAnnouncement] = useState('');
  const [openForm, setOpenForm] = useState<FormKey | null>(null);

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
      .then(link => setInviteUrl(`${window.location.origin}${import.meta.env.BASE_URL}rooms/${roomId}?invite=${encodeURIComponent(link.token)}`))
      .catch(() => undefined);
  }, [token, roomId, roomIsClosed]);

  const { flow, apply: applyFlow, refresh: refreshFlow } = useContrastaFlow(token, roomId);
  const timeline = useMemo(() => buildTimeline(messages, flow), [messages, flow]);

  // Baja solo si hay algo nuevo, y nunca mientras se está escribiendo en una tarjeta.
  const lastItem = timeline[timeline.length - 1];
  const contentSignature = `${timeline.length}:${lastItem?.key}:${flow ? JSON.stringify(flow).length : 0}`;
  const seenSignature = useRef('');
  const seenLastKey = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (seenSignature.current === contentSignature) return;
    seenSignature.current = contentSignature;
    const chat = chatRef.current;
    if (!chat) return;
    if (followChat.current && !isEditing(chat)) {
      chat.scrollTop = chat.scrollHeight;
      setHasNew(false);
    } else {
      setHasNew(true);
    }
  }, [contentSignature]);

  // Un aviso breve para lectores de pantalla: las tarjetas y sus formularios no se anuncian enteros.
  useEffect(() => {
    if (!lastItem || seenLastKey.current === lastItem.key) return;
    const first = seenLastKey.current === undefined;
    seenLastKey.current = lastItem.key;
    if (first) return;
    if (lastItem.type === 'message') {
      if (lastItem.message.senderId !== user?.id) setAnnouncement(`${lastItem.message.senderName}: ${lastItem.message.content.slice(0, 200)}`);
    } else {
      setAnnouncement('Contrasta has a new update in the conversation.');
    }
  }, [lastItem, user?.id]);

  const handleScroll = () => {
    const chat = chatRef.current;
    if (!chat) return;
    followChat.current = chat.scrollHeight - chat.scrollTop - chat.clientHeight < 80;
    if (followChat.current) setHasNew(false);
  };

  const scrollToEnd = useCallback(() => {
    const chat = chatRef.current;
    if (!chat) return;
    followChat.current = true;
    setHasNew(false);
    chat.scrollTop = chat.scrollHeight;
  }, []);

  // El menú lo abre el estudiante: aquí sí se lleva la vista al formulario.
  const openActionForm = useCallback((form: FormKey) => setOpenForm(form), []);
  useEffect(() => {
    if (openForm) scrollToEnd();
  }, [openForm, scrollToEnd]);

  const focusComposer = useCallback(() => composerInput.current?.focus(), []);

  const flowContext = useMemo<FlowContextValue | null>(
    () =>
      flow && token && user && roomId
        ? {
            roomId,
            token,
            userId: user.id,
            flow,
            readOnly: Boolean(roomIsClosed),
            apply: applyFlow,
            refresh: refreshFlow,
            openForm: openActionForm,
            focusComposer,
          }
        : null,
    [flow, token, user, roomId, roomIsClosed, applyFlow, refreshFlow, openActionForm, focusComposer],
  );

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
      setSendError("The file can't be larger than 4 MB. For long videos, paste a YouTube link.");
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
      setSendError("The link isn't ready yet. Try again in a moment.");
      return;
    }
    try {
      await navigator.clipboard.writeText(inviteUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setSendError(`Couldn't copy the link. Try inviting the person from "Invite people".`);
    }
  };

  const backButton = (
    <button
      onClick={() => navigate('/rooms')}
      className="inline-flex items-center gap-2 text-sm font-bold text-muted hover:text-ink transition-colors cursor-pointer"
    >
      <ArrowLeft className="w-4 h-4" />
      <span>Rooms</span>
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

  if (!room) return <LoadingState message="Entering the room..." />;

  const renderMessage = (message: RoomMessage) => {
    const mine = message.senderId === user?.id;
    const youTubeId = findYouTubeId(message.content);
    return (
      <div key={message.id} className={`flex items-end gap-2 ${mine ? 'flex-row-reverse' : ''}`}>
        <Avatar name={message.senderName} photoUrl={message.senderPhotoUrl} tone={mine ? 'teach' : 'learn'} className="w-8 h-8 text-sm" />
        <div className={`max-w-[80%] min-w-0 space-y-1 ${mine ? 'text-right' : ''}`}>
          <p className="text-xs">
            <span className="font-bold">{mine ? 'You' : message.senderName}</span>{' '}
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
  };

  const others = room.participants.filter(participant => participant.id !== user?.id);
  const othersInRoom = others.length;
  const pending = pendingForMe(flow, user?.id);

  return (
    <div className="page max-w-7xl space-y-4">
      {backButton}

      {inviting && !room.isClosed && <InviteDialog roomId={id} onClose={closeInvite} />}

      <section className="hero p-5 sm:p-6">
        <div className="relative space-y-1.5">
          <p className="text-xs font-bold uppercase tracking-widest text-indigo-100">{room.isClosed ? 'Room closed' : 'Study room'}</p>
          <h1 className="text-2xl sm:text-3xl font-extrabold break-words">{room.title}</h1>
          {room.objective && (
            <p className="text-indigo-100 flex items-start gap-2">
              <Flag className="w-4 h-4 shrink-0 mt-1" aria-hidden="true" />
              <span className="break-words min-w-0">{room.objective}</span>
            </p>
          )}
        </div>
      </section>

      {connectionLost && <ErrorState message="Connection lost. Retrying..." />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <section className="card lg:col-span-2 flex flex-col h-[60vh] lg:h-[65vh] min-h-96" aria-label="Conversation">
          <p className="sr-only" aria-live="polite">{announcement}</p>
          {pending && (
            <div className="px-4 py-2 border-b border-line flex flex-wrap items-center justify-between gap-x-3 gap-y-1 text-xs">
              <span className="font-bold min-w-0 break-words">{pending.text}</span>
              <button
                type="button"
                onClick={() => document.getElementById(`timeline-${pending.target}`)?.scrollIntoView({ block: 'start' })}
                className="font-bold text-teach-strong cursor-pointer shrink-0"
              >
                Go to activity
              </button>
            </div>
          )}
          <div className="relative flex-1 min-h-0 flex flex-col">
          <div ref={chatRef} onScroll={handleScroll} className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-6 space-y-4">
            {timeline.length === 0 && (
              <p className="text-center text-sm text-muted py-12">
                Nobody has written yet. Start with a question or share a file: you don't need to know the answer.
              </p>
            )}
            {flowContext ? (
              <FlowContext.Provider value={flowContext}>
                {timeline.map(item => {
                  if (item.type === 'card') return <div key={item.key} id={`timeline-${item.key}`}>{item.render()}</div>;
                  return renderMessage(item.message);
                })}
                {openForm && <ActionForm key={openForm} form={openForm} flow={flowContext.flow} others={others} onClose={() => setOpenForm(null)} />}
              </FlowContext.Provider>
            ) : (
              messages.map(renderMessage)
            )}
          </div>
          {hasNew && (
            <button type="button" onClick={scrollToEnd} className="chip chip-teach absolute bottom-2 left-1/2 -translate-x-1/2 cursor-pointer shadow">
              New updates below
            </button>
          )}
          </div>

          {sendError && <div className="px-4 pb-2"><ErrorState message={sendError} /></div>}

          {!room.isClosed && (
          <form onSubmit={handleSend} className="relative p-4 border-t border-line flex items-center gap-2 max-[359px]:flex-wrap">
            <input ref={fileInput} type="file" accept={ACCEPTED_FILES} onChange={handleFile} className="hidden" aria-label="File to share" />
            <button
              type="button"
              onClick={() => fileInput.current?.click()}
              disabled={uploading}
              aria-label="Share an image, audio, video or PDF"
              title="Share an image, audio, video or PDF (up to 4 MB)"
              className="btn btn-secondary px-4!"
            >
              <Paperclip className="w-4 h-4" />
            </button>
            <ContrastaActionMenu actions={flow?.actions ?? []} onSelect={openActionForm} />
            <input
              ref={composerInput}
              value={draft}
              onChange={e => setDraft(e.target.value)}
              maxLength={2000}
              placeholder={uploading ? 'Uploading file...' : 'Type a message or paste a YouTube link...'}
              aria-label="Message"
              className="field flex-1 min-w-0 max-[359px]:order-first max-[359px]:basis-full"
            />
            <button type="submit" disabled={sending || !draft.trim()} aria-label="Send message" className="btn btn-primary px-4! max-[359px]:ml-auto">
              <Send className="w-4 h-4" />
            </button>
          </form>
          )}
        </section>

        <aside className="space-y-6" aria-label="Room information">
          {flowContext && <FlowContext.Provider value={flowContext}><SessionCard flow={flowContext.flow} /></FlowContext.Provider>}

          <section className="card p-5 space-y-4">
            <h2 className="text-lg text-ink flex items-center gap-2">
              <Users className="w-5 h-5 text-teach" aria-hidden="true" />
              <span>In the room ({room.participantCount})</span>
            </h2>
            <ul className="space-y-2">
              {room.participants.map(participant => (
                <li key={participant.id} className="flex items-center gap-2.5 min-w-0">
                  <Avatar name={participant.name} photoUrl={participant.photoUrl} className="w-8 h-8 text-sm" />
                  <span className="text-sm font-semibold truncate flex-1 min-w-0">
                    {participant.name}{participant.id === user?.id && <span className="text-muted font-normal"> (you)</span>}
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
                  <span>Invite people</span>
                </button>
                <button onClick={handleCopyLink} className="btn btn-secondary w-full">
                  {copied ? <Check className="w-4 h-4" /> : <Link2 className="w-4 h-4" />}
                  <span>{copied ? 'Link copied' : 'Invite with a link'}</span>
                </button>
                {!confirmingLeave && (
                  <button onClick={() => setConfirmingLeave(true)} className="btn btn-secondary w-full">
                    <LogOut className="w-4 h-4" />
                    <span>Leave the room</span>
                  </button>
                )}
                {confirmingLeave && (
                  <div className="rounded-2xl bg-learn-soft p-4 space-y-3" role="alertdialog" aria-label="Confirm leaving">
                    <p className="text-sm font-bold text-learn-strong">
                      {othersInRoom === 0
                        ? 'You are the last person: the room will close and nobody will be able to see its messages or files.'
                        : `You will no longer see its messages and files, and you will need another invitation to come back. You will have to rate ${othersInRoom === 1 ? 'the other person' : `the ${othersInRoom} people`} in the room.`}
                    </p>
                    <div className="flex gap-2">
                      <button onClick={handleLeave} disabled={leaving} className="btn btn-primary flex-1">
                        {leaving ? 'Leaving...' : 'Yes, leave'}
                      </button>
                      <button onClick={() => setConfirmingLeave(false)} disabled={leaving} className="btn btn-secondary flex-1">Cancel</button>
                    </div>
                  </div>
                )}
              </>
            )}
          </section>

          {!room.isClosed && (
            <>
              <ContrastaPanel roomId={id} />
              <StudyMindPanel roomId={id} />
              <TeachBackPanel roomId={id} />
            </>
          )}
        </aside>
      </div>
    </div>
  );
};
