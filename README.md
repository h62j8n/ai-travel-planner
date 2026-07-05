# AI Travel Planner

- `frontend/` — Vue 3 + Vite + TypeScript
- `backend/` — Python + FastAPI (managed with [uv](https://docs.astral.sh/uv/))

## Local development

### Backend

```bash
cd backend
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

API runs at http://localhost:8000, docs at http://localhost:8000/docs.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

App runs at http://localhost:5173.

## Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000

## Deployment

Frontend and backend deploy separately.

### Backend → Render

`render.yaml` at the repo root defines a Blueprint that builds `backend/Dockerfile`.

1. In Render, "New +" → "Blueprint", point it at this repo.
2. Set the secret env vars it prompts for (not stored in the blueprint):
   - `OPENROUTER_API_KEY`
   - `OPENROUTER_MODEL` (optional, leave blank to use the fallback chain in `config.py`)
   - `CORS_ORIGINS` — JSON array string, e.g. `["https://your-app.vercel.app"]`
3. Health check is `/api/v1/health`. Note the resulting service URL (e.g. `https://ai-travel-planner-backend.onrender.com`).

Free plan spins down on idle — the first request after inactivity may take ~30–60s to wake up, on top of the AI generation call.

### Frontend → Vercel

1. Import this repo into Vercel, set **Root Directory** to `frontend`.
2. Framework preset: Vite (auto-detected). Build command / output directory are the Vite defaults.
3. Set the env var `VITE_API_BASE_URL` to `https://<your-render-backend-url>/api/v1`.
4. `frontend/vercel.json` adds the SPA rewrite needed for `vue-router`'s history mode.

After the first Vercel deploy, go back to Render and set `CORS_ORIGINS` to include that Vercel domain (and any preview domains you use), then redeploy the backend.
