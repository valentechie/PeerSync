import { apiRequest } from './api';

export const MAX_HELP_STEP = 6;

export interface StudyMindHelp {
  source: 'ai' | 'fallback';
  step: number;
  message: string;
  suggestedAction: string;
  uncertaintyNote: string;
}

export const requestHelp = (token: string, roomId: string, difficulty: string, step: number) =>
  apiRequest<StudyMindHelp>(`/rooms/${encodeURIComponent(roomId)}/ai/studymind`, {
    method: 'POST',
    body: { difficulty, step },
    token,
  });
