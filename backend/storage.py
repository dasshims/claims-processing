from typing import Dict, Optional

import pandas as pd


class InMemoryStore:
    def __init__(self) -> None:
        self.files: Dict[str, pd.DataFrame] = {}
        self.mappings_by_signature: Dict[str, Dict[str, str]] = {}
        self.workspaces: Dict[str, Dict[str, str]] = {}

    def add_file(self, file_id: str, df: pd.DataFrame) -> None:
        self.files[file_id] = df

    def get_file(self, file_id: str) -> Optional[pd.DataFrame]:
        return self.files.get(file_id)

    def save_mapping(self, signature: str, mapping: Dict[str, str]) -> None:
        self.mappings_by_signature[signature] = mapping

    def get_mapping(self, signature: str) -> Optional[Dict[str, str]]:
        return self.mappings_by_signature.get(signature)

    def add_workspace(self, workspace_id: str, payload: Dict[str, str]) -> None:
        self.workspaces[workspace_id] = payload

    def get_workspace(self, workspace_id: str) -> Optional[Dict[str, str]]:
        return self.workspaces.get(workspace_id)

    def attach_file_to_workspace(self, workspace_id: str, file_id: str) -> None:
        if workspace_id in self.workspaces:
            self.workspaces[workspace_id]["file_id"] = file_id


store = InMemoryStore()
