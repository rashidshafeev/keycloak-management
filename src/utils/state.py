# src/utils/state.py
from pathlib import Path
import json
from typing import Dict, Any

class DeploymentState:
    def __init__(self, state_file: Path = Path("/opt/fawz/keycloak/state.json")):
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {"completed_stages": [], "current_stage": None}
    
    def _save_state(self):
        self.state_file.write_text(json.dumps(self.state, indent=2))
    
    def mark_completed(self, stage: str):
        if stage not in self.state["completed_stages"]:
            self.state["completed_stages"].append(stage)
            self._save_state()
    
    def set_current_stage(self, stage: str):
        self.state["current_stage"] = stage
        self._save_state()
    
    def is_completed(self, stage: str) -> bool:
        return stage in self.state["completed_stages"]
