from dataclasses import dataclass
from typing import Dict, List
from playwright.async_api import Page

@dataclass
class AppContext:
    browser_sessions: Dict[str, Page]
    playbook: List[dict]
