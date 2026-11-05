import { apiRequest } from './api';

export interface TeachBackSubmission {
  id: string;
  explainerId: string;
  explainerName: string;
  concept: string;
  explanation: string;
  createdAt: string;
  review: { reviewerId: string; reviewerName: string; comment: string; createdAt: string } | null;
}

export interface TeachBackFeedback {
  strengths: string[];
  possibleGaps: string[];
  questionsForPeer: string[];
  evidenceToCheck: string[];
  suggestedPeerActivity: string;
  uncertaintyNote: string;
}

const base = (roomId: string) => `/rooms/${encodeURIComponent(roomId)}/teachback`;

export const fetchSubmissions = (token: string, roomId: string) =>
  apiRequest<TeachBackSubmission[]>(base(roomId), { token });

export const createSubmission = (token: string, roomId: string, concept: string, explanation: string) =>
  apiRequest<TeachBackSubmission>(base(roomId), { method: 'POST', body: { concept, explanation }, token });

export const createPeerReview = (token: string, roomId: string, submissionId: string, comment: string) =>
  apiRequest<TeachBackSubmission>(`${base(roomId)}/${encodeURIComponent(submissionId)}/review`, {
    method: 'POST',
    body: { comment },
    token,
  });

export const requestFeedback = (token: string, roomId: string, submissionId: string) =>
  apiRequest<TeachBackFeedback>(`${base(roomId)}/${encodeURIComponent(submissionId)}/ai-feedback`, { method: 'POST', token });
