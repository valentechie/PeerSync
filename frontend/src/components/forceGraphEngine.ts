import { apiAssetUrl } from '../services/api';
import { STEP_SECONDS, createSimulation, isAtRest, step, type Body, type Simulation } from './forceSimulation';

export type NodeTone = 'center' | 'teach' | 'learn';

export interface ForceNode {
  id: string;
  label: string;
  /** Letra del círculo si no hay foto. */
  initial: string;
  photoUrl: string | null;
  radius: number;
  tone: NodeTone;
  /** Dibuja un aro que marca una solicitud de amistad pendiente. */
  ring?: boolean;
}

export interface ForceLink {
  source: string;
  target: string;
  weight: number;
}

export interface GraphEngine {
  zoomBy: (factor: number) => void;
  fit: () => void;
  redraw: () => void;
  destroy: () => void;
}

const MIN_ZOOM = 0.25;
const MAX_ZOOM = 3;
const MAX_AUTO_ZOOM = 1.15;
const FIT_MARGIN = 56;
const CLICK_TOLERANCE = 5;
const MAX_STEPS_PER_FRAME = 3;
const SETTLE_STEPS_WITHOUT_MOTION = 700;
const LABEL_MAX = 18;
const TOUCH_HIT_MARGIN = 14;
const MOUSE_HIT_MARGIN = 4;
const THROW_SCALE = 0.6;

const QUIET_FRAMES_BEFORE_SLEEP = 30;

const token = (element: Element, name: string, fallback: string) =>
  getComputedStyle(element).getPropertyValue(name).trim() || fallback;

const shortLabel = (label: string) => (label.length > LABEL_MAX ? `${label.slice(0, LABEL_MAX - 1)}…` : label);

/**
 * Dibuja el grafo en el lienzo y atiende los gestos: arrastrar y lanzar un nodo, mover
 * el fondo y hacer zoom con la rueda o con dos dedos. Deja de calcular cuando todo está quieto.
 */
