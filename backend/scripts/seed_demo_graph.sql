-- Datos de demo del hackathon para los grafos de conexiones. Se pega en el SQL Editor de Supabase.
--
--   *   15 fantasmas amigos de valen@gmail.com          -> grafo "My network"
--   *   40 fantasmas que NO son sus amigos, con estudios
--          de su misma familia                          -> grafo "Discover" (muestra 30 como máximo)
--   * Amistades entre fantasmas de la misma familia.
--
-- Valen no tenía estudios ni temas, y sin ellos Discover sale vacío: este script le asigna ambos.
-- Se puede ejecutar varias veces sin duplicar nada. Para deshacerlo, ver el final del archivo.

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'valen@gmail.com') THEN
    RAISE EXCEPTION 'No existe el usuario valen@gmail.com';
  END IF;
END $$;

-- Códigos de `app/ai/skillswap/studies.py`: un código fuera del catálogo no se relaciona con nadie.
CREATE TEMP TABLE demo_study (pos int GENERATED ALWAYS AS IDENTITY, family text, code text) ON COMMIT DROP;
INSERT INTO demo_study (family, code)
SELECT family, unnest(codes)
FROM (VALUES
  ('Electronics', ARRAY['inst-telecom','inst-electricas','sist-telecom','automatizacion','mant-electronico','sist-electrotecnicos','ing-telecom','ing-electronica','ing-electrica']),
  ('Industry',    ARRAY['mecanizado','soldadura','electromecanica','automocion','diseno-mecanico','mecatronica','ing-mecanica','ing-industrial','ing-aeroespacial']),
  ('Construction',ARRAY['proyectos-edificacion','proyectos-obra-civil','arquitectura','ing-civil']),
  ('Business',    ARRAY['gestion-admin','admin-finanzas','asistencia-direccion','ade','economia','finanzas-contabilidad']),
  ('Commerce',    ARRAY['actividades-comerciales','marketing-publicidad','comercio-internacional','gestion-ventas','marketing']),
  ('Healthcare',  ARRAY['auxiliar-enfermeria','farmacia-parafarmacia','emergencias','laboratorio-clinico','imagen-diagnostico','higiene-bucodental','dietetica','medicina','enfermeria','farmacia','fisioterapia']),
  ('Education',   ARRAY['dependencia','educacion-infantil-fp','integracion-social','animacion-sociocultural','magisterio-infantil','magisterio-primaria','pedagogia','psicologia','trabajo-social']),
  ('Design',      ARRAY['video-dj-sonido','animacion-3d','realizacion','sonido','comunicacion-audiovisual','periodismo','bellas-artes','diseno']),
  ('Hospitality', ARRAY['cocina','servicios-restauracion','direccion-cocina','alojamientos','agencias-viajes','turismo','gastronomia']),
  ('Sport',       ARRAY['guia-medio-natural','animacion-sociodeportiva','acondicionamiento-fisico','cafyd']),
  ('Sciences',    ARRAY['quimica-industrial','matematicas','fisica','quimica','biologia','biotecnologia']),
  ('Law',         ARRAY['derecho','historia','filologia','traduccion']),
  ('Secondary',   ARRAY['bach-ciencias','bach-sociales','bach-artes','bach-general'])
) AS families (family, codes);

-- `family` agrupa las amistades entre fantasmas; `topics` son temas que también quiere aprender valen.
CREATE TEMP TABLE demo_ghost (n int PRIMARY KEY, family text, code text, topics text[]) ON COMMIT DROP;

-- Amigos, informática (12): quedan muy unidos a valen y forman el grupo central del grafo.
INSERT INTO demo_ghost
SELECT n, 'Computing',
       (ARRAY['ing-informatica','ing-software','dam','daw','asir','smr','ciberseguridad','ciencia-datos','ia','ing-computadores'])[1 + n % 10],
       CASE n % 4
         WHEN 0 THEN ARRAY['Python','Algorithms']
         WHEN 1 THEN ARRAY['Databases']
         WHEN 2 THEN ARRAY['Python']
         ELSE ARRAY[]::text[]
       END
