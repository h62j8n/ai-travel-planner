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
