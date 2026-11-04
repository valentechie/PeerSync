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

El centro de PeerSync: salas abiertas donde estudian personas que no tienen por qué ser expertas. Cualquiera con sesión puede ver las salas, crearlas y unirse. Solo sus participantes leen y envían mensajes. El frontend consulta cada 3 segundos.

| Método | Ruta | Respuestas | Límite |
|---|---|---|---|
| GET | `/rooms` | `200` lista de salas | 120/min por IP |
| POST | `/rooms` con `title` (hasta 120) y `objective` (hasta 300) | `201` sala, con su creador dentro · `422` | 20/min por IP |
| GET | `/rooms/{id}` | `200` sala y participantes · `404` | 600/min por IP |
| POST | `/rooms/{id}/join` | `200` sala (repetirlo no cambia nada) · `404` | 60/min por IP |
| POST | `/rooms/{id}/leave` | `204` · `404` | 60/min por IP |
| GET | `/rooms/{id}/messages` | `200` últimos 100 mensajes · `403` no participa · `404` | 600/min por IP |
| POST | `/rooms/{id}/messages` con `content` (hasta 2000) | `201` · `403` · `404` · `422` | 120/min por IP |
| POST | `/rooms/{id}/attachments?fileName=`, con el archivo como cuerpo | `201` mensaje con `attachment` · `403` · `404` · `413` más de 4 MB o sala llena · `415` formato no admitido · `422` vacío | 30/min por IP |
| POST | `/rooms/{id}/close` | `200` sala cerrada · `403` solo quien la abrió, o cualquiera de dentro si esa persona se fue · `404` | 30/min por IP |
| POST | `/rooms/{id}/reviews` con `revieweeId`, `clarity`, `listening` y `preparation` (de 1 a 5) y `comment` (20 a 1000) | `201` · `400` a ti · `403` no estuvo · `404` esa persona no estuvo · `409` sala abierta o ya evaluada · `422` | 30/min por IP |
| GET | `/rooms/{id}/attachments/{attachmentId}` | `200` el archivo · `403` · `404` | 600/min por IP |

Archivos: PNG, JPEG, GIF, WebP, MP3, OGG, WAV, M4A, MP4, WebM y PDF, hasta 4 MB cada uno y 100 MB por sala. El tipo se detecta por el contenido, nunca por el nombre. Solo los participantes de la sala pueden subirlos y descargarlos.

Sala: `{"id", "title", "objective", "participantCount", "isMember", "lastActivityAt"}`, más `participants` con `id` y `name`. Nunca incluye emails.

## Amigos

Cada pareja tiene una sola relación. Las respuestas nunca incluyen emails.

| Método | Ruta | Respuestas | Límite |
|---|---|---|---|
| GET | `/friends` | `200` `{"friends", "received", "sent"}` | 120/min por IP |
| POST | `/friends/{id}` | `200` persona; si esa persona ya te lo pidió, quedáis como amigos · `400` a ti · `404` | 60/min por IP |
| POST | `/friends/{id}/accept` | `200` · `404` sin solicitud de esa persona | 60/min por IP |
| DELETE | `/friends/{id}` | `204`: rechaza, cancela o elimina | 60/min por IP |

Persona: `{"id", "name", "bio", "sharedInterests", "friendStatus"}`, con `friendStatus` en `friend`, `sent`, `received` o `null`. Cada amigo incluye `rooms`, hasta 3 salas en las que está.

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

Al cerrarse una sala queda en solo lectura para quienes estaban dentro, y cada uno evalúa a los demás una sola vez. `rating` es la media redondeada de los tres criterios, y de él sale la reputación.

| Método | Ruta | Respuestas | Límite |
|---|---|---|---|
| GET | `/profiles/me/pending-reviews` | `200` `[{"roomId", "roomTitle", "personId", "personName"}]` | 120/min por IP |
| GET | `/profiles/me/feedback` | `200` `{"count", "average", "clarity", "listening", "preparation", "items"}` | 120/min por IP |

Solo cada persona puede ver su propio feedback, con el nombre de quien evaluó.

## Perfil

Solo el perfil del usuario del token: no hay forma de leer o editar el de otro.

| Método | Ruta | Respuestas | Límite |
|---|---|---|---|
| GET | `/profiles/me` | `200` perfil | 120/min por IP |
| PATCH | `/profiles/me` | `200` perfil · `422` | 30/min por IP |

Perfil: `{"id", "name", "email", "bio", "studyCode", "study", "skillsOffering", "skillsSeeking", "reputation", "completedSessions"}`. `reputation` es `null` hasta la primera valoración.

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

