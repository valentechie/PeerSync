/**
 * Simulación física del grafo, sin dependencias ni acceso al DOM.
 *
 * Cada nodo tiene masa, posición y velocidad. Las fuerzas son simétricas (acción y
 * reacción): repulsión entre nodos, muelles en las líneas, gravedad hacia el centro
 * y rozamiento. Se integra con paso fijo, así que el resultado no depende de los
 * fotogramas por segundo del dispositivo.
 */

export const STEP_SECONDS = 1 / 60;

const REPULSION = 2_400_000;
const MIN_DISTANCE_SQUARED = 400;
const SPRING_STIFFNESS = 5;
const COLLISION_STIFFNESS = 40;
const COLLISION_PADDING = 14;
const GRAVITY = 1;
const CENTER_GRAVITY = 5;
const DAMPING_PER_SECOND = 2.6;
// Rozamiento estático: lo que va despacio se frena mucho más, y el grafo acaba parándose.
const SLOW_SPEED = 40;
const SLOW_DAMPING_PER_SECOND = 14;
const MAX_SPEED = 1400;
const SHORTEST_SPRING = 110;
const LONGEST_SPRING = 300;
const REST_SPEED = 5;

export interface BodyInput {
  id: string;
  radius: number;
  isCenter?: boolean;
}

export interface SpringInput {
  source: string;
  target: string;
  /** De 0 a 1. Cuanto más fuerte, más corto es el muelle y más cerca quedan los nodos. */
  weight: number;
}

export interface Body extends BodyInput {
  x: number;
  y: number;
  vx: number;
  vy: number;
  mass: number;
  /** Mientras alguien lo arrastra, lo mueve la mano y no las fuerzas. */
  held: boolean;
}

export interface Spring {
  a: Body;
  b: Body;
  rest: number;
  stiffness: number;
}

export interface Simulation {
  bodies: Body[];
  springs: Spring[];
}

const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

export function createSimulation(inputs: BodyInput[], links: SpringInput[]): Simulation {
  // Espiral fija: ningún nodo nace encima de otro y la colocación es reproducible.
  const bodies: Body[] = inputs.map((input, index) => {
    const distance = input.isCenter ? 0 : 26 * Math.sqrt(index + 1);
    return {
      ...input,
      x: Math.cos(index * GOLDEN_ANGLE) * distance,
      y: Math.sin(index * GOLDEN_ANGLE) * distance,
      vx: 0,
      vy: 0,
      mass: input.radius / 12,
      held: false,
    };
  });
  const byId = new Map(bodies.map(body => [body.id, body]));
  const springs: Spring[] = [];
  for (const link of links) {
    const a = byId.get(link.source);
    const b = byId.get(link.target);
    if (!a || !b || a === b) continue;
    const weight = Math.min(1, Math.max(0, link.weight));
    const touchesCenter = a.isCenter || b.isCenter;
    springs.push({
      a,
      b,
      rest: LONGEST_SPRING - (LONGEST_SPRING - SHORTEST_SPRING) * weight,
      // Las líneas con la persona central mandan; las demás solo agrupan.
      stiffness: SPRING_STIFFNESS * (touchesCenter ? 1 : 0.25 + weight * 0.5),
    });
  }
  return { bodies, springs };
}

function push(a: Body, b: Body, fx: number, fy: number, dt: number) {
  a.vx -= (fx / a.mass) * dt;
  a.vy -= (fy / a.mass) * dt;
  b.vx += (fx / b.mass) * dt;
  b.vy += (fy / b.mass) * dt;
}

export function step(simulation: Simulation, dt = STEP_SECONDS): void {
  const { bodies, springs } = simulation;

  for (let i = 0; i < bodies.length; i += 1) {
    const a = bodies[i];
    for (let j = i + 1; j < bodies.length; j += 1) {
      const b = bodies[j];
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const squared = Math.max(dx * dx + dy * dy, MIN_DISTANCE_SQUARED);
      const distance = Math.sqrt(squared);
      let force = REPULSION / squared;
      const overlap = a.radius + b.radius + COLLISION_PADDING - distance;
      if (overlap > 0) force += COLLISION_STIFFNESS * overlap;
      push(a, b, (force * dx) / distance, (force * dy) / distance, dt);
    }
  }

  for (const { a, b, rest, stiffness } of springs) {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const distance = Math.max(Math.hypot(dx, dy), 1);
    const force = stiffness * (distance - rest);
    push(a, b, (-force * dx) / distance, (-force * dy) / distance, dt);
  }

  const friction = Math.exp(-DAMPING_PER_SECOND * dt);
  const slowFriction = Math.exp(-SLOW_DAMPING_PER_SECOND * dt);
  for (const body of bodies) {
    if (body.held) {
      body.vx = 0;
      body.vy = 0;
      continue;
    }
    const gravity = body.isCenter ? CENTER_GRAVITY : GRAVITY;
    body.vx -= gravity * body.x * dt;
    body.vy -= gravity * body.y * dt;
    const drag = Math.hypot(body.vx, body.vy) < SLOW_SPEED ? slowFriction : friction;
    body.vx *= drag;
    body.vy *= drag;
    const speed = Math.hypot(body.vx, body.vy);
    if (speed > MAX_SPEED) {
      body.vx *= MAX_SPEED / speed;
      body.vy *= MAX_SPEED / speed;
    }
    body.x += body.vx * dt;
    body.y += body.vy * dt;
  }
}

/** Cierto si todos los nodos están prácticamente quietos y se puede dejar de calcular. */
export function isAtRest(simulation: Simulation): boolean {
  return simulation.bodies.every(body => body.held || Math.hypot(body.vx, body.vy) < REST_SPEED);
}
