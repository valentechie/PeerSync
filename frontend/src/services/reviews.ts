import { apiRequest } from './api';

export interface ReviewScores {
  punctuality: number;
  treatment: number;
  participation: number;
  clarity: number;
}

export const CRITERIA: { key: keyof ReviewScores; label: string; hint: string }[] = [
  { key: 'punctuality', label: 'Punctuality', hint: 'Were they on time and did they respect the schedule?' },
  { key: 'treatment', label: 'Respect', hint: 'Were they respectful and pleasant?' },
  { key: 'participation', label: 'Participation', hint: 'Did they get involved and contribute to the room?' },
  { key: 'clarity', label: 'Clarity', hint: 'Were they easy to understand when explaining?' },
];

export const INITIAL_SCORE = 5;

export interface PendingReview {
  roomId: string;
  roomTitle: string;
  personId: string;
  personName: string;
  personPhotoUrl: string | null;
}

export interface FeedbackItem extends ReviewScores {
  id: string;
  reviewerName: string;
  reviewerPhotoUrl: string | null;
  roomTitle: string;
  createdAt: string;
}

export interface FeedbackSummary {
  count: number;
  page: number;
  pageSize: number;
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

export const fetchFeedback = (token: string, page = 1) =>
  apiRequest<FeedbackSummary>(`/profiles/me/feedback?page=${page}`, { token });

export const fetchPendingReviews = (token: string) => apiRequest<PendingReview[]>('/profiles/me/pending-reviews', { token });
