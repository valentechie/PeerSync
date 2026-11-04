# API de Swap4Edu

Base: `/api`. Documentación interactiva con el backend en marcha: `/docs`.

Los endpoints protegidos requieren `Authorization: Bearer <token>`. Sin token válido responden `401`.

Errores: `{"detail": "..."}`, o una lista de `{loc, msg, type}` en los `422` (nunca repite el valor enviado). `429` si se supera el límite de peticiones; `503` si la base de datos no está disponible.

## Auth

| Método | Ruta | Cuerpo | Respuestas | Límite |
|---|---|---|---|---|
| POST | `/auth/register` | `name`, `email`, `password` (8 caracteres a 72 bytes) | `201` token y usuario · `409` email ya registrado · `422` | 5/min por IP |
| POST | `/auth/login` | `email`, `password` | `200` token y usuario · `401` credenciales incorrectas | 10/min por IP |

Respuesta: `{"access_token", "token_type": "bearer", "user": {"id", "name", "email", "created_at"}}`. El token caduca a los `ACCESS_TOKEN_EXPIRE_MINUTES`.

## Perfil

Solo el perfil del usuario del token: no hay forma de leer o editar el de otro.

| Método | Ruta | Respuestas | Límite |
|---|---|---|---|
| GET | `/profiles/me` | `200` perfil | 120/min por IP |
| PATCH | `/profiles/me` | `200` perfil · `422` | 30/min por IP |

Perfil: `{"id", "name", "email", "bio", "skillsOffering", "skillsSeeking", "reputation", "completedSessions"}`. `reputation` es `null` hasta la primera valoración.

PATCH admite `name`, `bio` (máx. 1000), `skillsOffering` y `skillsSeeking` (máx. 20 de hasta 100 caracteres). Los campos omitidos no cambian; una lista enviada sustituye a la anterior. `email`, `reputation` y `completedSessions` no son editables.

## Matching

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

