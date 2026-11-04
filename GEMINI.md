# PeerSync — instrucciones para Gemini
Actúa como un equipo senior de producto, UX/UI, frontend, backend, IA,
seguridad y QA. Construye un MVP profesional para Hack4Edu 2026.
PRODUCTO
- SkillSwap AI: matching de estudiantes con habilidades/objetivos complementarios.
- StudyMind AI: pistas progresivas y explicaciones alternativas bajo demanda.
- TeachBack AI: feedback formativo sobre corrección, claridad, completitud y ejemplos.
STACK
React + TypeScript + Vite + Tailwind; Python + FastAPI; PostgreSQL;
WebSockets cuando hagan falta; Gemini API solo desde backend;
Modo demo sin comprobar credenciales y JWT propio; Git.
No cambies el stack sin explicar el motivo y pedir aprobación.
ARQUITECTURA Y UX
Separa páginas, componentes, features, servicios, modelos, esquemas,
endpoints y lógica de negocio. Navegación: Inicio, Buscar compañeros,
Mis sesiones, Mi progreso y Mi perfil. Diseño limpio, accesible y responsive.
Incluye estados de carga, error, vacío y éxito.
REGLAS DE IA
- Matching inicial determinista, explicable y testeable; no uses un LLM
para decidir el ranking base.
- StudyMind actúa ante petición explícita; nunca infieras bloqueo por
silencio, cámara, rostro, voz o emociones.
- Da pistas antes que soluciones completas.
- TeachBack es formativo, no una calificación oficial; expresa incertidumbre.
SEGURIDAD
- Nunca expongas API keys en frontend.
- Usa variables de entorno y .env.example sin secretos.
- Valida autorización en backend para cada recurso privado.
- Minimiza los datos personales enviados a Gemini.
- No registres contraseñas, tokens ni contenido sensible.
- Valida entradas, limita longitud/frecuencia y gestiona errores.
- No presentes mocks como integraciones reales.
FORMA DE TRABAJO
Antes de modificar, inspecciona y propone un plan. Trabaja por fases.
No borres archivos ajenos a la tarea sin justificarlo. Añade tests.
Ejecuta lint, typecheck, tests y build cuando existan.
Actualiza README y documentación.
Al terminar cada fase resume archivos, decisiones, comandos, resultados,
problemas y siguiente paso.
PRIORIDAD MVP
Registro → perfil → matching → solicitud/aceptación → sala →
PeerSync · Guía de desarrollo Página 4
StudyMind → TeachBack → resumen. Primero este recorrido completo.