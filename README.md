---
title: Claims Onboarding
emoji: 📚
colorFrom: red
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# AI-Powered Data Onboarding Copilot

FastAPI backend + Next.js frontend for onboarding messy customer files into the Daffodil schema.

## Daffodil Accepted Schema
- member_id
- claim_id
- claim_amount
- date_of_service
- provider_id

## Project Structure
- `backend/` FastAPI APIs (`/upload`, `/infer-schema`, `/validate`, `/generate-questions`)
- `web/` Next.js UI

## Local Run
1. Install backend deps:

```bash
python3 -m pip install -r requirements.txt
```

2. Run both backend and frontend:

```bash
./run_app.sh
```

3. Open:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000/health`

## Environment Variables
- Backend:
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL` (optional, default `gpt-4o-mini`)
- Frontend/Next server:
  - `API_BASE_URL` (defaults to `http://127.0.0.1:8000`)

## Deploy Next.js Frontend
### Vercel
1. Import this repo in Vercel.
2. Set Root Directory to `web`.
3. Set env var `API_BASE_URL=https://<your-backend-url>`.
4. Deploy.

### Hugging Face Space (Docker)
This repo root Dockerfile runs both backend + Next.js app in one container.
Set secret `OPENAI_API_KEY` in Space settings.
