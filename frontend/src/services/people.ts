import { apiRequest } from './api';

export type FriendStatus = 'friend' | 'sent' | 'received' | null;

export interface Person {
  id: string;
  name: string;
  bio: string;
  study: string | null;
  sharedInterests: string[];
  friendStatus: FriendStatus;
}

export interface StudyMatch extends Person {
  matchType: 'direct' | 'similar';
  matchReason: string;
}

export interface StudyFamily {
  name: string;
  studies: { code: string; label: string }[];
}

export interface Friend extends Person {
  rooms: { id: string; title: string }[];
}

export interface FriendsOverview {
  friends: Friend[];
  received: Person[];
  sent: Person[];
}

export const fetchFriends = (token: string) => apiRequest<FriendsOverview>('/friends', { token });

export const addFriend = (token: string, id: string) =>
  apiRequest<Person>(`/friends/${encodeURIComponent(id)}`, { method: 'POST', token });

export const acceptFriend = (token: string, id: string) =>
  apiRequest<Person>(`/friends/${encodeURIComponent(id)}/accept`, { method: 'POST', token });

export const removeFriend = (token: string, id: string) =>
  apiRequest<void>(`/friends/${encodeURIComponent(id)}`, { method: 'DELETE', token });

export const searchPeople = (token: string, search: string) =>
  apiRequest<Person[]>(`/people?search=${encodeURIComponent(search)}`, { token });

export const fetchSameInterests = (token: string) => apiRequest<Person[]>('/people/same-interests', { token });

export const fetchStudyMatches = (token: string) => apiRequest<StudyMatch[]>('/people/study-matches', { token });

export const fetchStudies = (token: string) => apiRequest<StudyFamily[]>('/studies', { token });
