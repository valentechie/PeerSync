import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../services/api';
import type { ConnectionGraph, GraphNode, Strength } from '../services/connections';
import { ErrorState, LoadingState } from './UIStates';
import { Avatar } from './Swap';
import { FriendButton } from './FriendButton';
import { ForceGraph } from './ForceGraph';
import type { ForceLink, ForceNode } from './forceGraphEngine';

const CENTER_RADIUS = 26;
const MIN_RADIUS = 13;
const RADIUS_PER_POINT = 0.11;

const STRENGTH_LABELS: Record<Strength, { label: string; chip: string }> = {
  strong: { label: 'Strong connection', chip: 'chip-teach' },
  good: { label: 'Good connection', chip: 'chip-learn' },
  possible: { label: 'Possible connection', chip: 'chip-demo' },
};

const initialOf = (name: string) => name.charAt(0).toUpperCase() || 'U';

const NodeDetails: React.FC<{
  node: GraphNode;
  tone: 'teach' | 'learn';
  showStrength: boolean;
  onClose: () => void;
  onStatusChange: (status: GraphNode['friendStatus']) => void;
  onError: (message: string) => void;
}> = ({ node, tone, showStrength, onClose, onStatusChange, onError }) => (
  <section className="card p-5 space-y-3 min-w-0" aria-live="polite" aria-label={`About ${node.name}`}>
    <div className="flex items-center gap-3 min-w-0">
      <Avatar name={node.name} photoUrl={node.photoUrl} tone={tone} className="w-12 h-12 text-xl" />
      <div className="min-w-0 flex-1">
        <h2 className="text-lg text-ink truncate">{node.name}</h2>
        {node.study && <p className="text-sm text-muted break-words">{node.study}</p>}
      </div>
      <button
        type="button"
        onClick={onClose}
        aria-label="Close details"
        title="Close details"
        className="p-2 text-muted hover:text-ink rounded-lg transition-colors cursor-pointer shrink-0"
      >
        <X className="w-4 h-4" aria-hidden="true" />
      </button>
    </div>

    {showStrength && <span className={`chip ${STRENGTH_LABELS[node.strength].chip}`}>{STRENGTH_LABELS[node.strength].label}</span>}

    {node.reasons.length > 0 ? (
      <ul className="list-disc pl-5 text-sm space-y-1">
        {node.reasons.map(reason => <li key={reason} className="break-words">{reason}</li>)}
      </ul>
    ) : (
      <p className="text-sm text-muted">You don't have studies, topics or rooms in common yet.</p>
    )}

    {node.rooms.length > 0 && (
      <ul className="space-y-1.5">
        {node.rooms.map(room => (
          <li key={room.id}>
            <Link to={`/rooms/${room.id}`} className="text-sm font-bold text-teach-strong hover:underline underline-offset-2 inline-flex items-center gap-1.5 max-w-full">
              <span className="truncate">Open {room.title}</span>
              <ArrowRight className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
            </Link>
          </li>
        ))}
      </ul>
    )}

    <FriendButton personId={node.id} status={node.friendStatus} onChange={onStatusChange} onError={onError} />
  </section>
);

