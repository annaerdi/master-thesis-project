from pydantic import BaseModel
from typing import Dict, List, Optional, Any

class AppContext(BaseModel):
    browser_sessions: Dict[str, Any] = {}
    playbook: List[dict] = []
    current_page_summary: str = ""
    last_interactive_elements: List[dict] = []
    user_goal: str = ""
