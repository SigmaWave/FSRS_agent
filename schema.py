from pydantic import BaseModel, Field
from typing import List, Optional

class ParsedItem(BaseModel):
    category: str = Field(description="Must be exactly one of: 'citation', 'date', 'coding', or 'unknown'")
    quote: Optional[str] = Field(default=None, description="The quote text if category is citation")
    author: Optional[str] = Field(default=None, description="The author if category is citation")
    event: Optional[str] = Field(default=None, description="The event name if category is date")
    date: Optional[str] = Field(default=None, description="The date if category is date")
    command: Optional[str] = Field(default=None, description="The command if category is coding")
    description: Optional[str] = Field(default=None, description="The description if category is coding")
    text: Optional[str] = Field(default=None, description="The raw text if category is unknown")

class ExtractedData(BaseModel):
    items: List[ParsedItem] = Field(description="List of items extracted from the text.")

class CategoryVerdict(BaseModel):
    is_correct: bool = Field(
        description="True if the category matches the extracted fields correctly. False if fields are mismatched or categorized incorrectly."
    )
    reason: str = Field(
        description="Concise reason why the extraction is correct or how it failed."
    )