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


ai_service = AIService()
