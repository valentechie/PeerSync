import { apiRequest } from './api';

export interface ReviewScores {
  punctuality: number;
  treatment: number;
  participation: number;
  clarity: number;
}

export const CRITERIA: { key: keyof ReviewScores; label: string; hint: string }[] = [
  { key: 'punctuality', label: 'Puntualidad', hint: '¿Llegó a tiempo y respetó el horario?' },
  { key: 'treatment', label: 'Trato', hint: '¿Fue respetuoso y agradable?' },
  { key: 'participation', label: 'Participación', hint: '¿Se implicó y aportó a la sala?' },
  { key: 'clarity', label: 'Claridad', hint: '¿Se le entendía al explicar?' },
];

export const INITIAL_SCORE = 5;

export interface PendingReview {
  roomId: string;
  roomTitle: string;
  personId: string;
  personName: string;
}

export interface FeedbackItem extends ReviewScores {
  id: string;
  reviewerName: string;
  roomTitle: string;
  createdAt: string;
}

export interface FeedbackSummary {
  count: number;
  average: number | null;
  punctuality: number | null;
  treatment: number | null;
  participation: number | null;
  clarity: number | null;
  items: FeedbackItem[];
}

export const submitReview = (token: string, roomId: string, revieweeId: string, scores: ReviewScores) =>
  apiRequest<unknown>(`/rooms/${encodeURIComponent(roomId)}/reviews`, {
    method: 'POST',
    body: { revieweeId, ...scores },
    token,
  });

export const fetchFeedback = (token: string) => apiRequest<FeedbackSummary>('/profiles/me/feedback', { token });

export const fetchPendingReviews = (token: string) => apiRequest<PendingReview[]>('/profiles/me/pending-reviews', { token });