/** Pantalla común de los dos grafos: el lienzo, la ficha de la persona y la lista accesible. */
export const ConnectionGraphView: React.FC<{
  title: string;
  subtitle: string;
  graphLabel: string;
  listTitle: string;
  legend: string;
  tone: 'teach' | 'learn';
  showStrength: boolean;
  fetchGraph: (token: string) => Promise<ConnectionGraph>;
  loadingMessage: string;
  renderEmpty: () => React.ReactNode;
}> = ({ title, subtitle, graphLabel, listTitle, legend, tone, showStrength, fetchGraph, loadingMessage, renderEmpty }) => {
  const { token } = useAuth();
  const [graph, setGraph] = useState<ConnectionGraph | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');

  const load = useCallback(() => {
    if (!token) return;
    fetchGraph(token)
      .then(data => {
        setGraph(data);
        setError('');
      })
      .catch((err: unknown) => setError(errorMessage(err)));
  }, [token, fetchGraph]);

  useEffect(load, [load]);

  const forceNodes = useMemo<ForceNode[]>(() => {
    if (!graph) return [];
    return [
      { id: graph.me.id, label: 'You', initial: initialOf(graph.me.name), photoUrl: graph.me.photoUrl, radius: CENTER_RADIUS, tone: 'center' },
      ...graph.nodes.map(node => ({
        id: node.id,
        label: node.name,
        initial: initialOf(node.name),
        photoUrl: node.photoUrl,
        radius: MIN_RADIUS + node.score * RADIUS_PER_POINT,
        tone,
        ring: node.friendStatus === 'sent' || node.friendStatus === 'received',
      })),
    ];
  }, [graph, tone]);

  const forceLinks = useMemo<ForceLink[]>(
    () => graph?.links.map(({ source, target, weight }) => ({ source, target, weight })) ?? [],
    [graph],
  );

  const selected = graph?.nodes.find(node => node.id === selectedId) ?? null;

  const changeStatus = (id: string, friendStatus: GraphNode['friendStatus']) =>
    setGraph(current =>
      current && { ...current, nodes: current.nodes.map(node => (node.id === id ? { ...node, friendStatus } : node)) },
    );

  return (
    <div className="page max-w-7xl space-y-6">
      <div>
        <h1 className="page-title">{title}</h1>
        <p className="page-subtitle">{subtitle}</p>
      </div>

      {error && <ErrorState message={error} onRetry={load} />}
      {actionError && <ErrorState message={actionError} />}
      {!graph && !error && <LoadingState message={loadingMessage} />}
      {graph && graph.nodes.length === 0 && renderEmpty()}

      {graph && graph.nodes.length > 0 && (
        <div className="grid lg:grid-cols-[minmax(0,1fr)_22rem] gap-4 items-start">
          <div className="space-y-2 min-w-0">
            <div className="h-[62vh] min-h-96 max-h-[46rem] rounded-3xl border border-line bg-surface/60 overflow-hidden">
              <ForceGraph
                nodes={forceNodes}
                links={forceLinks}
                selectedId={selectedId}
                onSelect={setSelectedId}
                label={`${graphLabel}: you and ${graph.nodes.length} ${graph.nodes.length === 1 ? 'person' : 'people'}. The same people are listed in this page.`}
              />
            </div>
            <p className="text-xs text-muted">{legend} Drag a person to move them, or scroll and pinch to zoom.</p>
          </div>

          <div className="space-y-4 min-w-0">
            {selected && (
              <NodeDetails
                node={selected}
                tone={tone}
                showStrength={showStrength}
                onClose={() => setSelectedId(null)}
                onError={setActionError}
                onStatusChange={friendStatus => changeStatus(selected.id, friendStatus)}
              />
            )}

            <section className="card p-5 space-y-2 min-w-0" aria-labelledby="graph-people">
              <h2 id="graph-people" className="text-lg text-ink">{listTitle} ({graph.nodes.length})</h2>
              <ul className="divide-y divide-line max-h-96 overflow-y-auto -mx-2">
                {graph.nodes.map(node => (
                  <li key={node.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedId(node.id)}
                      aria-pressed={node.id === selectedId}
                      className={`w-full flex items-center gap-3 px-2 py-2.5 rounded-xl text-left cursor-pointer min-w-0 transition-colors ${node.id === selectedId ? 'bg-teach-soft' : 'hover:bg-paper'}`}
                    >
                      <Avatar name={node.name} photoUrl={node.photoUrl} tone={tone} className="w-9 h-9 text-sm" />
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm font-bold truncate">{node.name}</span>
                        <span className="block text-xs text-muted truncate">{node.reasons[0] ?? 'Nothing in common yet'}</span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </div>
      )}
    </div>
  );
};