FROM generate_series(1, 12) AS n;

-- Amigos, otras familias (3): comparten Python con valen, así que todos tienen algo en común.
INSERT INTO demo_ghost
SELECT n, s.family, s.code, CASE WHEN n % 10 = 0 THEN ARRAY['Python'] ELSE ARRAY[]::text[] END
FROM unnest(ARRAY[460, 470, 480]) AS n
JOIN demo_study s ON s.pos = 1 + n % (SELECT count(*) FROM demo_study);

-- Discover: escalonado por puntuación para que el top 30 tenga vínculos fuertes, buenos y posibles.
-- Misma carrera = 35, parecida = 20 y cada tema en común = 15. Fuerte >= 60, bueno >= 35.
INSERT INTO demo_ghost
SELECT n, 'Computing', code, topics
FROM (VALUES
  (1001, 1005, 'ing-informatica', ARRAY['Python','Algorithms']),               -- 65
  (1006, 1010, 'ciencia-datos',   ARRAY['Python','Databases','Machine Learning']), -- 65
  (1011, 1015, 'ing-informatica', ARRAY['Machine Learning']),                  -- 50
  (1016, 1020, 'ing-software',    ARRAY['Algorithms']),                        -- 35
  (1021, 1025, 'ing-informatica', ARRAY[]::text[]),                            -- 35
  (1026, 1030, 'daw',             ARRAY[]::text[]),                            -- 20
  (1031, 1035, 'ia',              ARRAY[]::text[]),                            -- 20
  (1036, 1040, 'ciberseguridad',  ARRAY[]::text[])                             -- 20
) AS tiers (first_n, last_n, code, topics)
CROSS JOIN LATERAL generate_series(first_n, last_n) AS n;

ALTER TABLE demo_ghost ADD COLUMN id uuid, ADD COLUMN email text, ADD COLUMN name text;
UPDATE demo_ghost
SET id = md5('peersync-demo-ghost-' || n)::uuid,
    email = format('demo-ghost-%s@example.com', lpad(n::text, 4, '0')),
    name = (ARRAY['Alba','Hugo','Lucía','Mateo','Martina','Leo','Sofía','Pablo','Julia','Daniel','Paula','Álvaro','Carla','Adrián','Sara','Diego','Noa','Marcos','Irene','Javier','Vera','Iker','Claudia','Bruno','Nerea','Gael','Elena','Rubén','Aina','Óscar','Marta','Nil','Lola','Sergio','Ana','Unai','Emma','Raúl','Inés','Marc'])[1 + (n - 1) % 40]
           || ' ' ||
           (ARRAY['García','Martín','Navarro','Ortega','Vidal','Serrano','Molina','Castro','Rubio','Marín','Soler','Iglesias','Campos','Vega','Herrero','Prieto','Reyes','Nieto','Crespo','Cano','Peña','Lozano','Santos','Bravo','Rojas','Pascual','Ibáñez','Mora','Gil','Blanco','Núñez','Ferrer','Aguilar','Roca','Delgado','Sáez','Calvo','León','Parra','Costa'])[1 + ((n - 1) * 7 + (n - 1) / 40) % 40];

-- Usuarios y perfiles. Sin contraseña: el modo demo no la comprueba.
INSERT INTO users (id, name, email, is_active)
SELECT id, name, email, true FROM demo_ghost
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO profiles (user_id, bio, study_code)
SELECT id, '', code FROM demo_ghost
ON CONFLICT (user_id) DO UPDATE SET study_code = EXCLUDED.study_code, updated_at = now();

-- Valen. Si cambias su carrera, usa una de Computing o Discover dejará de tener a los 40 de arriba.
INSERT INTO profiles (user_id, bio, study_code)
SELECT id, '', 'ing-informatica' FROM users WHERE email = 'valen@gmail.com'
ON CONFLICT (user_id) DO UPDATE SET study_code = EXCLUDED.study_code, updated_at = now();

