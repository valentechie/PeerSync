import { apiRequest } from './api';

export interface RevealedAnswer {
  userId: string;
  name: string;
  answer: string;
}

export interface ContrastaRound {
  id: string;
  prompt: string;
  status: 'individual' | 'revealed';
  createdAt: string;
  revealedAt: string | null;
  answeredBy: { id: string; name: string }[];
  waitingForCount: number;
  myAnswer: string | null;
  answers: RevealedAnswer[];
}

export interface ContrastaState {
  round: ContrastaRound | null;
}

export interface Facilitation {
  source: 'ai' | 'fallback';
  kind: 'evidence_check' | 'edge_case' | 'missing_information' | 'open_question';
  messageToPeers: string;
  suggestedAction: string;
  evidenceNeeded: string;
  uncertaintyNote: string;
}

const base = (roomId: string) => `/rooms/${encodeURIComponent(roomId)}`;

export const fetchContrasta = (token: string, roomId: string) =>
  apiRequest<ContrastaState>(`${base(roomId)}/contrasta`, { token });

export const startRound = (token: string, roomId: string, prompt: string) =>
  apiRequest<ContrastaState>(`${base(roomId)}/contrasta/rounds`, { method: 'POST', body: { prompt }, token });

export const submitAnswer = (token: string, roomId: string, answer: string) =>
  apiRequest<ContrastaState>(`${base(roomId)}/contrasta/answers`, { method: 'POST', body: { answer }, token });

export const requestFacilitation = (token: string, roomId: string) =>
  apiRequest<Facilitation>(`${base(roomId)}/ai/facilitate`, { method: 'POST', token });
