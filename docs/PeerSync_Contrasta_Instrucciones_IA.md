# PeerSync · Encargo de implementación para IA de desarrollo

## 0. Contexto y objetivo

Trabajas en el repositorio **PeerSync**, proyecto de **Hack4Edu 2026**, reto «IA aplicada al aprendizaje entre pares».

**Objetivo:** convertir la sala de estudio existente en una experiencia unificada llamada **Contrasta**: una conversación humana continua en la que aparecen sugerencias discretas, un menú contextual y actividades de aprendizaje entre pares. **StudyMind** (ayudas y preguntas) y **TeachBack** (explicación y revisión humana) son capacidades internas integradas en Contrasta, **no pantallas ni chats independientes**.

**No estamos solicitando un rediseño ni otro chatbot educativo.** La IA debe promover que los estudiantes piensen, argumenten, comprueben y se expliquen conceptos mutuamente, no reemplazarlos.

Trabaja sobre el **estado real de la rama actual** y contrasta estas indicaciones con el código antes de tocarlo. Como referencia, el ZIP auditado era `main` en commit `ec271d8`; podría haber cambios posteriores en otras ramas.

## 1. Restricciones no negociables: preservar lo existente

1. **Bloqueo visual (visual freeze):** conservar la estética de PeerSync: fondo, gradientes, paleta, tipografías, tarjetas, bordes, radios, espaciados generales, iconos y diseño responsive. Reutilizar `frontend/src/index.css`, las clases existentes (`hero`, `card`, `btn`, `field`, etc.), los tokens `teach`, `learn`, `guide`, y Lucide. **No instalar un nuevo sistema de componentes, no crear otro tema, no reescribir el CSS global**. Se permiten estilos locales y ajustes mínimos para acomodar tarjetas y menú sin romper diseño móvil/escritorio.
2. **Regresión cero del flujo actual:** conservar crear/entrar/salir de salas, invitaciones, participantes, chat, adjuntos, vistas previas de YouTube, amistades, feedback al abandonar, autenticación, navegación, matching y otros módulos. No retirar endpoints ni cambiar contratos existentes si puede evitarse.
3. **Chat siempre disponible:** ningún estado de sugerencia, invitación, StudyMind o TeachBack bloquea enviar mensajes, adjuntar archivos, consultar el historial ni desplazarse por él (salvo comportamiento preexistente de sala cerrada).
4. **No modificar el stack:** React + TypeScript + Vite + Tailwind; FastAPI + SQLAlchemy + Alembic + PostgreSQL; Gemini exclusivamente desde backend. No añadir WebSockets como requisito: reutilizar el polling actual de la sala (aprox. 3 s) para el MVP.
5. **No tocar main directamente, no reset/force-push, no borrar trabajo de compañeros:** comprobar `git status`, ramas y diferencias. Crear rama de trabajo (`feature/contrasta-unificado`) o seguir la estrategia del equipo. Cambios pequeños y trazables.
6. **No romper la base de datos:** migraciones Alembic aditivas y reversibles; nada de borrar tablas o columnas existentes. No ejecutar migraciones ni pruebas destructivas sobre una base compartida/de producción. No introducir secretos.
7. **No simular funcionalidades como reales:** si Gemini falla, avisar con un estado de error adecuado y mantener chat/actividades manuales utilizables; no presentar texto fijo como si fuera una respuesta de IA.
8. **Accesibilidad:** navegación por teclado, foco visible, roles/labels, textos legibles, mensajes de error, compatibilidad móvil, no depender solo de color, evitar anuncios excesivos con `aria-live`.

## 2. Inspección previa obligatoria

Revisar como mínimo:

