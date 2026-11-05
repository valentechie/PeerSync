import React, { useEffect, useState } from 'react';
import { Download, FileText } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { fetchAttachment, type RoomAttachment } from '../services/rooms';

const formatSize = (bytes: number) =>
  bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;

/** Los archivos exigen el token, así que se descargan aquí en lugar de usar su URL directa. */
export const AttachmentView: React.FC<{ roomId: string; attachment: RoomAttachment }> = ({ roomId, attachment }) => {
  const { token } = useAuth();
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    let created: string | null = null;
    fetchAttachment(token, roomId, attachment.id)
      .then(blob => {
        if (cancelled) return;
        created = URL.createObjectURL(blob);
        setUrl(created);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
      if (created) URL.revokeObjectURL(created);
    };
  }, [token, roomId, attachment.id]);

  if (failed) return <p className="text-sm text-muted">Couldn't load {attachment.fileName}.</p>;
  if (!url) return <p role="status" className="text-sm text-muted">Loading {attachment.fileName}...</p>;

  const { contentType, fileName } = attachment;
  if (contentType.startsWith('image/')) {
    return (
      <a href={url} download={fileName} title={`Download ${fileName}`} className="inline-block max-w-full">
        <img src={url} alt={fileName} className="rounded-2xl max-h-72 max-w-full object-contain" />
      </a>
    );
  }
  if (contentType.startsWith('video/')) {
    return <video src={url} controls preload="metadata" aria-label={fileName} className="rounded-2xl max-h-72 max-w-full" />;
  }
  if (contentType.startsWith('audio/')) {
    return <audio src={url} controls preload="metadata" aria-label={fileName} className="max-w-full" />;
  }
  return (
    <a href={url} download={fileName} className="inline-flex items-center gap-3 rounded-2xl border border-line px-4 py-3 text-left max-w-full hover:border-teach transition-colors">
      <FileText className="w-6 h-6 text-teach shrink-0" aria-hidden="true" />
      <span className="min-w-0">
        <span className="block text-sm font-bold truncate">{fileName}</span>
        <span className="block text-xs text-muted">PDF · {formatSize(attachment.size)}</span>
      </span>
      <Download className="w-4 h-4 text-muted shrink-0" aria-hidden="true" />
    </a>
  );
};
