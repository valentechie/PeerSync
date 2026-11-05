import React, { useEffect, useRef } from 'react';
import { Maximize, ZoomIn, ZoomOut } from 'lucide-react';
import { createGraphEngine, type ForceLink, type ForceNode, type GraphEngine } from './forceGraphEngine';

/**
 * Grafo interactivo con físicas. El lienzo no es accesible por sí solo: la página
 * debe ofrecer también la lista de personas.
 */
export const ForceGraph: React.FC<{
  nodes: ForceNode[];
  links: ForceLink[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  label: string;
}> = ({ nodes, links, selectedId, onSelect, label }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const engineRef = useRef<GraphEngine | null>(null);
  const latest = useRef({ nodes, selectedId, onSelect });

  useEffect(() => {
    latest.current = { nodes, selectedId, onSelect };
    engineRef.current?.redraw();
  });

  // Solo se rehace si cambian los nodos o las líneas: seleccionar a alguien no reinicia las físicas.
  const structure = JSON.stringify([nodes.map(node => [node.id, node.radius]), links]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext('2d');
    if (!canvas || !context) return;
    const parsedLinks = (JSON.parse(structure) as [unknown, ForceLink[]])[1];
    const engine = createGraphEngine(
      canvas,
      context,
      parsedLinks,
      () => latest.current.nodes,
      () => latest.current.selectedId,
      id => latest.current.onSelect(id),
    );
    engineRef.current = engine;
    return () => {
      engine.destroy();
      engineRef.current = null;
    };
  }, [structure]);

  const controlClass =
    'p-2 rounded-lg bg-surface/90 border border-line text-muted hover:text-ink transition-colors cursor-pointer';

  return (
    <div className="relative h-full w-full">
      <canvas
        ref={canvasRef}
        role="img"
        aria-label={label}
        data-testid="force-graph"
        className="block h-full w-full touch-none cursor-grab"
      />
      <div className="absolute top-3 right-3 flex flex-col gap-1.5">
        <button type="button" onClick={() => engineRef.current?.zoomBy(1.25)} aria-label="Zoom in" title="Zoom in" className={controlClass}>
          <ZoomIn className="w-4 h-4" aria-hidden="true" />
        </button>
        <button type="button" onClick={() => engineRef.current?.zoomBy(0.8)} aria-label="Zoom out" title="Zoom out" className={controlClass}>
          <ZoomOut className="w-4 h-4" aria-hidden="true" />
        </button>
        <button type="button" onClick={() => engineRef.current?.fit()} aria-label="Fit the whole graph" title="Fit the whole graph" className={controlClass}>
          <Maximize className="w-4 h-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
};
