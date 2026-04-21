import hashlib
import logging
from io import BytesIO
from typing import Dict, Optional
from uuid import uuid4

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from config import STANDARD_SCHEMA
from models import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    InferSchemaRequest,
    InferSchemaResponse,
    MappingSuggestion,
    UploadResponse,
    ValidateRequest,
    ValidateResponse,
)
from services.ai_service import ai_service
from services.validation_service import validate_dataframe
from storage import store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Onboarding Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_uploaded_file(uploaded: UploadFile, content: bytes) -> pd.DataFrame:
    filename = (uploaded.filename or "").lower()
    if filename.endswith(".csv"):
        return pd.read_csv(BytesIO(content))
    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        return pd.read_excel(BytesIO(content))
    raise HTTPException(status_code=400, detail="Unsupported file type. Use CSV or Excel.")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        df = _read_uploaded_file(file, content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to parse file: {exc}") from exc

    file_id = str(uuid4())
    store.add_file(file_id, df)

    return UploadResponse(
        file_id=file_id,
        filename=file.filename or "uploaded_file",
        columns=[str(c) for c in df.columns.tolist()],
        sample_rows=df.head(10).where(pd.notna(df.head(10)), None).to_dict(orient="records"),
        row_count=len(df),
    )


@app.post("/infer-schema", response_model=InferSchemaResponse)
def infer_schema(payload: InferSchemaRequest) -> InferSchemaResponse:
    logger.info("Inferring schema for %d columns", len(payload.columns))

    signature = hashlib.sha1("|".join(sorted(payload.columns)).encode("utf-8")).hexdigest()
    reused = store.get_mapping(signature)
    if reused:
        suggestions = [
            MappingSuggestion(source_column=src, target_field=tgt, confidence=0.95)
            for src, tgt in reused.items()
        ]
        return InferSchemaResponse(suggestions=suggestions)

    raw_suggestions = ai_service.infer_schema(payload.columns, payload.sample_rows)

    mapped: Dict[str, Optional[str]] = {}
    suggestions = []
    for col in payload.columns:
        hit = next((s for s in raw_suggestions if s.get("source_column") == col), None)
        target = hit.get("target_field") if hit else None
        confidence = float(hit.get("confidence", 0.0)) if hit else 0.0
        if target not in STANDARD_SCHEMA:
            target = None
            confidence = min(confidence, 0.3)
        mapped[col] = target
        suggestions.append(MappingSuggestion(source_column=col, target_field=target, confidence=confidence))

    clean = {k: v for k, v in mapped.items() if v}
    if clean:
        store.save_mapping(signature, clean)

    return InferSchemaResponse(suggestions=suggestions)


@app.post("/validate", response_model=ValidateResponse)
def validate(payload: ValidateRequest) -> ValidateResponse:
    df = store.get_file(payload.file_id)
    if df is None:
        raise HTTPException(status_code=404, detail="file_id not found")

    missing_source_cols = [src for src in payload.mapping.keys() if src not in df.columns]
    if missing_source_cols:
        raise HTTPException(status_code=400, detail=f"Unknown source columns: {missing_source_cols}")

    errors = validate_dataframe(df, payload.mapping)

    return ValidateResponse(valid=len(errors) == 0, total_errors=len(errors), errors=errors)


@app.post("/generate-questions", response_model=GenerateQuestionsResponse)
def generate_questions(payload: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
    low_conf = [
        s.model_dump()
        for s in payload.suggestions
        if s.confidence < 0.9 or s.target_field is None
    ]
    questions = ai_service.generate_yes_no_questions(low_conf)
    return GenerateQuestionsResponse(questions=questions)
