from pydantic import BaseModel, Field
from typing import Optional



#TODO: refactor in a single knowledge1-knowlege2 relationship which can be tested on either side. The LLM has to decipher the information to test itself

class CitationSubject(BaseModel):
    subject: str = Field(description="The core subject or theme of the citation.")

class CommandGoal(BaseModel):
    main_goal: str = Field(description="The primary action or goal the command achieves.")

class GradeEvaluation(BaseModel):
    grade: int = Field(description="An integer from 1 to 4 based on the strict grading rubric.")
    feedback: str = Field(description="Justification for the grade assigned.")