-- Temas. El índice único de `skills` es sobre lower(name): la "Python" que ya existe se reutiliza.
INSERT INTO skills (id, name)
SELECT md5('peersync-demo-skill-' || lower(topic))::uuid, topic
FROM unnest(ARRAY['Python','Algorithms','Databases','Machine Learning']) AS topic
ON CONFLICT (lower(name)) DO NOTHING;

INSERT INTO user_skills (user_id, skill_id, kind)
SELECT g.id, s.id, 'seeking'
FROM demo_ghost g
CROSS JOIN LATERAL unnest(g.topics) AS topic
JOIN skills s ON lower(s.name) = lower(topic)
ON CONFLICT DO NOTHING;

INSERT INTO user_skills (user_id, skill_id, kind)
SELECT u.id, s.id, 'seeking'
FROM users u
JOIN skills s ON lower(s.name) IN ('python', 'algorithms', 'databases', 'machine learning')
WHERE u.email = 'valen@gmail.com'
ON CONFLICT DO NOTHING;

-- Valen con sus 15 amigos. Cada pareja es una fila ordenada, igual que `friend_service._pair`.
INSERT INTO friendships (user_a_id, user_b_id, requester_id, status)
SELECT least(u.id, g.id), greatest(u.id, g.id), u.id, 'accepted'
FROM users u
JOIN demo_ghost g ON g.n <= 1000
WHERE u.email = 'valen@gmail.com'
ON CONFLICT DO NOTHING;

-- Fantasmas entre sí: cada uno con los 3 siguientes de su familia.
-- El grafo no dibuja estas filas (por privacidad, sus líneas salen de estudios, temas y salas),
-- pero sí cuentan para el resto de la web.
INSERT INTO friendships (user_a_id, user_b_id, requester_id, status)
SELECT least(a.id, b.id), greatest(a.id, b.id), a.id, 'accepted'
FROM (SELECT id, family, row_number() OVER (PARTITION BY family ORDER BY n) AS pos FROM demo_ghost) a
JOIN (SELECT id, family, row_number() OVER (PARTITION BY family ORDER BY n) AS pos FROM demo_ghost) b
  ON a.family = b.family AND b.pos BETWEEN a.pos + 1 AND a.pos + 3
ON CONFLICT DO NOTHING;

COMMIT;

-- Comprobación: debería dar 55, 15 y 40 (y el top 30 de Discover sale de esos 40).
SELECT
  (SELECT count(*) FROM users WHERE email LIKE 'demo-ghost-%@example.com') AS fantasmas,
  (SELECT count(*) FROM friendships f JOIN users v ON v.id IN (f.user_a_id, f.user_b_id)
    WHERE v.email = 'valen@gmail.com' AND f.status = 'accepted') AS amigos_de_valen,
  (SELECT count(*) FROM users g JOIN profiles p ON p.user_id = g.id
    WHERE g.email LIKE 'demo-ghost-%@example.com'
      AND p.study_code IN ('smr','asir','dam','daw','ing-informatica','ing-software','ing-computadores','ciberseguridad','ciencia-datos','ia','otros-informatica')
      AND NOT EXISTS (
        SELECT 1 FROM friendships f JOIN users v ON v.email = 'valen@gmail.com'
        WHERE (f.user_a_id, f.user_b_id) IN ((v.id, g.id), (g.id, v.id))
      )) AS candidatos_discover;

-- Para deshacerlo (el borrado de usuarios arrastra sus perfiles, temas y amistades):
--
--   DELETE FROM users WHERE email LIKE 'demo-ghost-%@example.com';
--   DELETE FROM user_skills WHERE user_id = (SELECT id FROM users WHERE email = 'valen@gmail.com');
--   UPDATE profiles SET study_code = NULL WHERE user_id = (SELECT id FROM users WHERE email = 'valen@gmail.com');
--   DELETE FROM skills WHERE id::text IN (
--     md5('peersync-demo-skill-algorithms')::uuid::text,
--     md5('peersync-demo-skill-databases')::uuid::text,
--     md5('peersync-demo-skill-machine learning')::uuid::text
--   );
