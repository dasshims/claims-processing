import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

STANDARD_SCHEMA = [
    "member_id",
    "claim_id",
    "claim_amount",
    "date_of_service",
    "provider_id",
]

REQUIRED_STANDARD_FIELDS = STANDARD_SCHEMA.copy()
