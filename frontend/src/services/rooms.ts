import { apiRequest } from './api';

export interface RoomSummary {
  id: string;
  title: string;
  objective: string;
  participantCount: number;
  isMember: boolean;
  lastActivityAt: string;
}

export interface RoomDetail extends RoomSummary {
  participants: { id: string; name: string }[];
}

export interface RoomMessage {
  id: string;
  senderId: string;
  senderName: string;
  content: string;
  createdAt: string;
}

export const fetchRooms = (token: string) => apiRequest<RoomSummary[]>('/rooms', { token });

export const createRoom = (token: string, title: string, objective: string) =>
  apiRequest<RoomDetail>('/rooms', { method: 'POST', body: { title, objective }, token });

export const fetchRoom = (token: string, id: string) =>
  apiRequest<RoomDetail>(`/rooms/${encodeURIComponent(id)}`, { token });

export const joinRoom = (token: string, id: string) =>
  apiRequest<RoomDetail>(`/rooms/${encodeURIComponent(id)}/join`, { method: 'POST', token });

export const leaveRoom = (token: string, id: string) =>
  apiRequest<void>(`/rooms/${encodeURIComponent(id)}/leave`, { method: 'POST', token });

export const fetchMessages = (token: string, id: string) =>
  apiRequest<RoomMessage[]>(`/rooms/${encodeURIComponent(id)}/messages`, { token });

export const sendMessage = (token: string, id: string, content: string) =>
  apiRequest<RoomMessage>(`/rooms/${encodeURIComponent(id)}/messages`, { method: 'POST', body: { content }, token });
