---
<<<<<<< HEAD
title: Claims Onboarding
emoji: 📚
colorFrom: red
colorTo: green
sdk: docker
pinned: false
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
=======
title: Daffodil Data Onboarding Copilot
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# AI-Powered Data Onboarding Copilot (MVP)

This project provides a full-stack MVP for onboarding messy customer data.

## Features
- Upload CSV/Excel files
- AI schema inference to standard schema
- Editable mapping UI
- Data validation for required fields, nulls, date and number formats
- AI-generated yes/no clarification questions for low-confidence mappings
- Dashboard workflow status

## Standard Schema
- member_id
- claim_id
- claim_amount
- date_of_service
- provider_id

## Project Structure
- `backend/main.py` - FastAPI app + routes
- `backend/services/ai_service.py` - OpenAI schema inference + question generation
- `backend/services/validation_service.py` - validation rules
- `frontend/app.py` - Streamlit workflow UI

## Run
1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start backend:

```bash
cd backend
uvicorn main:app --reload
```

3. Start frontend:

```bash
cd frontend
streamlit run app.py
```

## Environment Variables
- `OPENAI_API_KEY` (optional, enables AI inference; otherwise heuristic fallback is used)
- `OPENAI_MODEL` (optional, defaults to `gpt-4o-mini`)
- `API_BASE` (frontend only, defaults to `http://localhost:8000`)

## API Endpoints
- `POST /upload`
- `POST /infer-schema`
- `POST /validate`
- `POST /generate-questions`
- `GET /health`

## Deploy Online (Docker on Railway)
Recommended setup:
- Railway service 1: backend (`backend/Dockerfile`)
- Railway service 2: frontend (`frontend/Dockerfile`)

### 1) Push this repo to GitHub
Railway deploys from your GitHub repo.

### 2) Create backend service on Railway
1. In Railway, click `New Project` -> `Deploy from GitHub repo`.
2. Select this repo.
3. Open service settings and set:
   - `Root Directory`: `backend`
   - `Builder`: `Dockerfile`
4. Add environment variables:
   - `OPENAI_API_KEY` = your key
   - `OPENAI_MODEL` = `gpt-4o-mini` (optional)
5. Deploy and copy the generated public backend URL.
6. Verify: `https://<backend-url>/health`.

### 3) Create frontend service on Railway
1. In the same Railway project, click `New` -> `GitHub Repo` and pick the same repo.
2. In service settings, set:
   - `Root Directory`: `frontend`
   - `Builder`: `Dockerfile`
3. Add environment variable:
   - `API_BASE` = `https://<backend-url>`
4. Deploy and open the frontend URL.

### 4) CORS
Backend currently allows all origins for MVP speed. For production hardening, restrict `allow_origins` in [main.py](/Users/hims/git/daffodil-customer-agent/backend/main.py).

## Deployment Files
- [backend/Dockerfile](/Users/hims/git/daffodil-customer-agent/backend/Dockerfile): backend container
- [frontend/Dockerfile](/Users/hims/git/daffodil-customer-agent/frontend/Dockerfile): frontend container
- [docker-compose.yml](/Users/hims/git/daffodil-customer-agent/docker-compose.yml): local Docker run for both services
- [backend/requirements.txt](/Users/hims/git/daffodil-customer-agent/backend/requirements.txt): backend-only dependencies
- [frontend/requirements.txt](/Users/hims/git/daffodil-customer-agent/frontend/requirements.txt): frontend-only dependencies
>>>>>>> 9dba780 (Deploy to Hugging Face Space (Docker))