- Frontend: `frontend/src/pages/Room.tsx`, `frontend/src/services/rooms.ts`, `frontend/src/services/api.ts`, `frontend/src/index.css`, `frontend/src/components/`, `frontend/package.json`.
- Backend: `backend/app/api/endpoints/rooms.py`, `backend/app/api/router.py`, `backend/app/services/room_service.py`, `backend/app/models/session.py`, `backend/app/models/message.py`, `backend/app/ai/llm_client.py`, `backend/app/ai/studymind/`, `backend/app/ai/teachback/`, `backend/app/schemas/`, `backend/alembic/versions/` y `backend/tests/`.
- Documentación: `CLAUDE.md`, `GEMINI.md`, `README.md` y documentación API.

En la versión auditada: el chat funciona con polling; el panel «Apoyo de IA» es informativo; ya existen modelos `ContrastaRound`, `ContrastaAnswer`, `TeachBackSubmission`, `TeachBackPeerReview`, `TeachBackAIFeedback` y `StudyMindHint`, pero faltan endpoints/servicios para el recorrido completo. **Reutilizar modelos y servicios cuando resulte correcto, no duplicar estructuras por comodidad.** Los módulos `app/ai/studymind/*` y `app/ai/teachback/*` están vacíos en ese commit. Confirmar el estado real antes de implementar.

**Primera entrega:** inventario de lo existente, riesgos, plan incremental por archivos, contrato de datos previsto y una lista de comportamientos que quedarán inalterados. **Después implementar; no quedarse solo en la planificación.**

## 3. Comportamiento UX definitivo

### 3.1. Pantalla única de Contrasta

Conservar el aspecto actual de la sala: cabecera con título/objetivo, conversación principal y panel lateral de información/participantes. Reutilizar componentes y tokens visuales actuales.

- El **chat es el eje permanente**. Mensajes humanos mantienen apariencia actual.
- Añadir **menú contextual compacto**, accesible desde la zona de escritura o junto a ella, con cuatro acciones:
  1. **Necesitamos una pista** → StudyMind genera una pregunta o pista progresiva.
  2. **Queremos comprobar una idea** → StudyMind propone una forma de contrastarla (ejemplo, experimento, prueba, fuente); no finge haber ejecutado nada.
  3. **Practicar una explicación** → propone actividad TeachBack a la otra persona.
  4. **Hemos llegado a una conclusión** → permite registrar conclusión y ofrece TeachBack o comprobación individual.
- Presentar el menú como un popover/desplegable con componentes y clases ya existentes, usable en móvil y con teclado; **no convertirlo en cuatro botones permanentes gigantes**.
- Las intervenciones de Contrasta se presentan como **tarjetas discretas dentro del flujo o en un espacio contextual cercano al chat**, no modales invasivos ni rutas nuevas.
- StudyMind y TeachBack no necesitan pestañas propias. El panel «Apoyo de IA» puede convertirse en un acceso contextual o ayuda breve, conservando la estructura estética general.

### 3.2. Sugerencias no intrusivas

Ejemplo de tarjeta: «Parece que habéis aclarado la diferencia. ¿Queréis probar a explicárosla mutuamente?». Acciones: **Proponer explicación**, **Más tarde**, **Cerrar**. No añadir un botón «Seguir debatiendo»: el usuario simplemente sigue escribiendo.

- No se cambia de pantalla, no se oculta el chat, no se roba el foco del cuadro de texto y no se fuerza el scroll hacia la tarjeta si el usuario está leyendo mensajes antiguos.
- **Más tarde:** tarjeta minimizada/recuperable; **Cerrar:** se descarta para ese usuario sin alterar el estado compartido; propuesta aceptada por uno: se muestra como pendiente al otro.
- Evitar sugerencias duplicadas y spam. Una oportunidad pedagógica no puede generar múltiples tarjetas idénticas por cada refresh/poll.
- **MVP:** sugerencia determinista tras indicar explícitamente «Hemos llegado a una conclusión» y cuando alguien selecciona «Practicar una explicación». No usar vigilancia permanente ni detección automática de emociones, silencios o análisis continuo del chat. Una detección inteligente de momentos oportunos queda fuera del MVP.

### 3.3. Invitación TeachBack sin interrumpir

