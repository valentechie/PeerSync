import { apiRequest } from './api';

export interface Partner {
  id: string;
  name: string;
  bio: string;
  skillsOffering: string[];
  skillsSeeking: string[];
  reputation: number | null;
  completedSessions: number;
  score: number;
  breakdown: {
    learnPoints: number;
    teachPoints: number;
    reputationPoints: number;
    theyTeachYou: string[];
    youTeachThem: string[];
  };
  requestStatus: 'sent' | 'received' | 'connected' | null;
}

export const fetchSuggestions = (token: string) =>
  apiRequest<Partner[]>('/matching/suggestions', { token });

export const fetchPartner = (token: string, id: string) =>
  apiRequest<Partner>(`/matching/partners/${encodeURIComponent(id)}`, { token });

export const sendMatchRequest = (token: string, receiverId: string) =>
  apiRequest<unknown>('/matching/requests', { method: 'POST', body: { receiverId }, token });
