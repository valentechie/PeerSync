# PeerSync

PeerSync is a web app for private, invitation-only study rooms where students learn from each other, without needing an expert in the room. It was built for Hack4Edu 2026, for the challenge on AI applied to peer learning.

<!-- Add an image here, for example: ![PeerSync study room](docs/screenshot.png) -->

## The idea

Most AI study tools replace the conversation between students with a conversation with a chatbot. PeerSync does the opposite: the AI supports a conversation between peers, and the people in the room do the thinking, arguing and explaining.

Three rules shape the product:

- **Peers come first.** Human review always happens before automated feedback.
- **Students think for themselves first.** In Contrasta, individual answers stay hidden on the server until the individual phase is complete.
- **Help is on demand.** StudyMind only gives hints when someone asks. It never infers that a student is stuck from silence or from their camera.

## Features

### Study rooms

The room is the center of the app. Only people with an invitation or an invite link can join, and only participants can see what happens inside. Each room has a shared chat with attachments, and the AI tools below are built into that conversation.

- **Contrasta** is the main path through a room. Two students answer a question on their own, then compare and discuss their answers as a pair.
- **StudyMind** gives graduated hints when students ask for them.
- **TeachBack** lets a student explain a concept to their peers. Classmates review the explanation first, and formative AI feedback comes after.

### Finding people

- **Friends:** search for people, send requests and see which rooms your friends are in.
- **Learn:** list the topics you want to learn and find people who want to learn the same things.
- **Classmates:** find people on the same or similar studies, across both vocational training and university.
- **My network and Discover:** interactive graphs of your friends and of suggested connections.

Compatibility is calculated with deterministic rules, not by an AI model, so every result is reproducible and comes with the reasons behind it. To protect privacy, the graphs never reveal who other people are friends with. The lines between people come only from what you can already see: studies, shared topics and your own rooms.

### Practice

A separate space for practicing a topic one-on-one with AI, outside the rooms.

## Tech stack

| Area | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL (Supabase) |
| AI | DeepSeek for the rooms, Gemini for Practice |

AI providers are called only from the backend, never from the browser.

## Project structure

```text
backend/    FastAPI app, database migrations and tests
frontend/   React web app
database/   SQL schema
docs/       API reference, database design and Contrasta specification
```

The full API reference is in [docs/api-documentation.md](docs/api-documentation.md). With the backend running, interactive documentation is available at `/docs`.

## Local development

Backend:

```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
cp .env.example .env   # then fill in the values
.venv/bin/uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend && npm install
cp .env.example .env
npm run dev
```

Run the backend tests from the repository root:

```bash
npm test
```

## Deployment

The web app and the API are deployed separately. GitHub Pages only serves static files, so the FastAPI API and the database need their own server.

### Web app on GitHub Pages

`.github/workflows/deploy-pages.yml` builds `frontend/` and publishes `frontend/dist` on every push to `main` that changes the frontend.

1. In **Settings > Pages**, choose **GitHub Actions** as the source.
2. In **Settings > Secrets and variables > Actions > Variables**, create `VITE_API_BASE_URL` with the public address of the API, ending in `/api`. This value is public, so never put keys in `VITE_` variables.
3. Run the workflow from **Actions**, or push to `main`.

The site is published at `https://USERNAME.github.io/REPOSITORY-NAME/`.

### API

Any server with Python can run it from `backend/`:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment variables:

1. `DATABASE_URL`: the Supabase connection string. On a stateless server, use the **Transaction pooler** (port `6543`).
2. `CORS_ORIGINS`: the origin of the web app, without a path, for example `https://USERNAME.github.io`.
3. `JWT_SECRET`: a long secret of your own.
4. `DEEPSEEK_API_KEY`: for the AI in the rooms (Contrasta, StudyMind and TeachBack). Without it, rooms keep working: the Contrasta and StudyMind panels show prepared questions, labeled as such, and the pair flow shows an error that can be retried. TeachBack reports that it cannot give suggestions.
5. `GEMINI_API_KEY`: for the Practice section. Without it, that section reports that it is not configured.
6. `TRUST_FORWARDED_FOR=1`: only if a proxy of your own overwrites `X-Forwarded-For`.

**Demo mode:** login does not check credentials, so anyone can sign in as any user. Do not use it with real data.

Migrations do not run on deployment. Run them locally before publishing a schema change, using the direct connection or the session pooler (port `5432`):

```bash
cd backend && .venv/bin/alembic upgrade head
```
