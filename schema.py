from typing import TypedDict, List
from pydantic import BaseModel, Field

class ExtractedFacts(BaseModel):
    facts: List[str] = Field(
        description="A list of standalone, atomic facts extracted from the text."
    )