1. Ana selecciona **Practicar una explicación** o acepta la sugerencia de Contrasta.
2. Contrasta registra **propuesta pendiente** asociada a la ronda y visible para ambos; **no cambia el estado del debate**.
3. Luis ve: «Ana propone practicar una explicación. ¿Participas?», con **Aceptar** y **Ahora no**. Mientras decide, ambos siguen chateando.
4. Si Luis elige «Ahora no», el debate sigue; mostrar estado claro de propuesta pospuesta/rechazada sin penalización.
5. Si acepta, se inserta una **actividad TeachBack dentro de la conversación**, sin navegación.
6. Turno A: Ana redacta **su propia explicación** (editor con borrador propio); la envía; Luis revisa con comentario y, opcionalmente, solicita aclaraciones.
7. **Solo después de la revisión humana**, ofrecer feedback formativo de IA opcional. Nunca dar nota oficial ni afirmar infalibilidad.
8. Cambian los roles: Luis explica y Ana revisa. Puede omitirse la segunda vuelta solo si ambos lo acuerdan explícitamente; dejar la capacidad de completarla como recorrido recomendado.
9. El chat y los archivos **siguen accesibles en todos los estados**, incluida actividad activa. TeachBack no cierra la ronda ni termina la sala automáticamente.

### 3.4. Contrasta completo

- Al comenzar la ronda, ambos reciben una pregunta (introducida por un usuario o propuesta por la plataforma) y responden **individualmente**.
- Antes de la revelación, cada usuario solo puede consultar su propia respuesta y el progreso agregado (ej. 1/2). **La respuesta del compañero no debe aparecer en ningún endpoint, evento, petición al LLM ni payload de frontend.**
- Cuando las dos respuestas de los participantes definidos para la ronda estén guardadas, revelar ambas de forma atómica/consistente.
- Mostrar contraste de coincidencias, diferencias y preguntas de debate; no sentenciar automáticamente quién tiene razón.
- El chat existente permite discutir, citar razonamientos y compartir pruebas. Para el MVP, no es necesario implementar comentarios anidados ni una plataforma de debates compleja.
- Después de «Hemos llegado a una conclusión», permitir registrar la conclusión compartida, proponer TeachBack y proponer una **comprobación individual breve** sobre una variante del problema. Su resultado no es una calificación oficial.
- Si todavía no hay una ronda, el chat actual debe seguir funcionando igual. Ningún usuario debe quedar atrapado en un asistente obligatorio.

## 4. Reglas de estados y sincronización

**Separar estado de la ronda, estado de sugerencia, estado de propuesta y estado de TeachBack.** No representar todo con un único enum gigantesco ni cambiar `ContrastaStatus` sin necesidad.

Ejemplo:

```
ContrastaRound.status = INDIVIDUAL | REVEALED  # respetar el modelo existente
RoomConversation.status = OPEN  # chat humano independiente
TeachBackProposal.status = PENDING | ACCEPTED | DECLINED | CANCELLED
TeachBackActivity.status = EXPLAINING | PEER_REVIEW | READY_FOR_AI_FEEDBACK | COMPLETED
```

El esquema concreto puede adaptarse a lo existente, pero deben cumplirse estas invariantes:

- Sugerencia o invitación TeachBack **nunca** cierra ni bloquea el chat.
- Una propuesta compartida requiere confirmación de los dos participantes de la actividad. Un solo usuario no impone la actividad.
- Eventos visibles y actividades persisten tras recargar o entrar desde otro navegador; los borradores individuales pueden permanecer privados.
- Proteger de pulsaciones dobles, mensajes duplicados, eventos fuera de orden, polling concurrente y dos aceptaciones simultáneas (transacciones/idempotencia).
- Para el MVP, definir explícitamente el par de participantes de la ronda. Si una sala tiene más de dos usuarios, o si se incorpora alguien tarde, mostrar una restricción clara o gestionar un par seleccionado: **nunca revelar accidentalmente respuestas de una ronda por cambios en la lista de miembros**.
- Cerrar o abandonar una sala mantiene los comportamientos actuales de feedback y permisos; una propuesta pendiente no impide salir.