export function createGraphEngine(
  canvas: HTMLCanvasElement,
  context: CanvasRenderingContext2D,
  links: ForceLink[],
  getNodes: () => ForceNode[],
  getSelectedId: () => string | null,
  onSelect: (id: string | null) => void,
): GraphEngine {
  const initial = getNodes();
  const simulation: Simulation = createSimulation(
    initial.map(node => ({ id: node.id, radius: node.radius, isCenter: node.tone === 'center' })),
    links,
  );
  const bodyById = new Map(simulation.bodies.map(body => [body.id, body]));
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const colors = {
    ink: token(canvas, '--color-ink', '#f1f2ff'),
    night: token(canvas, '--color-night', '#11152d'),
    line: token(canvas, '--color-muted', '#a3aed0'),
    center: token(canvas, '--color-sun', '#fbbf24'),
    centerSoft: token(canvas, '--color-sun-soft', '#3b2f12'),
    teach: token(canvas, '--color-teach', '#a78bfa'),
    teachSoft: token(canvas, '--color-teach-soft', '#2b2560'),
    learn: token(canvas, '--color-learn', '#f472b6'),
    learnSoft: token(canvas, '--color-learn-soft', '#421f45'),
  };

  const neighbours = new Map<string, Set<string>>();
  for (const { a, b } of simulation.springs) {
    if (!neighbours.has(a.id)) neighbours.set(a.id, new Set());
    if (!neighbours.has(b.id)) neighbours.set(b.id, new Set());
    neighbours.get(a.id)?.add(b.id);
    neighbours.get(b.id)?.add(a.id);
  }

  const images = new Map<string, HTMLImageElement>();
  let width = 0;
  let height = 0;
  let camera = { x: 0, y: 0, k: 1 };
  let cameraTouched = false;
  let hoveredId: string | null = null;
  let frame = 0;
  let animating = false;
  let lastTime = 0;
  let carry = 0;
  let quietFrames = 0;

  const pointers = new Map<number, { x: number; y: number }>();
  let drag:
    | { kind: 'node'; body: Body; moved: boolean; lastX: number; lastY: number; lastT: number; vx: number; vy: number }
    | { kind: 'pan'; moved: boolean; startX: number; startY: number }
    | null = null;
  let pinchDistance = 0;

  const toWorld = (x: number, y: number) => ({
    x: (x - width / 2 - camera.x) / camera.k,
    y: (y - height / 2 - camera.y) / camera.k,
  });

  const fittedCamera = () => {
    let minX = Infinity;
    let maxX = -Infinity;
    let minY = Infinity;
    let maxY = -Infinity;
    for (const body of simulation.bodies) {
      minX = Math.min(minX, body.x - body.radius);
      maxX = Math.max(maxX, body.x + body.radius);
      minY = Math.min(minY, body.y - body.radius);
      maxY = Math.max(maxY, body.y + body.radius);
    }
    const k = Math.max(
      MIN_ZOOM,
      Math.min(
        MAX_AUTO_ZOOM,
        (width - FIT_MARGIN * 2) / Math.max(maxX - minX, 1),
        (height - FIT_MARGIN * 2) / Math.max(maxY - minY, 1),
      ),
    );
    return { x: (-(minX + maxX) / 2) * k, y: (-(minY + maxY) / 2) * k, k };
  };

  const imageFor = (url: string) => {
    let image = images.get(url);
    if (!image) {
      image = new Image();
      image.onload = () => requestDraw();
      image.src = apiAssetUrl(url);
      images.set(url, image);
    }
    return image.complete && image.naturalWidth > 0 ? image : null;
  };

  const draw = () => {
    const dpr = window.devicePixelRatio || 1;
    context.setTransform(dpr, 0, 0, dpr, 0, 0);
    context.clearRect(0, 0, width, height);
    context.translate(width / 2 + camera.x, height / 2 + camera.y);
    context.scale(camera.k, camera.k);

    const focusId = hoveredId ?? getSelectedId();
    const focusSet = focusId ? neighbours.get(focusId) : null;
    const inFocus = (id: string) => !focusId || id === focusId || Boolean(focusSet?.has(id));

    for (const { a, b, rest } of simulation.springs) {
      const active = focusId !== null && (a.id === focusId || b.id === focusId);
      context.globalAlpha = focusId ? (active ? 0.95 : 0.07) : 0.34;
      context.strokeStyle = active ? colors.ink : colors.line;
      // Los muelles cortos son vínculos fuertes: también se dibujan más gruesos.
      context.lineWidth = (0.9 + (300 - rest) / 95) / Math.max(camera.k, 0.6);
      context.beginPath();
      context.moveTo(a.x, a.y);
      context.lineTo(b.x, b.y);
      context.stroke();
    }

    const fontSize = 12 / Math.max(camera.k, 0.55);
    context.textAlign = 'center';
    context.textBaseline = 'top';
    context.font = `600 ${fontSize}px ui-sans-serif, system-ui, sans-serif`;
    context.lineJoin = 'round';

    for (const info of getNodes()) {
      const body = bodyById.get(info.id);
      if (!body) continue;
      const { x, y, radius } = body;
      const stroke = info.tone === 'center' ? colors.center : info.tone === 'teach' ? colors.teach : colors.learn;
      const soft = info.tone === 'center' ? colors.centerSoft : info.tone === 'teach' ? colors.teachSoft : colors.learnSoft;
      context.globalAlpha = inFocus(info.id) ? 1 : 0.2;

      if (info.id === focusId) {
        context.save();
        context.shadowColor = stroke;
        context.shadowBlur = 24;
        context.fillStyle = stroke;
        context.beginPath();
        context.arc(x, y, radius, 0, Math.PI * 2);
        context.fill();
        context.restore();
      }

      const image = info.photoUrl ? imageFor(info.photoUrl) : null;
      context.fillStyle = soft;
      context.beginPath();
      context.arc(x, y, radius, 0, Math.PI * 2);
      context.fill();
      if (image) {
        context.save();
        context.clip();
        context.drawImage(image, x - radius, y - radius, radius * 2, radius * 2);
        context.restore();
      } else {
        context.fillStyle = colors.ink;
        context.save();
        context.textBaseline = 'middle';
        context.font = `700 ${radius}px ui-sans-serif, system-ui, sans-serif`;
        context.fillText(info.initial, x, y + radius * 0.06);
        context.restore();
      }
      context.strokeStyle = stroke;
      context.lineWidth = 2;
      context.beginPath();
      context.arc(x, y, radius, 0, Math.PI * 2);
      context.stroke();
      if (info.ring) {
        context.strokeStyle = colors.center;
        context.setLineDash([4, 3]);
        context.beginPath();
        context.arc(x, y, radius + 5, 0, Math.PI * 2);
        context.stroke();
        context.setLineDash([]);
      }

      const text = shortLabel(info.label);
      const textY = y + radius + (info.ring ? 9 : 5);
      context.lineWidth = 3.5 / Math.max(camera.k, 0.55);
      context.strokeStyle = colors.night;
      context.strokeText(text, x, textY);
      context.fillStyle = colors.ink;
      context.fillText(text, x, textY);
    }
    context.globalAlpha = 1;
  };

  const requestDraw = () => {
    if (!frame) frame = requestAnimationFrame(tick);
  };

  const wake = () => {
    animating = !reducedMotion || Boolean(drag);
    lastTime = 0;
    quietFrames = 0;
    requestDraw();
  };

  function tick(time: number) {
    frame = 0;
    if (animating) {
      const elapsed = lastTime ? Math.min((time - lastTime) / 1000, 0.05) : STEP_SECONDS;
      lastTime = time;
      carry += elapsed;
      let steps = 0;
      while (carry >= STEP_SECONDS && steps < MAX_STEPS_PER_FRAME) {
        step(simulation);
        carry -= STEP_SECONDS;
        steps += 1;
      }
      if (steps === MAX_STEPS_PER_FRAME) carry = 0;
      // Un nodo que oscila se para un instante al cambiar de sentido: eso aún no es reposo.
      quietFrames = !drag && isAtRest(simulation) ? quietFrames + 1 : 0;
      if (quietFrames >= QUIET_FRAMES_BEFORE_SLEEP) animating = false;
    }
    if (!cameraTouched && !drag) {
      const target = fittedCamera();
      const ease = animating ? 0.08 : 1;
      camera = {
        x: camera.x + (target.x - camera.x) * ease,
        y: camera.y + (target.y - camera.y) * ease,
        k: camera.k + (target.k - camera.k) * ease,
      };
    }
    draw();
    if (animating) requestDraw();
  }

  const resize = () => {
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    const dpr = window.devicePixelRatio || 1;
    width = rect.width;
    height = rect.height;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    if (!cameraTouched) camera = fittedCamera();
    requestDraw();
  };

  const point = (event: { clientX: number; clientY: number }) => {
    const rect = canvas.getBoundingClientRect();
    return { x: event.clientX - rect.left, y: event.clientY - rect.top };
  };

  const hit = (x: number, y: number, margin: number) => {
    const world = toWorld(x, y);
    let found: Body | null = null;
    let best = Infinity;
    for (const body of simulation.bodies) {
      const distance = Math.hypot(body.x - world.x, body.y - world.y);
      if (distance <= body.radius + margin / camera.k && distance < best) {
        best = distance;
        found = body;
      }
    }
    return found;
  };

  const zoomAt = (x: number, y: number, factor: number) => {
    const k = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, camera.k * factor));
    const world = toWorld(x, y);
    camera = { k, x: x - width / 2 - world.x * k, y: y - height / 2 - world.y * k };
    cameraTouched = true;
    requestDraw();
  };

  const onPointerDown = (event: PointerEvent) => {
    canvas.setPointerCapture(event.pointerId);
    const at = point(event);
    pointers.set(event.pointerId, at);
    if (pointers.size === 2) {
      // El segundo dedo convierte el gesto en zoom: se suelta lo que se estuviera moviendo.
      if (drag?.kind === 'node') drag.body.held = false;
      drag = null;
      const [first, second] = [...pointers.values()];
      pinchDistance = Math.hypot(first.x - second.x, first.y - second.y);
      return;
    }
    const margin = event.pointerType === 'mouse' ? MOUSE_HIT_MARGIN : TOUCH_HIT_MARGIN;
    const body = hit(at.x, at.y, margin);
    if (body) {
      body.held = true;
      drag = { kind: 'node', body, moved: false, lastX: at.x, lastY: at.y, lastT: event.timeStamp, vx: 0, vy: 0 };
      animating = true;
      wake();
    } else {
      drag = { kind: 'pan', moved: false, startX: at.x, startY: at.y };
    }
  };

  const onPointerMove = (event: PointerEvent) => {
    const at = point(event);
    if (pointers.has(event.pointerId)) {
      const previous = pointers.get(event.pointerId) as { x: number; y: number };
      pointers.set(event.pointerId, at);
      if (pointers.size === 2) {
        const [first, second] = [...pointers.values()];
        const distance = Math.hypot(first.x - second.x, first.y - second.y);
        if (pinchDistance > 0) zoomAt((first.x + second.x) / 2, (first.y + second.y) / 2, distance / pinchDistance);
        pinchDistance = distance;
        return;
      }
      if (drag?.kind === 'node') {
        if (Math.hypot(at.x - drag.lastX, at.y - drag.lastY) > CLICK_TOLERANCE) drag.moved = true;
        if (drag.moved) {
          const world = toWorld(at.x, at.y);
          const seconds = Math.max((event.timeStamp - drag.lastT) / 1000, 0.001);
          drag.vx = (at.x - drag.lastX) / camera.k / seconds;
          drag.vy = (at.y - drag.lastY) / camera.k / seconds;
          drag.lastX = at.x;
          drag.lastY = at.y;
          drag.lastT = event.timeStamp;
          drag.body.x = world.x;
          drag.body.y = world.y;
          wake();
        }
      } else if (drag?.kind === 'pan') {
        if (Math.hypot(at.x - drag.startX, at.y - drag.startY) > CLICK_TOLERANCE) drag.moved = true;
        if (drag.moved) {
          camera = { ...camera, x: camera.x + at.x - previous.x, y: camera.y + at.y - previous.y };
          cameraTouched = true;
          requestDraw();
        }
      }
      return;
    }
    if (event.pointerType === 'mouse') {
      const body = hit(at.x, at.y, MOUSE_HIT_MARGIN);
      const id = body?.id ?? null;
      canvas.style.cursor = body ? 'pointer' : 'grab';
      if (id !== hoveredId) {
        hoveredId = id;
        requestDraw();
      }
    }
  };

  const onPointerUp = (event: PointerEvent) => {
    pointers.delete(event.pointerId);
    pinchDistance = 0;
    const finished = drag;
    drag = null;
    if (!finished) return;
    if (finished.kind === 'node') {
      finished.body.held = false;
      if (finished.moved && !reducedMotion) {
        // Al soltarlo conserva la inercia de la mano, así que se puede lanzar.
        finished.body.vx = finished.vx * THROW_SCALE;
        finished.body.vy = finished.vy * THROW_SCALE;
      }
      if (!finished.moved) onSelect(finished.body.isCenter ? null : finished.body.id);
      wake();
    } else if (!finished.moved && event.type === 'pointerup') {
      onSelect(null);
    }
  };

  const onPointerLeave = () => {
    if (hoveredId) {
      hoveredId = null;
      requestDraw();
    }
  };

  const onWheel = (event: WheelEvent) => {
    event.preventDefault();
    const at = point(event);
    zoomAt(at.x, at.y, Math.exp(-event.deltaY * 0.0015));
  };

  canvas.addEventListener('pointerdown', onPointerDown);
  canvas.addEventListener('pointermove', onPointerMove);
  canvas.addEventListener('pointerup', onPointerUp);
  canvas.addEventListener('pointercancel', onPointerUp);
  canvas.addEventListener('pointerleave', onPointerLeave);
  canvas.addEventListener('wheel', onWheel, { passive: false });
  const observer = new ResizeObserver(resize);
  observer.observe(canvas);


  if (reducedMotion) {
    // Sin animación: se calcula el reposo de golpe y se pinta una sola vez.
    for (let index = 0; index < SETTLE_STEPS_WITHOUT_MOTION; index += 1) step(simulation);
  }
  resize();
  wake();


  return {
    zoomBy: factor => zoomAt(width / 2, height / 2, factor),
    fit: () => {
      cameraTouched = false;
      camera = fittedCamera();
      requestDraw();
    },
    redraw: requestDraw,
    destroy: () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      canvas.removeEventListener('pointerdown', onPointerDown);
      canvas.removeEventListener('pointermove', onPointerMove);
      canvas.removeEventListener('pointerup', onPointerUp);
      canvas.removeEventListener('pointercancel', onPointerUp);
      canvas.removeEventListener('pointerleave', onPointerLeave);
      canvas.removeEventListener('wheel', onWheel);
    },
  };
}
