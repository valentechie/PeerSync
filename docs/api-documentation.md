# API de PeerSync

Base: `/api`. Documentación interactiva con el backend en marcha: `/docs`.

Los endpoints protegidos requieren `Authorization: Bearer <token>`. Sin token válido responden `401`.

Errores: `{"detail": "..."}`, o una lista de `{loc, msg, type}` en los `422` (nunca repite el valor enviado). `429` si se supera el límite de peticiones; `503` si la base de datos no está disponible.

## Auth

**Modo demo para el hackathon: no hay contraseñas ni se comprueba ninguna credencial.** Cualquiera puede entrar como cualquier usuario.

| Método | Ruta | Cuerpo | Respuestas | Límite |
|---|---|---|---|---|
| POST | `/auth/login` | `email` (cualquier texto, de 1 a 320 caracteres) | `200` `{"access_token", "token_type"}` · `403` cuenta desactivada · `422` | 60/min por IP |

Si el usuario no existe, se crea. El token dura 7 días.

## Salas

El centro de PeerSync: salas privadas donde estudian personas que no tienen por qué ser expertas. Solo se entra con una invitación o un enlace de invitación, y solo los participantes ven la sala y sus mensajes. El frontend consulta cada 3 segundos.

| Método | Ruta | Respuestas | Límite |
|---|---|---|---|
| GET | `/rooms` | `200` solo las salas en las que estás; las invitaciones llegan por `/invitations` | 120/min por IP |
| POST | `/rooms` con `title` (hasta 120) y `objective` (hasta 300) | `201` sala, con su creador dentro · `409` feedback pendiente · `422` | 20/min por IP |
| GET | `/rooms/{id}` | `200` sala y participantes · `403` no estás dentro · `404` · `409` cerrada | 600/min por IP |
| POST | `/rooms/{id}/join`, opcionalmente con `inviteToken` | `200` sala (repetirlo no cambia nada) · `403` sin invitación ni enlace válido · `404` · `409` cerrada o feedback pendiente | 60/min por IP |
| GET | `/rooms/{id}/invite-link` | `200` `{"token"}`, firmado y válido 7 días, solo para esa sala · `403` · `404` · `409` | 60/min por IP |
| POST | `/rooms/{id}/leave` | `200` a quién debes evaluar · `404` · `409` ya cerrada. La última persona en salir cierra la sala | 60/min por IP |
| GET | `/rooms/{id}/messages` | `200` últimos 100 mensajes · `403` no participa · `404` | 600/min por IP |
| POST | `/rooms/{id}/messages` con `content` (hasta 2000) | `201` · `403` · `404` · `422` | 120/min por IP |
| POST | `/rooms/{id}/attachments?fileName=`, con el archivo como cuerpo | `201` mensaje con `attachment` · `403` · `404` · `413` más de 4 MB o sala llena · `415` formato no admitido · `422` vacío | 30/min por IP |
| POST | `/rooms/{id}/reviews` con `revieweeId`, `punctuality`, `treatment`, `participation` y `clarity` (enteros de 0 a 10) | `201` · `404` no coincidisteis · `409` sigues dentro o ya evaluaste · `422` | 60/min por IP |
| GET | `/rooms/{id}/attachments/{attachmentId}` | `200` el archivo · `403` · `404` | 600/min por IP |

Archivos: PNG, JPEG, GIF, WebP, MP3, OGG, WAV, M4A, MP4, WebM y PDF, hasta 4 MB cada uno y 100 MB por sala. El tipo se detecta por el contenido, nunca por el nombre. Solo los participantes de la sala pueden subirlos y descargarlos.

Sala: `{"id", "title", "objective", "participantCount", "isMember", "lastActivityAt"}`, más `participants` con `id` y `name`. Nunca incluye emails.

## Invitaciones

Cualquier participante de una sala abierta puede invitar a amigos o a otros usuarios. Invitar no mete a nadie en la sala: la otra persona decide. Una invitación rechazada no se puede repetir en esa sala.