## 5. Backend y contrato API

Reutilizar autenticación, autorización, modelos, servicios y `llm_client.py`. Preferir endpoints **aditivos** bajo rutas coherentes con `/api/rooms/{room_id}/...` para:

- Crear/listar/consultar ronda Contrasta.
- Enviar mi respuesta y consultar estado; revelar respuestas solo cuando corresponde.
- Consultar eventos pedagógicos/tarjetas con IDs estables y visibilidad por usuario, o una línea de tiempo combinada con eventos tipados sin modificar/romper el contrato de mensajes actual.
- Registrar conclusión y acciones del menú contextual.
- Crear propuesta TeachBack; aceptarla/rechazarla/cancelarla; consultar estado.
- Enviar explicación; recibir revisión del compañero; ofrecer feedback IA **después** de la revisión humana; intercambiar roles.
- Pedir pista/verificación StudyMind con contexto mínimo autorizado.
- Crear/contestar la comprobación individual final.

**No son nombres de endpoint obligatorios:** estudiar rutas y esquemas actuales, diseñar una API mínima coherente, documentarla y tiparla en los servicios frontend. Todas las operaciones privadas deben comprobar pertenencia a la sala, asociación a la ronda y rol apropiado. Validar longitudes, permisos, orden de transiciones y rate limits de IA. Los eventos no pueden filtrar respuestas ocultas. Evitar datos personales innecesarios enviados a Gemini. No exponer claves en frontend.

Si no hay `GEMINI_API_KEY` o Gemini falla, StudyMind/feedback IA muestran una incidencia recuperable, sin inutilizar el chat ni la revisión entre iguales. No generar respuestas falsas.

## 6. Frontend y componentes

Refactorizar `Room.tsx` **de manera incremental**, sin reemplazar la página entera ni cambiar el layout. Extraer componentes pequeños cuando mejore la claridad, por ejemplo: `ContrastaActionMenu`, `ContrastaSuggestionCard`, `ContrastaRoundCard`, `TeachBackInvitationCard`, `TeachBackActivityCard`, `StudyMindHintCard` y tipos/API específicos. Usar nombres compatibles con las convenciones actuales.

El menú permanece disponible incluso si hay una sugerencia. No abrir modales que capturen la conversación. Mantener la altura y scroll del chat compatibles con la vista actual; la aparición de nuevas tarjetas no debe hacer que la escritura salte o pierda foco. Añadir loading/error/success/deshabilitado para acciones asíncronas. Preservar el diseño responsive y la estética actual. Reusar `fetchMessages`, `sendMessage` y adjuntos existentes.

## 7. Trabajo por fases (aplicar cambios y validar cada fase)

**Fase 0 — Línea base:** comprobar ramas y working tree; ejecutar tests y build actuales y anotar fallos previos; documentar capturas del diseño actual (escritorio y móvil, si el entorno permite navegador). No cambiar UI global.

**Fase 1 — Núcleo Contrasta:** API de ronda, respuestas privadas, revelación, tarjetas de comparación y sincronización; tests de privacidad y roles. Conservar chat existente.

**Fase 2 — Menú y sugerencias:** introducir menú contextual y sugerencias posponibles/cerrables, invitación TeachBack con doble consentimiento; chat siempre utilizable; estados compartidos persistentes.

**Fase 3 — TeachBack integrado:** editores/revisiones en tarjetas dentro del chat, turnos, revisión humana previa a IA, posibilidad de continuar debatiendo.

**Fase 4 — StudyMind + cierre:** pistas/verificaciones a demanda desde menú, conclusión compartida y comprobación individual, sin respuestas automáticas que sustituyan a los compañeros.

