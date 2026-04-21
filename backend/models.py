from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    columns: List[str]
    sample_rows: List[Dict[str, Any]]
    row_count: int
    workspace_id: Optional[str] = None


class CreateWorkspaceRequest(BaseModel):
    customer_name: str
    integration_type: str
    target_go_live_date: Optional[str] = None
    owner: str


class WorkspaceResponse(BaseModel):
    workspace_id: str
    customer_name: str
    integration_type: str
    target_go_live_date: Optional[str] = None
    owner: str
    file_id: Optional[str] = None


class InferSchemaRequest(BaseModel):
    columns: List[str]
    sample_rows: List[Dict[str, Any]]


class MappingSuggestion(BaseModel):
    source_column: str
    target_field: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class InferSchemaResponse(BaseModel):
    suggestions: List[MappingSuggestion]


class ValidateRequest(BaseModel):
    file_id: str
    mapping: Dict[str, Optional[str]]


class ValidationErrorItem(BaseModel):
    row_index: Optional[int] = None
    source_column: Optional[str] = None
    target_field: str
    error_type: Literal["missing_required_field", "null_value", "invalid_date", "invalid_number"]
    message: str


class ValidateResponse(BaseModel):
    valid: bool
    total_errors: int
    errors: List[ValidationErrorItem]


class GenerateQuestionsRequest(BaseModel):
    suggestions: List[MappingSuggestion]


class QuestionItem(BaseModel):
    source_column: str
    proposed_target: str
    confidence: float
    question: str


class GenerateQuestionsResponse(BaseModel):
    questions: List[QuestionItem]


class ReadinessRequest(BaseModel):
    file_id: str


class ReadinessBlocker(BaseModel):
    code: str
    message: str
    severity: Literal["high", "medium", "low"]


class ReadinessResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    status: Literal["ready", "at_risk", "blocked"]
    blockers: List[ReadinessBlocker]
    summary: str


class GenerateReportRequest(BaseModel):
    workspace_id: str
    mapping: Dict[str, Optional[str]]
    readiness_score: Optional[int] = None
    validation_error_count: Optional[int] = None


class GenerateReportResponse(BaseModel):
    title: str
    go_live_confidence: Literal["high", "medium", "low"]
    key_findings: List[str]
    next_actions: List[str]


class NextActionsRequest(BaseModel):
    workspace_id: Optional[str] = None
    file_id: Optional[str] = None
    readiness_score: Optional[int] = None
    validation_error_count: Optional[int] = None
    unmapped_count: Optional[int] = None
    low_confidence_count: Optional[int] = None


class CopilotAction(BaseModel):
    id: str
    title: str
    reason: str
    impact: str
    confidence: float = Field(ge=0.0, le=1.0)
    command: Literal[
        "assess_readiness",
        "infer_schema",
        "accept_high_confidence",
        "run_validation",
        "generate_report",
    ]


class NextActionsResponse(BaseModel):
    summary: str
    actions: List[CopilotAction]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class CopilotChatRequest(BaseModel):
    workspace_id: Optional[str] = None
    file_id: Optional[str] = None
    readiness_score: Optional[int] = None
    validation_error_count: Optional[int] = None
    unmapped_count: Optional[int] = None
    low_confidence_count: Optional[int] = None
    columns: Optional[List[str]] = None
    sample_rows: Optional[List[Dict[str, Any]]] = None
    mapping: Optional[Dict[str, Optional[str]]] = None
    messages: List[ChatMessage]


class CopilotChatResponse(BaseModel):
    answer: str
