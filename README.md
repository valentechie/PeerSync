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

## Despliegue en Vercel

`vercel.json` despliega frontend y API en un solo proyecto: `/api/*` va a FastAPI (`backend/index.py`) y el resto a la web de Vite. Usa `builds`, así que Vercel ignora el preset y los comandos del panel.

1. Importa el repositorio en Vercel y deja **Root Directory** en la raíz.
2. Añade la variable de entorno `DATABASE_URL`, con la cadena **Transaction pooler** de Supabase (puerto `6543`). La URL del proyecto y la clave publicable son públicas y ya vienen por defecto en el código.
3. En Supabase, entra en **Authentication → URL Configuration** y pon el dominio de producción en **Site URL** y `https://TU-DOMINIO/login` en **Redirect URLs**. Añade también `http://localhost:5173/login` para desarrollo.

Supabase exige confirmar el correo al registrarse, y su servidor de correo integrado admite muy pocos envíos por hora. Para producción, configura un SMTP propio o desactiva **Confirm email** en **Authentication → Sign In / Providers**

Las migraciones no se ejecutan al desplegar. Lánzalas en local antes de publicar un cambio de esquema, con la conexión directa o el pooler de sesión (puerto `5432`):

```bash
cd backend && .venv/bin/alembic upgrade head
```
