# MindMate

AI programming tutor for C++ and DSA: **Assess → Identify → Teach → Practice → Verify mastery**.

- `backend/` FastAPI + SQLAlchemy (SQLite by default, Postgres/Supabase via `DATABASE_URL`)
- `frontend/` React + Vite + Tailwind

## Run locally
```bash
# terminal 1
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
# terminal 2
cd frontend && npm install && npm run dev      # http://localhost:5173
```
Optional AI tutor (works fine without it): copy `backend/.env.example` to `backend/.env` and set `ANTHROPIC_API_KEY`.

## Test
```bash
cd backend && pytest
```
