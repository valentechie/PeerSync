import { apiRequest } from './api';
import type { RevealedAnswer } from './contrasta';
import type { TeachBackFeedback } from './teachback';

export interface Person {
  id: string;
  name: string;
}

export type ReactionKind = 'agree' | 'doubt' | 'convince';

export type ActionKey = 'start' | 'hint' | 'idea' | 'practice' | 'conclusion';

export interface FlowAction {
  key: ActionKey;
  enabled: boolean;
  reason: string | null;
}

export interface FlowRound {
  id: string;
  prompt: string;
  status: 'individual' | 'revealed';
  createdAt: string;
  revealedAt: string | null;
  finishedAt: string | null;
  partner: Person;
  partnerPresent: boolean;
  iHaveAnswered: boolean;
  partnerHasAnswered: boolean;
  myAnswer: string | null;
  answers: RevealedAnswer[];
  conclusion: { text: string; by: Person; at: string; confirmedAt: string | null } | null;
  finishRequestedByMe: boolean;
  finishRequestedByPartner: boolean;
  myPrediction: string | null;
  predictions: { person: Person; text: string }[];
  reactions: { person: Person; kind: ReactionKind }[];
}

export interface Comparison {
  status: 'pending' | 'ready' | 'failed';
  requestedByName: string;
  updatedAt: string;
  result: {
    agreements: string[];
    differences: string[];
    questions: string[];
    claimsToVerify: string[];
    uncertaintyNote: string;
  } | null;
}

export interface HelpCard {
  id: string;
  kind: 'hint' | 'idea';
  author: Person;
  request: string;
  result: { message: string; suggestedAction: string; uncertaintyNote: string };
  private: boolean;
  createdAt: string;
}

export interface ActivityTurn {
  turn: number;
  explainer: Person;
  explanation: string;
  createdAt: string;
  review: { reviewer: Person; comment: string; createdAt: string } | null;
  feedback: TeachBackFeedback | null;
}

export interface Activity {
  id: string;
  concept: string;
  status: 'pending' | 'declined' | 'cancelled' | 'active' | 'completed' | 'stopped';
  proposer: Person;
  partner: Person;
  turn: number;
  createdAt: string;
  updatedAt: string;
  skipRequestedByMe: boolean;
  skipRequestedByPartner: boolean;
  turns: ActivityTurn[];
}

export interface Check {
  question: string;
  source: 'ai' | 'peer';
  createdAt: string;
  iHaveAnswered: boolean;
  partnerHasAnswered: boolean;
  answers: { person: Person; answer: string; reflection: string }[];
}

export interface Voice {
  key: string;
  at: string;
  kind: 'info' | 'prediction' | 'debate';
  text: string;
}

export interface Flow {
  round: FlowRound | null;
  otherPairInProgress: boolean;
  comparison: Comparison | null;
  cards: HelpCard[];
  activities: Activity[];
  check: Check | null;
  suggestion: { key: 'teachback' | 'check'; at: string } | null;
  step: { number: number; label: string } | null;
  actions: FlowAction[];
  voice: Voice[];
  move: { mine: boolean; text: string; target: string | null } | null;
  welcome: { key: string; text: string } | null;
}

const base = (roomId: string) => `/rooms/${encodeURIComponent(roomId)}/contrasta`;
const activity = (roomId: string, activityId: string) => `${base(roomId)}/activities/${encodeURIComponent(activityId)}`;
const post = (token: string, path: string, body?: unknown) => apiRequest<Flow>(path, { method: 'POST', body, token });

export const fetchFlow = (token: string, roomId: string) => apiRequest<Flow>(`${base(roomId)}/flow`, { token });

export const startPairRound = (token: string, roomId: string, prompt: string, partnerId: string) =>
  apiRequest<unknown>(`${base(roomId)}/rounds`, { method: 'POST', body: { prompt, partnerId }, token });

export const answerRound = (token: string, roomId: string, answer: string) =>
  apiRequest<unknown>(`${base(roomId)}/answers`, { method: 'POST', body: { answer }, token });

export const savePrediction = (token: string, roomId: string, text: string) =>
  post(token, `${base(roomId)}/prediction`, { text });
export const react = (token: string, roomId: string, kind: ReactionKind) =>
  post(token, `${base(roomId)}/reaction`, { kind });
export const cancelRound = (token: string, roomId: string) => post(token, `${base(roomId)}/round/cancel`);
export const finishRound = (token: string, roomId: string) => post(token, `${base(roomId)}/round/finish`);
export const requestComparison = (token: string, roomId: string) => post(token, `${base(roomId)}/comparison`);
export const requestHelp = (token: string, roomId: string, kind: 'hint' | 'idea', text: string) =>
  post(token, `${base(roomId)}/help`, { kind, text });
export const recordConclusion = (token: string, roomId: string, text: string) =>
  post(token, `${base(roomId)}/conclusion`, { text });
export const confirmConclusion = (token: string, roomId: string) => post(token, `${base(roomId)}/conclusion/confirm`);
export const proposeActivity = (token: string, roomId: string, concept: string) =>
  post(token, `${base(roomId)}/activities`, { concept });
export const respondToActivity = (token: string, roomId: string, id: string, decision: 'accept' | 'decline' | 'cancel') =>
  post(token, `${activity(roomId, id)}/respond/${decision}`);
export const submitExplanation = (token: string, roomId: string, id: string, explanation: string) =>
  post(token, `${activity(roomId, id)}/explanation`, { explanation });
export const submitReview = (token: string, roomId: string, id: string, comment: string) =>
  post(token, `${activity(roomId, id)}/review`, { comment });
export const requestActivityFeedback = (token: string, roomId: string, id: string, turn: number) =>
  post(token, `${activity(roomId, id)}/feedback`, { turn });
export const advanceActivity = (token: string, roomId: string, id: string) => post(token, `${activity(roomId, id)}/advance`);
export const skipSecondTurn = (token: string, roomId: string, id: string) => post(token, `${activity(roomId, id)}/skip`);
export const leaveActivity = (token: string, roomId: string, id: string) => post(token, `${activity(roomId, id)}/leave`);
export const createCheck = (token: string, roomId: string, question?: string) =>
  post(token, `${base(roomId)}/check`, question ? { question } : {});
export const answerCheck = (token: string, roomId: string, answer: string, reflection: string) =>
  post(token, `${base(roomId)}/check/answer`, { answer, reflection });
