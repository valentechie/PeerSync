import { apiRequest } from './api';
import type { FriendStatus } from './people';

export type Strength = 'strong' | 'good' | 'possible';

export interface GraphNode {
  id: string;
  name: string;
  study: string | null;
  photoUrl: string | null;
  friendStatus: FriendStatus;
  score: number;
  strength: Strength;
  reasons: string[];
  rooms: { id: string; title: string }[];
}

export interface GraphLink {
  source: string;
  target: string;
  weight: number;
  reasons: string[];
}

export interface ConnectionGraph {
  me: { id: string; name: string; photoUrl: string | null };
  nodes: GraphNode[];
  links: GraphLink[];
}

export const fetchFriendsGraph = (token: string) => apiRequest<ConnectionGraph>('/connections/friends', { token });

export const fetchSuggestionsGraph = (token: string) => apiRequest<ConnectionGraph>('/connections/suggestions', { token });
