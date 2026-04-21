import json
import logging
from typing import Any, Dict, List

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, STANDARD_SCHEMA

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

    def infer_schema(self, columns: List[str], sample_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.client:
            logger.warning("OPENAI_API_KEY not set. Falling back to heuristic inference.")
            return self._heuristic_infer(columns)

        prompt = (
            "Map source columns to a target schema with confidence scores. "
            "Only use these target fields: "
            f"{STANDARD_SCHEMA}. If unknown, use null target_field and low confidence."
        )

        schema = {
            "type": "object",
            "properties": {
                "suggestions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_column": {"type": "string"},
                            "target_field": {
                                "anyOf": [
                                    {"type": "string", "enum": STANDARD_SCHEMA},
                                    {"type": "null"},
                                ]
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                        "required": ["source_column", "target_field", "confidence"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["suggestions"],
            "additionalProperties": False,
        }

        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a precise data mapping assistant."},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "instruction": prompt,
                                "columns": columns,
                                "sample_rows": sample_rows,
                            }
                        ),
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "schema_mapping",
                        "schema": schema,
                        "strict": True,
                    },
                },
                temperature=0,
            )
            content = response.choices[0].message.content or "{}"
            payload = json.loads(content)
            return payload.get("suggestions", [])
        except Exception:
            logger.exception("AI schema inference failed, using heuristic fallback")
            return self._heuristic_infer(columns)

    def generate_yes_no_questions(self, low_confidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        questions = []
        for item in low_confidence:
            source = item.get("source_column")
            target = item.get("target_field")
            conf = float(item.get("confidence", 0.0))
            if source and target:
                questions.append(
                    {
                        "source_column": source,
                        "proposed_target": target,
                        "confidence": conf,
                        "question": f"Is '{source}' the {target}?",
                    }
                )
            elif source and not target:
                questions.append(
                    {
                        "source_column": source,
                        "proposed_target": "member_id",
                        "confidence": conf,
                        "question": (
                            f"We could not confidently map '{source}'. "
                            "Should this be mapped to member_id?"
                        ),
                    }
                )
        return questions

    def _heuristic_infer(self, columns: List[str]) -> List[Dict[str, Any]]:
        suggestions = []
        for col in columns:
            c = col.lower().strip()
            target = None
            confidence = 0.35
            if "member" in c or c in {"mem_id", "memberid", "mbr_id"}:
                target, confidence = "member_id", 0.85
            elif "claim" in c and ("id" in c or c.endswith("_id")):
                target, confidence = "claim_id", 0.82
            elif "amount" in c or ("claim" in c and "amt" in c):
                target, confidence = "claim_amount", 0.83
            elif "date" in c or "dos" in c or "service" in c:
                target, confidence = "date_of_service", 0.8
            elif "provider" in c and "id" in c:
                target, confidence = "provider_id", 0.88

            suggestions.append(
                {
                    "source_column": col,
                    "target_field": target,
                    "confidence": confidence,
                }
            )
        return suggestions

    def chat_about_data(self, context: Dict[str, Any], messages: List[Dict[str, str]]) -> str:
        if not messages:
            return "Ask me anything about your data, mappings, onboarding workflow, or next steps."

        user_message = messages[-1].get("content", "").lower()
        if not self.client:
            return self._heuristic_chat(user_message, context)

        try:
            prompt = (
                "You are a general-purpose operations copilot for Daffodil implementation teams. "
                "You can answer broad questions, but ground operational advice in provided context. "
                "Daffodil accepted schema is: "
                f"{STANDARD_SCHEMA}. "
                "If context is missing, say what is missing and suggest what to run/upload next. "
                "Keep answers concise and practical."
            )
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "system", "content": json.dumps(context)},
                    *messages,
                ],
                temperature=0.2,
            )
            return (response.choices[0].message.content or "").strip() or self._heuristic_chat(user_message, context)
        except Exception:
            logger.exception("Copilot chat failed, using heuristic fallback")
            return self._heuristic_chat(user_message, context)

    def _heuristic_chat(self, user_message: str, context: Dict[str, Any]) -> str:
        readiness = context.get("readiness_score")
        validation_errors = context.get("validation_error_count")
        unmapped = context.get("unmapped_count", 0)
        low_conf = context.get("low_confidence_count", 0)
        columns = context.get("columns", [])
        schema_text = ", ".join(STANDARD_SCHEMA)

        if "next" in user_message or "step" in user_message:
            steps = []
            if readiness is None:
                steps.append("run readiness assessment")
            if unmapped or low_conf:
                steps.append("review low-confidence mappings and accept high-confidence fields")
            if validation_errors is None or validation_errors > 0:
                steps.append("run validation and resolve remaining errors")
            steps.append("generate go-live report")
            return "Recommended next steps: " + ", then ".join(steps) + "."

        if "format" in user_message or "schema" in user_message or "daffodil" in user_message:
            return f"Daffodil accepted format is: {schema_text}."

        if "column" in user_message or "field" in user_message:
            if columns:
                return f"Current uploaded columns are: {', '.join(columns)}."
            return "No file columns are available yet. Upload a file so I can analyze fields."

        if "mapping" in user_message:
            return f"Current mapping health: {unmapped} unmapped fields and {low_conf} low-confidence fields."

        if "validation" in user_message or "error" in user_message:
            if validation_errors is None:
                return "Validation has not been run yet. Run validation to identify required-field, date, and numeric issues."
            return f"Validation currently shows {validation_errors} errors. Resolve those and rerun validation."

        if "readiness" in user_message:
            if readiness is None:
                return "Readiness score is not available yet. Run readiness assessment first."
            return f"Readiness score is {readiness}. Higher than 80 is generally go-live favorable."

        return (
            "I can help with data questions, Daffodil schema, mapping strategy, validation, readiness, and onboarding planning. "
            "Ask any question and I will use available context."
        )


ai_service = AIService()
