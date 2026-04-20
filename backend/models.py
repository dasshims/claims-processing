from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    columns: List[str]
    sample_rows: List[Dict[str, Any]]
    row_count: int


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
