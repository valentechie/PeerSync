import { apiRequest } from './api';

export interface InviteCandidate {
  id: string;
  name: string;
  study: string | null;
  photoUrl: string | null;
  isFriend: boolean;
  status: 'member' | 'invited' | 'declined' | null;
}

export interface RoomInvitation {
  id: string;
  roomId: string;
  roomTitle: string;
  roomObjective: string;
  inviterName: string;
  createdAt: string;
}

export const fetchInviteCandidates = (token: string, roomId: string, search: string) =>
  apiRequest<InviteCandidate[]>(
    `/rooms/${encodeURIComponent(roomId)}/invite-candidates${search ? `?search=${encodeURIComponent(search)}` : ''}`,
    { token },
  );

export const inviteToRoom = (token: string, roomId: string, inviteeId: string) =>
  apiRequest<InviteCandidate>(`/rooms/${encodeURIComponent(roomId)}/invitations`, {
    method: 'POST',
    body: { inviteeId },
    token,
  });

export const fetchInvitations = (token: string) => apiRequest<RoomInvitation[]>('/invitations', { token });

export const acceptInvitation = (token: string, id: string) =>
  apiRequest<{ roomId: string }>(`/invitations/${encodeURIComponent(id)}/accept`, { method: 'POST', token });

export const declineInvitation = (token: string, id: string) =>
  apiRequest<void>(`/invitations/${encodeURIComponent(id)}`, { method: 'DELETE', token });
