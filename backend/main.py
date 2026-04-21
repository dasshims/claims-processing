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
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotAction,
    CreateWorkspaceRequest,
    GenerateReportRequest,
    GenerateReportResponse,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    InferSchemaRequest,
    InferSchemaResponse,
    MappingSuggestion,
    NextActionsRequest,
    NextActionsResponse,
    ReadinessRequest,
    ReadinessResponse,
    UploadResponse,
    ValidateRequest,
    ValidateResponse,
    WorkspaceResponse,
)
from services.ai_service import ai_service
from services.readiness_service import assess_readiness
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


@app.post("/workspaces", response_model=WorkspaceResponse)
def create_workspace(payload: CreateWorkspaceRequest) -> WorkspaceResponse:
    workspace_id = str(uuid4())
    body = payload.model_dump()
    body["workspace_id"] = workspace_id
    store.add_workspace(workspace_id, body)
    return WorkspaceResponse(**body)


@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...), workspace_id: Optional[str] = None) -> UploadResponse:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        df = _read_uploaded_file(file, content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to parse file: {exc}") from exc

    file_id = str(uuid4())
    store.add_file(file_id, df)
    if workspace_id:
        store.attach_file_to_workspace(workspace_id, file_id)

    return UploadResponse(
        file_id=file_id,
        filename=file.filename or "uploaded_file",
        columns=[str(c) for c in df.columns.tolist()],
        sample_rows=df.head(10).where(pd.notna(df.head(10)), None).to_dict(orient="records"),
        row_count=len(df),
        workspace_id=workspace_id,
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


@app.post("/assess-readiness", response_model=ReadinessResponse)
def assess_data_readiness(payload: ReadinessRequest) -> ReadinessResponse:
    df = store.get_file(payload.file_id)
    if df is None:
        raise HTTPException(status_code=404, detail="file_id not found")
    readiness = assess_readiness(df)
    return ReadinessResponse(**readiness)


@app.post("/generate-report", response_model=GenerateReportResponse)
def generate_report(payload: GenerateReportRequest) -> GenerateReportResponse:
    workspace = store.get_workspace(payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="workspace_id not found")

    mapped_count = len([v for v in payload.mapping.values() if v])
    readiness = payload.readiness_score if payload.readiness_score is not None else 0
    errors = payload.validation_error_count if payload.validation_error_count is not None else 0

    if readiness >= 80 and errors == 0 and mapped_count >= 5:
        confidence = "high"
    elif readiness >= 55 and errors <= 10:
        confidence = "medium"
    else:
        confidence = "low"

    key_findings = [
        f"Workspace customer: {workspace.get('customer_name', 'N/A')}.",
        f"{mapped_count} columns are mapped to Daffodil schema.",
        f"Readiness score is {readiness} and validation errors are {errors}.",
    ]
    next_actions = [
        "Resolve remaining unmapped fields and rerun validation.",
        "Approve low-confidence mapping decisions in review queue.",
        "Run one dry-run ingestion before production go-live.",
    ]

    return GenerateReportResponse(
        title="Implementation Readiness Report",
        go_live_confidence=confidence,
        key_findings=key_findings,
        next_actions=next_actions,
    )


@app.post("/copilot-next-actions", response_model=NextActionsResponse)
def copilot_next_actions(payload: NextActionsRequest) -> NextActionsResponse:
    actions = []

    if not payload.file_id:
        actions.append(
            CopilotAction(
                id="a_upload_then_readiness",
                title="Assess readiness after first upload",
                reason="No file context yet, readiness cannot be calculated.",
                impact="Clarifies implementation risk early.",
                confidence=0.9,
                command="assess_readiness",
            )
        )
        return NextActionsResponse(
            summary="Upload is pending. Start with readiness to identify blockers.",
            actions=actions,
        )

    if payload.readiness_score is None:
        actions.append(
            CopilotAction(
                id="a_readiness",
                title="Run readiness assessment",
                reason="Readiness score is missing for this file.",
                impact="Identifies blockers before mapping effort.",
                confidence=0.93,
                command="assess_readiness",
            )
        )

    if (payload.unmapped_count or 0) > 0 or (payload.low_confidence_count or 0) > 0:
        actions.append(
            CopilotAction(
                id="a_infer",
                title="Run schema inference and review low-confidence fields",
                reason="There are unmapped or uncertain columns.",
                impact="Reduces manual mapping effort and review time.",
                confidence=0.89,
                command="infer_schema",
            )
        )
        actions.append(
            CopilotAction(
                id="a_accept_high",
                title="Auto-accept high-confidence mappings",
                reason="Confident mappings can be applied immediately.",
                impact="Speeds up onboarding while preserving manual review for risky fields.",
                confidence=0.85,
                command="accept_high_confidence",
            )
        )

    if payload.validation_error_count is None:
        actions.append(
            CopilotAction(
                id="a_validate",
                title="Run validation and clarification checks",
                reason="Validation has not been executed yet.",
                impact="Catches format/null/required-field issues before go-live.",
                confidence=0.95,
                command="run_validation",
            )
        )
    elif payload.validation_error_count > 0:
        actions.append(
            CopilotAction(
                id="a_revalidate",
                title="Fix mapping issues and re-run validation",
                reason=f"{payload.validation_error_count} validation errors remain.",
                impact="Improves go-live confidence and reduces post-launch failures.",
                confidence=0.91,
                command="run_validation",
            )
        )

    if (
        payload.readiness_score is not None
        and payload.readiness_score >= 55
        and (payload.validation_error_count or 0) <= 10
    ):
        actions.append(
            CopilotAction(
                id="a_report",
                title="Generate go-live report",
                reason="Enough signals are available for implementation decisioning.",
                impact="Provides leadership-ready summary and next actions.",
                confidence=0.88,
                command="generate_report",
            )
        )

    summary = "Top next steps generated from current onboarding signals."
    return NextActionsResponse(summary=summary, actions=actions[:5])


@app.post("/copilot-chat", response_model=CopilotChatResponse)
def copilot_chat(payload: CopilotChatRequest) -> CopilotChatResponse:
    context = {
        "workspace_id": payload.workspace_id,
        "file_id": payload.file_id,
        "readiness_score": payload.readiness_score,
        "validation_error_count": payload.validation_error_count,
        "unmapped_count": payload.unmapped_count,
        "low_confidence_count": payload.low_confidence_count,
        "columns": payload.columns or [],
        "sample_rows": (payload.sample_rows or [])[:5],
        "mapping": payload.mapping or {},
    }
    answer = ai_service.chat_about_data(context, [m.model_dump() for m in payload.messages])
    return CopilotChatResponse(answer=answer)
