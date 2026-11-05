# Base de datos de PeerSync

PostgreSQL en Supabase. El esquema se gestiona con Alembic (`backend/alembic/`); `database/schema.sql` es una copia generada con `alembic upgrade head --sql`, no se edita a mano.

## Seguridad

Supabase publica el esquema `public` en una API REST. **Toda tabla nueva debe activar RLS en su migración.** Sin políticas, esa API no puede leerla ni escribirla; el backend conecta como propietario y no se ve afectado.

## Tablas

| Tabla | Contenido | Reglas clave |
|---|---|---|
| `users` | Cuenta: nombre y usuario (columna `email`) | Usuario único, en minúsculas; en modo demo no siempre es un correo; `supabase_user_id` y `password_hash` sin uso |
| `profiles` | Biografía, estudio (`study_code`) y foto (`photo_data`, `photo_type`, `photo_version`) | Se crea al guardar por primera vez; el catálogo de estudios está en el código |
| `skills` | Catálogo de habilidades | Nombre único sin distinguir mayúsculas |
| `user_skills` | Qué quiere aprender (`seeking`) u ofrece (`offering`, sin uso en la web) cada usuario | |
| `match_requests` | Solicitudes de intercambio | Nunca consigo mismo; una pendiente por dirección; guarda `score` y `score_breakdown` |
| `study_sessions` | Salas de estudio | Sin `match_id` es una sala abierta, con `title` y `created_by_id` |
| `friendships` | Amistades y solicitudes | Una fila por pareja, en orden fijo; `status`: `pending` o `accepted` |
| `room_invitations` | Invitaciones a salas | Una por persona y sala; `status`: `pending` o `declined`; se borra al entrar |
| `session_participants` | Quién está o estuvo en cada sala | Una fila por usuario y sala; `left_at` marca la salida |
| `messages` | Chat de la sala | |
| `message_attachments` | Archivos del chat, guardados en la propia base de datos | Uno por mensaje; hasta 4 MB |
| `session_reviews` | Evaluación entre pares | `punctuality`, `treatment`, `participation` y `clarity` de 0 a 10; `rating` de 0 a 5; una por sala y pareja |
| `studymind_hints` | Pistas pedidas | `level` de 1 a 3; siempre por petición explícita |
| `teachback_submissions` | Explicaciones del estudiante | |
| `teachback_peer_reviews` | Revisión del compañero | Una por explicación |
| `teachback_ai_feedback` | Feedback formativo de IA | `peer_review_id` obligatorio; sin columna de nota |
| `contrasta_rounds` | Rondas de Contrasta | `status`: `individual` o `revealed` |
| `contrasta_answers` | Respuestas individuales | Una por usuario y ronda; ocultarlas hasta `revealed` es tarea del servicio |
| `contrasta_comparisons` | Comparación con IA pedida por la pareja | Una por ronda; `status`: `pending`, `ready` o `failed` |
| `contrasta_cards` | Pistas y comprobaciones de StudyMind en una ronda | `private` antes de revelar |
| `teachback_activities` | Propuesta y actividad TeachBack de una pareja | Nace `pending`; turno 1 explica quien propone y turno 2 su pareja |
| `contrasta_checks` | Comprobación individual | Una por ronda; sin nota ni solución |
| `contrasta_check_answers` | Respuestas a la comprobación | Ocultas hasta que respondan los dos |

Reputación y sesiones completadas no se almacenan: se calculan a partir de `session_reviews` y `study_sessions`.

Todas las claves foráneas usan `ON DELETE CASCADE`: borrar un usuario borra sus datos.

## Contrasta por parejas (migración `0015`)

Solo añade tablas y columnas opcionales. En `contrasta_rounds`: `pair_a_id` y `pair_b_id` (sin ellas la ronda sigue las reglas de siempre), `conclusion`, `conclusion_by_id`, `conclusion_at`, `conclusion_confirmed_at`, `finish_requested_by_id` y `finished_at`. En `teachback_submissions`: `activity_id` y `turn`; sin `activity_id` es una explicación independiente del panel.

La migración debe aplicarse antes de desplegar este código: el código nuevo lee esas columnas en las rutas de Contrasta y TeachBack.
