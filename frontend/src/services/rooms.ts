import { apiBlob, apiRequest, apiUpload } from './api';

export interface RoomSummary {
  id: string;
  title: string;
  objective: string;
  participantCount: number;
  isMember: boolean;
  isClosed: boolean;
  lastActivityAt: string;
}

export interface RoomDetail extends RoomSummary {
  participants: { id: string; name: string }[];
}

export interface RoomAttachment {
  id: string;
  fileName: string;
  contentType: string;
  size: number;
}

export interface RoomMessage {
  id: string;
  senderId: string;
  senderName: string;
  content: string;
  createdAt: string;
  attachment: RoomAttachment | null;
}

export const fetchRooms = (token: string) => apiRequest<RoomSummary[]>('/rooms', { token });

export const createRoom = (token: string, title: string, objective: string) =>
  apiRequest<RoomDetail>('/rooms', { method: 'POST', body: { title, objective }, token });

export const fetchRoom = (token: string, id: string) =>
  apiRequest<RoomDetail>(`/rooms/${encodeURIComponent(id)}`, { token });

export const joinRoom = (token: string, id: string) =>
  apiRequest<RoomDetail>(`/rooms/${encodeURIComponent(id)}/join`, { method: 'POST', token });

export const leaveRoom = (token: string, id: string) =>
  apiRequest<unknown>(`/rooms/${encodeURIComponent(id)}/leave`, { method: 'POST', token });

export const fetchMessages = (token: string, id: string) =>
  apiRequest<RoomMessage[]>(`/rooms/${encodeURIComponent(id)}/messages`, { token });

export const sendMessage = (token: string, id: string, content: string) =>
  apiRequest<RoomMessage>(`/rooms/${encodeURIComponent(id)}/messages`, { method: 'POST', body: { content }, token });

export const uploadAttachment = (token: string, id: string, file: File) =>
  apiUpload<RoomMessage>(`/rooms/${encodeURIComponent(id)}/attachments?fileName=${encodeURIComponent(file.name)}`, file, token);

export const fetchAttachment = (token: string, roomId: string, attachmentId: string) =>
  apiBlob(`/rooms/${encodeURIComponent(roomId)}/attachments/${encodeURIComponent(attachmentId)}`, token);