**Fase 5 — QA y documentación:** ejecutar test suites y build, verificar manualmente dos usuarios en sesiones de navegador diferentes, inspeccionar diferencias visuales, corregir errores, actualizar `CLAUDE.md`, `GEMINI.md`, `README.md` y API docs. Unificar instrucciones de producto: Contrasta es el centro; StudyMind/TeachBack son capacidades integradas, no destinos separados.

Entregar por cada fase: resumen de cambios, lista de archivos, migraciones, comandos realmente ejecutados y su resultado, pruebas añadidas y posibles riesgos. No afirmar haber probado lo que no se ejecutó.

## 8. Criterios de aceptación obligatorios

1. Una sala antigua sin ronda sigue teniendo chat, adjuntos, invitaciones y gestión de participantes exactamente como antes.
2. Dos usuarios diferentes abren la misma sala; pueden crear una ronda y responder independientemente. Antes de ambas entregas es imposible obtener la respuesta ajena, incluso consultando directamente la API.
3. Tras dos respuestas, aparecen las explicaciones reveladas sin duplicados en ambos navegadores.
4. El chat puede enviar y recibir mensajes **antes, durante y después** de ver una sugerencia; igualmente mientras hay propuesta pendiente o TeachBack activo.
5. Al ver una sugerencia, un usuario puede ignorarla, descartarla o posponerla sin alterar el debate; el menú permanece accesible.
6. La propuesta de TeachBack llega al otro usuario y no se activa sin su aceptación; rechazar no bloquea el chat; aceptar dos veces no duplica la actividad.
7. Explicación y revisión suceden dentro de Contrasta; el feedback IA no puede generarse antes de la revisión humana.
8. StudyMind solo responde cuando se solicita; no inventa ejecuciones ni revela soluciones completas por defecto; no filtra respuestas privadas.
9. Recargar la página conserva propuestas, actividades y mensajes sin estados inconsistentes; cerrar sala respeta permisos actuales.
10. El diseño de sala conserva aspecto general en desktop/móvil; navegación por teclado y etiquetas accesibles. Sin paquetes visuales nuevos.
11. Pasan los tests existentes y los nuevos; `npm run lint` y `npm run build` pasan o se explican errores preexistentes; `pytest` pasa en entorno de pruebas. Hay tests de seguridad, transiciones, concurrencia/idempotencia y regresión.
12. Ningún cambio arriesga los datos reales: migración revisada, aditiva, y probada en base desechable antes de aplicarla a entornos compartidos.

## 9. Escenario de demostración que debe funcionar

Ana y Luis entran en una sala titulada «Punteros en C» y debaten `p++` frente a `(*p)++`:

1. Ambos responden individualmente; las respuestas están ocultas entre sí.
2. Al responder los dos, Contrasta revela las respuestas y muestra el contraste.
3. Discuten en el chat. Ana usa el menú → «Queremos comprobar una idea» y Contrasta propone un experimento en C sin inventar resultados.
4. Siguen hablando sin interrupción. Pulsan «Hemos llegado a una conclusión» y registran su acuerdo.
5. Contrasta sugiere practicar una explicación. Ana pulsa «Proponer explicación» y Luis puede seguir enviando mensajes mientras decide.
6. Luis acepta. Aparece una actividad TeachBack integrada: Ana explica, Luis revisa, opcionalmente llega feedback IA; después intercambian roles.
7. Ambos completan una pregunta breve individual y ven el resumen de lo que han cambiado en su razonamiento.
8. Nada de esto modifica visualmente la identidad de PeerSync ni rompe el chat preexistente.

## 10. Entrega final solicitada

Proporciona: (a) PR/diff o cambios aplicados por archivos, (b) resumen funcional, (c) explicación del modelo de estados, (d) endpoints y migraciones, (e) pruebas con resultados reales, (f) capturas antes/después si es posible, (g) instrucciones reproducibles para probar en Codespaces con dos usuarios, y (h) lista explícita de cualquier parte pendiente o decisión técnica tomada. **Priorizar una demo vertical de dos estudiantes completamente funcional frente a muchos botones inconexos.**
