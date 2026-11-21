import datetime
from typing import Optional
from pydantic import BaseModel, Field


# 1. Request Body for submitting feedback on a finding
class FeedbackCreateRequest(BaseModel):
    is_useful: bool = Field(
        ...,
        example=True,
        description="Whether the finding was useful (True) or a false positive (False)"
    )
    reason: Optional[str] = Field(
        None,
        example="ACCURATE_FIX",
        description="Categorical reason: ACCURATE_FIX, FALSE_POSITIVE, INTENTIONAL_DESIGN, or IRRELEVANT"
    )
    comment: Optional[str] = Field(
        None,
        example="Caught a critical injection vulnerability before merge.",
        description="Optional developer notes"
    )


# 2. Standard Response for recorded feedback
class FeedbackResponse(BaseModel):
    id: int
    finding_id: int
    is_useful: bool
    reason: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# 3. Aggregated Accuracy Stats for a Repository
class FeedbackStatsResponse(BaseModel):
    repo_id: int
    total_feedback: int
    useful_count: int
    false_positive_count: int
    precision_rate_percentage: float