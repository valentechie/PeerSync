---
name: backend-api
description: Use when building, extending or reviewing the hack4edu/PeerSync backend — FastAPI endpoints, SQLAlchemy models, Pydantic schemas, services, auth, or anything under backend/app/. Also use when wiring the Gemini-powered AI features (SkillSwap matching, StudyMind, TeachBack).
---

# Backend & API — PeerSync (Hack4Edu 2026)

Guía para construir el backend de PeerSync: una app de intercambio de
habilidades entre estudiantes con tres motores de IA (SkillSwap AI,
StudyMind AI, TeachBack AI).

## Stack fijo

- **Backend**: Python + FastAPI
- **Base de datos**: PostgreSQL (SQLAlchemy + Alembic para migraciones)
- **Auth**: Google SSO como único acceso (ID token verificado en backend) + JWT propio
- **IA**: Gemini API — **solo invocada desde el backend, nunca desde el frontend**
- **Tiempo real**: WebSockets cuando la sala de estudio lo requiera
- **Frontend** (ya existe, no tocar su stack): React + TypeScript + Vite + Tailwind

No cambies el stack sin justificarlo explícitamente y pedir aprobación antes de hacerlo.

## Estructura de carpetas a respetar

El repo ya trae el esqueleto (`backend/app/`) con estas capas separadas —
rellena cada archivo en su capa, no mezcles responsabilidades:

```
app/
  main.py              # arranque de FastAPI, monta el router
  core/
    config.py           # settings (env vars) vía pydantic-settings
    database.py          # engine + sesión SQLAlchemy
    security.py          # hashing, JWT, dependencias de auth
  models/                # SQLAlchemy ORM (user, profile, skill, match, session, message)
  schemas/               # Pydantic request/response (user, profile, matching, session, ai)
  api/
    router.py             # agrega todos los endpoints
    endpoints/             # un archivo por recurso (auth, users, profiles, matching, sessions, messages, progress, ai)
  services/               # lógica de negocio, llamada desde los endpoints
  ai/
    skillswap/matcher.py    # matching determinista
    studymind/               # hint_generator.py, blocker_detector.py
    teachback/                # evaluator.py, feedback_generator.py
    llm_client.py              # único punto de contacto con Gemini
```

## Orden de prioridad del MVP

Construye en este orden, un flujo completo de extremo a extremo antes de
pulir nada:

1. Registro / login (auth)
2. Perfil de usuario (skills que ofrece / busca)
3. Matching (SkillSwap AI)
4. Solicitud y aceptación de match
5. Sala de estudio (sesión)
6. StudyMind (pistas bajo demanda)
7. TeachBack (feedback formativo)
8. Resumen de sesión / progreso

## Reglas de las IA (no negociables)

- **SkillSwap / matching inicial**: determinista, explicable y testeable.
  Nunca uses un LLM para decidir el ranking base de compatibilidad —
  calcula el score con reglas claras (solapamiento de skills ofrecidas
  vs. buscadas, reputación, etc.) para que sea reproducible y testeable.
- **StudyMind**: actúa solo ante petición explícita del usuario. Nunca
  infieras "bloqueo" o confusión por silencio, cámara, rostro, voz o
  señales emocionales. Da pistas progresivas antes que la solución
  completa.
- **TeachBack**: es feedback formativo, no una calificación oficial.
  Evalúa corrección, claridad, completitud y ejemplos, y expresa
  incertidumbre cuando corresponda — nunca lo presentes como una nota
  definitiva.

## Seguridad (checklist obligatorio en cada endpoint)

- Nunca expongas API keys (Gemini, Supabase, DB) en el frontend ni en
  código versionado — solo variables de entorno, con `.env.example`
  siempre sin secretos reales.
- Valida autorización en el backend para **cada** recurso privado
  (perfil, sesiones, mensajes) — no confíes en lo que mande el frontend.
- Minimiza los datos personales que se envían a Gemini (nunca mandes
  más contexto del necesario para generar la pista o el feedback).
- No registres (logs) contraseñas, tokens ni contenido sensible de las
  sesiones de estudio.
- Valida todas las entradas con Pydantic, limita longitud/frecuencia de
  requests, y maneja errores con respuestas HTTP claras (no stack
  traces crudos).
- No presentes mocks como si fueran integraciones reales — si un
  endpoint todavía no llama a la IA de verdad, dilo explícitamente en
  el código y en la respuesta (ej. campo `"mock": true`).

## Forma de trabajar

1. Antes de modificar algo, inspecciona el archivo y propone un plan
   breve si el cambio es grande.
2. Trabaja por fases siguiendo el orden de prioridad del MVP.
3. No borres archivos ajenos a la tarea actual sin justificarlo.
4. Añade tests para lógica de negocio, especialmente el matching
   determinista.
5. Ejecuta lint, typecheck y tests cuando existan antes de dar algo por
   terminado.
6. Actualiza `docs/api-documentation.md` y `docs/database-design.md`
   según vayas definiendo endpoints y tablas (están vacíos ahora mismo).
7. Al terminar cada fase, resume: archivos tocados, decisiones tomadas,
   comandos ejecutados, resultados y el siguiente paso pendiente.

## Estado actual del repo (punto de partida)

Todo `backend/app/**/*.py`, `database/schema.sql`, `backend/.env.example`
y los `docs/*.md` están vacíos — es un esqueleto sin implementar. Empieza
por `core/config.py` y `core/database.py` (conexión a Postgres), luego
`models/user.py` + `schemas/user.py` + `api/endpoints/auth.py` para tener
el primer flujo (registro/login) funcionando de punta a punta.
