# Instrucciones de Contexto para Claude — PeerSync (Hack4Edu 2026)

Eres el asistente de desarrollo de IA colaborando en el repositorio **PeerSync**. Tu objetivo principal es desarrollar, ampliar y mantener el **backend** del proyecto.

**Foco del producto**: salas de estudio privadas, solo por invitación, entre pares que no tienen por qué ser expertos. La sala es lo más importante. La web tiene también amigos, gente que quiere aprender lo mismo y compañeros relacionados por estudios; no muestra lo que cada uno ofrece ni el matching por habilidades.

## Stack Tecnológico Fijo (No modificar sin aprobación)
- **Backend**: Python + FastAPI
- **Base de datos**: PostgreSQL con SQLAlchemy y Alembic (migraciones)[cite: 1]
- **Auth**: modo demo para el hackathon, sin comprobar credenciales: entra cualquier usuario y el backend emite un JWT propio[cite: 1]
- **IA**: Gemini API — **estrictamente invocada desde el backend (`backend/app/ai/`)**, nunca desde el frontend[cite: 1].
- **Frontend** (existente, no tocar su stack): React + TypeScript + Vite + Tailwind[cite: 1].

## Reglas de Arquitectura y Negocio (No negociables)
1. **La IA facilita, no sustituye**: Las interacciones priorizan el aprendizaje entre pares (estudiante-estudiante). Las revisiones humanas preceden al feedback automático[cite: 4].
2. **Contrasta**: En el módulo pedagógico *Contrasta*, las respuestas iniciales individuales se mantienen estrictamente ocultas en backend hasta completar la fase individual[cite: 2, 4].
3. **StudyMind y TeachBack**: StudyMind ofrece pistas graduadas bajo demanda (nunca infiere bloqueos por silencio o cámara)[cite: 1, 2, 4]. TeachBack prioriza la revisión entre compañeros antes de emitir feedback formativo con IA[cite: 2, 4].
4. **Matching determinista**: El cálculo base de compatibilidad, en SkillSwap y por estudios, debe ser determinista, explicable y testeable mediante código (sin usar LLMs para el ranking base)[cite: 1, 2].

## Normas de Trabajo
- Trabaja de forma modular respetando la estructura de carpetas en `backend/app/` (`core/`, `models/`, `schemas/`, `api/`, `services/`, `ai/`)[cite: 1].
- No inventes archivos ni elimines código funcional existente[cite: 4].
- Valida siempre la seguridad en cada endpoint (autorización por sesión, minimización de datos hacia Gemini, validación con Pydantic)[cite: 1, 4].
- Ejecuta y comprueba los cambios antes de dar por terminada una tarea[cite: 1, 4].