| Método | Ruta | Respuestas | Límite |
|---|---|---|---|
| GET | `/rooms/{id}/invite-candidates?search=` (2 a 100 caracteres, opcional) | `200` tus amigos, o usuarios por nombre con tus amigos primero · `403` · `404` · `409` cerrada · `422` | 120/min por IP |
| POST | `/rooms/{id}/invitations` con `inviteeId` | `201` · `400` a ti · `403` no estás dentro · `404` · `409` ya está dentro, rechazó o sala cerrada · `422` | 60/min por IP |
| GET | `/invitations` | `200` tus invitaciones pendientes a salas abiertas | 240/min por IP |
| POST | `/invitations/{id}/accept` | `200` `{"roomId"}` · `404` · `409` sala cerrada o feedback pendiente | 60/min por IP |
| DELETE | `/invitations/{id}` | `204` rechaza · `404` | 60/min por IP |

Candidato: `{"id", "name", "study", "isFriend", "status"}`, con `status` en `member`, `invited`, `declined` o `null`. Nunca incluye el email.

## Amigos

Cada pareja tiene una sola relación. Las respuestas nunca incluyen emails.

| Método | Ruta | Respuestas | Límite |
|---|---|---|---|
| GET | `/friends` | `200` `{"friends", "received", "sent"}` | 120/min por IP |
| POST | `/friends/{id}` | `200` persona; si esa persona ya te lo pidió, quedáis como amigos · `400` a ti · `404` | 60/min por IP |
| POST | `/friends/{id}/accept` | `200` · `404` sin solicitud de esa persona | 60/min por IP |
| DELETE | `/friends/{id}` | `204`: rechaza, cancela o elimina | 60/min por IP |

Persona: `{"id", "name", "bio", "sharedInterests", "friendStatus"}`, con `friendStatus` en `friend`, `sent`, `received` o `null`. Cada amigo incluye `rooms`, hasta 3 salas suyas que tú puedes abrir, porque estás dentro o te han invitado.

## Personas

| Método | Ruta | Respuestas | Límite |
|---|---|---|---|
| GET | `/people?search=` (2 a 100 caracteres) | `200` hasta 20 personas por nombre · `422` | 60/min por IP |
| GET | `/people/study-matches` | `200` hasta 50 personas con tu mismo estudio o uno parecido, con `study`, `matchType` y `matchReason` | 60/min por IP |
| GET | `/people/same-interests` | `200` hasta 50 personas que quieren aprender algo que tú quieres aprender | 60/min por IP |

Los estudios se relacionan por reglas, sin LLM (`backend/app/ai/skillswap/studies.py`): `direct` si es el mismo título y `similar` si es de la misma familia, aunque sea de otro nivel, como SMR e Ingeniería Informática. "Otros estudios de..." solo cuenta como parecido, y "Otros estudios" no se relaciona. Orden: `direct` primero, luego temas en común, nombre e id.

La coincidencia es determinista y sin LLM: compara `skillsSeeking` sin distinguir mayúsculas. Orden: temas en común, nombre e id.

## Estudios

| Método | Ruta | Respuestas | Límite |
|---|---|---|---|
| GET | `/studies` | `200` catálogo por familias: `[{"name", "studies": [{"code", "label"}]}]` | 60/min por IP |

## Practicar

Entrenamiento de explicación con Gemini, invocado solo desde el backend. La IA hace una pregunta cada vez: no da la respuesta ni pone nota. No se guarda nada: el navegador envía la conversación en cada turno, y a Gemini solo llegan el tema y la conversación.

| Método | Ruta | Respuestas | Límite |
|---|---|---|---|
| POST | `/practice/next` con `topic` (hasta 120) e `history` (hasta 40 turnos alternos de `coach` y `student`, hasta 2000 caracteres) | `200` `{"question"}` · `422` · `502` Gemini no devolvió texto · `503` sin `GEMINI_API_KEY` o Gemini no disponible | 30/min por IP |

