import os
from typing import Dict, List, Optional

import pandas as pd
import requests
import streamlit as st

STANDARD_SCHEMA = [
    "member_id",
    "claim_id",
    "claim_amount",
    "date_of_service",
    "provider_id",
]

st.set_page_config(page_title="Data Onboarding Copilot", layout="wide")
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
st.title("AI-Powered Data Onboarding Copilot")


def init_state() -> None:
    defaults = {
        "file_id": None,
        "columns": [],
        "sample_rows": [],
        "mapping": {},
        "suggestions": [],
        "validation": None,
        "questions": [],
        "q_index": 0,
        "upload_done": False,
        "infer_done": False,
        "validate_done": False,
        "complete": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def dashboard() -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Upload", "Done" if st.session_state.upload_done else "Pending")
    c2.metric("Mapping", "Done" if st.session_state.infer_done else "Pending")
    c3.metric("Validation", "Done" if st.session_state.validate_done else "Pending")
    c4.metric("Completion", "Done" if st.session_state.complete else "Pending")


def upload_step() -> None:
    st.subheader("1) Upload File")
    file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    if file and st.button("Parse File"):
        files = {"file": (file.name, file.getvalue(), file.type or "application/octet-stream")}
        res = requests.post(f"{API_BASE}/upload", files=files, timeout=60)
        if res.ok:
            data = res.json()
            st.session_state.file_id = data["file_id"]
            st.session_state.columns = data["columns"]
            st.session_state.sample_rows = data["sample_rows"]
            st.session_state.upload_done = True
            st.success(f"Uploaded {data['filename']} with {data['row_count']} rows")
            if data["sample_rows"]:
                st.dataframe(pd.DataFrame(data["sample_rows"]))
        else:
            st.error(f"Upload failed: {res.text}")


def infer_step() -> None:
    if not st.session_state.upload_done:
        return

    st.subheader("2) Infer Schema")
    if st.button("Run AI Schema Inference"):
        payload = {
            "columns": st.session_state.columns,
            "sample_rows": st.session_state.sample_rows,
        }
        res = requests.post(f"{API_BASE}/infer-schema", json=payload, timeout=120)
        if res.ok:
            suggestions = res.json()["suggestions"]
            st.session_state.suggestions = suggestions
            st.session_state.mapping = {
                s["source_column"]: s.get("target_field") for s in suggestions
            }
            st.session_state.infer_done = True
            st.success("Inference complete")
        else:
            st.error(f"Inference failed: {res.text}")

    if st.session_state.infer_done:
        st.write("Suggested mappings (editable)")
        mapping: Dict[str, Optional[str]] = st.session_state.mapping
        for col in st.session_state.columns:
            current = mapping.get(col)
            options = ["(unmapped)"] + STANDARD_SCHEMA
            idx = options.index(current) if current in options else 0
            selected = st.selectbox(
                f"{col}",
                options,
                index=idx,
                key=f"map_{col}",
            )
            st.session_state.mapping[col] = None if selected == "(unmapped)" else selected


def validate_step() -> None:
    if not st.session_state.infer_done:
        return

    st.subheader("3) Validate Data")
    if st.button("Run Validation"):
        payload = {
            "file_id": st.session_state.file_id,
            "mapping": st.session_state.mapping,
        }
        res = requests.post(f"{API_BASE}/validate", json=payload, timeout=120)
        if res.ok:
            st.session_state.validation = res.json()
            st.session_state.validate_done = True
            st.session_state.complete = st.session_state.validation["valid"]
        else:
            st.error(f"Validation failed: {res.text}")

    if st.session_state.validation:
        v = st.session_state.validation
        st.write(f"Valid: `{v['valid']}` | Total errors: `{v['total_errors']}`")
        if v["errors"]:
            st.dataframe(pd.DataFrame(v["errors"]).head(100))


def question_step() -> None:
    if not st.session_state.validate_done:
        return

    st.subheader("4) Clarification Questions")
    if st.button("Generate Yes/No Questions"):
        payload = {"suggestions": st.session_state.suggestions}
        res = requests.post(f"{API_BASE}/generate-questions", json=payload, timeout=60)
        if res.ok:
            st.session_state.questions = res.json()["questions"]
            st.session_state.q_index = 0
        else:
            st.error(f"Question generation failed: {res.text}")

    questions: List[Dict] = st.session_state.questions
    idx = st.session_state.q_index
    if questions and idx < len(questions):
        q = questions[idx]
        st.info(q["question"])
        c1, c2 = st.columns(2)
        if c1.button("Yes", key=f"yes_{idx}"):
            st.session_state.mapping[q["source_column"]] = q["proposed_target"]
            st.session_state.q_index += 1
        if c2.button("No", key=f"no_{idx}"):
            st.session_state.mapping[q["source_column"]] = None
            st.session_state.q_index += 1
    elif questions:
        st.success("All questions answered. Re-run validation to confirm final dataset quality.")


def completion_step() -> None:
    st.subheader("5) Final Output")
    if st.session_state.complete:
        st.success("Dataset is fully validated and onboarding is complete.")
    else:
        st.warning("Complete validations and clarifications to finish onboarding.")


init_state()
dashboard()
upload_step()
infer_step()
validate_step()
question_step()
completion_step()
