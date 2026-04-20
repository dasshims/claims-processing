from typing import Dict, Optional

import pandas as pd


class InMemoryStore:
    def __init__(self) -> None:
        self.files: Dict[str, pd.DataFrame] = {}
        self.mappings_by_signature: Dict[str, Dict[str, str]] = {}

    def add_file(self, file_id: str, df: pd.DataFrame) -> None:
        self.files[file_id] = df

    def get_file(self, file_id: str) -> Optional[pd.DataFrame]:
        return self.files.get(file_id)

    def save_mapping(self, signature: str, mapping: Dict[str, str]) -> None:
        self.mappings_by_signature[signature] = mapping

    def get_mapping(self, signature: str) -> Optional[Dict[str, str]]:
        return self.mappings_by_signature.get(signature)


store = InMemoryStore()
