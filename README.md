---
title: Claims Onboarding
emoji: 📚
colorFrom: red
colorTo: green
sdk: docker
app_port: 7860
pinned: false
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
