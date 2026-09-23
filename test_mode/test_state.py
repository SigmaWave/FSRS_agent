from typing import TypedDict, List, Dict, Any, Optional

class TestItem(TypedDict):
    # Database fields
    id: int
    category: str
    quote: Optional[str]
    author: Optional[str]
    event: Optional[str]
    date: Optional[str]
    command: Optional[str]
    description: Optional[str]
    
    # FSRS fields
    stability: Optional[float]
    difficulty: Optional[float]
    
    # Pipeline generated fields
    query: Optional[str]
    user_answer: Optional[str]
    grade: Optional[int]
    feedback: Optional[str]

class TestState(TypedDict):
    items_to_review: List[TestItem]
    is_initial_pass: bool
