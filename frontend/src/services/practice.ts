import { apiRequest } from './api';

export interface PracticeTurn {
  role: 'coach' | 'student';
  content: string;
}

export const fetchNextQuestion = (token: string, topic: string, history: PracticeTurn[]) =>
  apiRequest<{ question: string }>('/practice/next', { method: 'POST', body: { topic, history }, token });
