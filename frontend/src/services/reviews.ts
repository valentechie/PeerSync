import { apiRequest } from './api';

export interface ReviewScores {
  clarity: number;
  listening: number;
  preparation: number;
}

export const CRITERIA: { key: keyof ReviewScores; label: string; hint: string }[] = [
  { key: 'clarity', label: 'Claridad', hint: '¿Se le entendía al explicar?' },
  { key: 'listening', label: 'Escucha', hint: '¿Escuchó y respetó a los demás?' },
  { key: 'preparation', label: 'Preparación', hint: '¿Llegó con el tema trabajado?' },
];

export const MIN_COMMENT_LENGTH = 20;

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
  comment: string;
  createdAt: string;
}

export interface FeedbackSummary {
  count: number;
  average: number | null;
  clarity: number | null;
  listening: number | null;
  preparation: number | null;
  items: FeedbackItem[];
}

export const submitReview = (token: string, roomId: string, revieweeId: string, scores: ReviewScores, comment: string) =>
  apiRequest<unknown>(`/rooms/${encodeURIComponent(roomId)}/reviews`, {
    method: 'POST',
    body: { revieweeId, ...scores, comment },
    token,
  });

export const fetchFeedback = (token: string) => apiRequest<FeedbackSummary>('/profiles/me/feedback', { token });

export const fetchPendingReviews = (token: string) => apiRequest<PendingReview[]>('/profiles/me/pending-reviews', { token });
