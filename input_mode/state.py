from typing import TypedDict, List, Dict, Any

class LogState(TypedDict):
    raw_input: str
    pending_items: List[Dict[str, Any]]
    approved_items: List[Dict[str, Any]]
    retry_count: int