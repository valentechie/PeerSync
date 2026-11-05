# PeerSync

## Desarrollo local

```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
cp .env.example .env   # y rellena los valores
.venv/bin/uvicorn app.main:app --reload
```

```bash
cd frontend && npm install
cp .env.example .env
npm run dev
```

## Despliegue

La web y la API se despliegan por separado. GitHub Pages solo sirve archivos estáticos, así que la API FastAPI y la base de datos necesitan su propio servidor.

### Web en GitHub Pages

`.github/workflows/deploy-pages.yml` compila `frontend/` y publica `frontend/dist` en cada push a `main` que cambie el frontend.

1. En **Settings → Pages**, elige **GitHub Actions** como origen.
2. En **Settings → Secrets and variables → Actions → Variables**, crea `VITE_API_BASE_URL` con la dirección pública de la API, terminada en `/api`. Es pública: nunca pongas claves en variables `VITE_`.
3. Lanza el flujo desde **Actions** o haz push a `main`.

La web queda en `https://USUARIO.github.io/NOMBRE-DEL-REPOSITORIO/`.

### API

Cualquier servidor con Python puede ejecutarla desde `backend/`:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Variables de entorno:

1. `DATABASE_URL`: la cadena de conexión de Supabase. En un servidor sin estado, usa el **Transaction pooler** (puerto `6543`).
2. `CORS_ORIGINS`: el origen de la web, sin ruta, por ejemplo `https://USUARIO.github.io`.
3. `JWT_SECRET`: un secreto largo y propio.
4. `DEEPSEEK_API_KEY`: para la IA de la sala (Contrasta, StudyMind y TeachBack). Sin ella, la sala sigue funcionando: Contrasta y StudyMind muestran en sus paneles preguntas preparadas, identificadas como tal, y el recorrido por parejas muestra un error que se puede reintentar. TeachBack avisa de que no puede dar sugerencias.
5. `GEMINI_API_KEY`: para el apartado Practicar. Sin ella, ese apartado avisa de que no está configurado.
6. `TRUST_FORWARDED_FOR=1`: solo si un proxy propio sobrescribe `X-Forwarded-For`.

**Modo demo:** el login no comprueba credenciales, así que cualquiera puede entrar como cualquier usuario. No lo uses con datos reales.

Las migraciones no se ejecutan al desplegar. Lánzalas en local antes de publicar un cambio de esquema, con la conexión directa o el pooler de sesión (puerto `5432`):

```bash
cd backend && .venv/bin/alembic upgrade head
```
