from typing import TypedDict, List

class LogState(TypedDict):
    raw_input: str
    pending_facts: List[str]
    approved_facts: List[str]
    retry_count: int