## Evaluación entre pares

Es obligatoria y no se escribe nada: al salir de una sala, cada persona puntúa de 0 a 10 la puntualidad, el trato, la participación y la claridad de todos los demás participantes, salvo quien entró después de que saliera. Mientras tenga evaluaciones pendientes no puede entrar en ninguna sala ni crear otra. La reputación (0 a 5) sale de la media de esas puntuaciones.

Una sala se cierra cuando sale la última persona. Quien sale deja de ver sus mensajes y archivos, y para volver necesita otra invitación.

| Método | Ruta | Respuestas | Límite |
|---|---|---|---|
| GET | `/profiles/me/pending-reviews` | `200` `[{"roomId", "roomTitle", "personId", "personName"}]` | 120/min por IP |
| GET | `/profiles/me/feedback?page=` (desde 1) | `200` `{"count", "page", "pageSize", "average", "punctuality", "treatment", "participation", "clarity", "items"}`: 5 evaluaciones por página, medias sobre 10 de todas | 120/min por IP |

Solo cada persona puede ver su propio feedback, con el nombre de quien evaluó.

## Perfil

Solo el perfil del usuario del token: no hay forma de leer o editar el de otro.

| Método | Ruta | Respuestas | Límite |
|---|---|---|---|
| GET | `/profiles/me` | `200` perfil | 120/min por IP |
| PATCH | `/profiles/me` | `200` perfil · `422` | 30/min por IP |
| PUT | `/profiles/me/photo`, con la imagen como cuerpo | `200` perfil · `413` más de 1 MB · `415` no es JPEG, PNG ni WebP · `422` vacía | 30/min por IP |
| DELETE | `/profiles/me/photo` | `200` perfil | 30/min por IP |
| GET | `/users/{id}/photo`, sin token porque la pide una etiqueta `<img>` | `200` la imagen · `404` | 1200/min por IP |

Perfil: `{"id", "name", "email", "bio", "studyCode", "study", "photoUrl", "skillsOffering", "skillsSeeking", "reputation", "completedSessions"}`. `reputation` es `null` hasta la primera valoración.

PATCH admite `studyCode` (código del catálogo, `null` lo quita; otro valor da `422`), `name`, `bio` (máx. 1000), `skillsOffering` y `skillsSeeking` (máx. 20 de hasta 100 caracteres). Los campos omitidos no cambian; una lista enviada sustituye a la anterior. `email`, `reputation` y `completedSessions` no son editables.

## Matching

Sin uso en la web actual, que se centra en las salas. La API sigue disponible.

La compatibilidad es determinista y no usa ningún LLM (`backend/app/ai/skillswap/matcher.py`). Puntuación sobre 100:

- Hasta 40: parte de lo que buscas que el compañero ofrece.
- Hasta 40: parte de lo que el compañero busca que tú ofreces.
- Hasta 20: reputación. Sin valoraciones cuenta como 3/5.

Orden: puntuación, habilidades complementarias, nombre e id. Solo se sugiere a quien comparte alguna habilidad complementaria.

| Método | Ruta | Respuestas | Límite |
|---|---|---|---|
| GET | `/matching/suggestions?limit=20` (1 a 50) | `200` lista de compañeros | 60/min por IP |
| GET | `/matching/partners/{id}` | `200` compañero · `404` | 60/min por IP |
| POST | `/matching/requests` con `{"receiverId"}` | `201` · `400` a uno mismo · `404` · `409` ya existe o no se complementan | 20/min por IP |

Compañero: `{"id", "name", "bio", "skillsOffering", "skillsSeeking", "reputation", "completedSessions", "score", "breakdown", "requestStatus"}`. Nunca incluye el email. `requestStatus`: `sent`, `received`, `connected` o `null`. `breakdown`: `learnPoints`, `teachPoints`, `reputationPoints`, `theyTeachYou`, `youTeachThem`.

La puntuación de una solicitud la calcula siempre el servidor, y se guarda una copia con su desglose.

