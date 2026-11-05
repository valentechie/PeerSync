import React from 'react';

const YOUTUBE_URL = /(?:https?:\/\/)?(?:www\.|m\.)?(?:youtube\.com\/(?:watch\?(?:[^\s]*&)?v=|shorts\/|embed\/)|youtu\.be\/)([\w-]{11})(?![\w-])/;

export const findYouTubeId = (text: string): string | null => text.match(YOUTUBE_URL)?.[1] ?? null;

export const YouTubeEmbed: React.FC<{ videoId: string }> = ({ videoId }) => (
  <iframe
    src={`https://www.youtube-nocookie.com/embed/${videoId}`}
    title="YouTube video"
    loading="lazy"
    sandbox="allow-scripts allow-same-origin allow-presentation allow-popups"
    allow="encrypted-media; picture-in-picture; fullscreen"
    referrerPolicy="strict-origin-when-cross-origin"
    className="w-full max-w-md aspect-video rounded-2xl border border-line"
  />
);
