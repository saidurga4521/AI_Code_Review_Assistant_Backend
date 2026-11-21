import datetime
from typing import Optional
from pydantic import BaseModel, Field


# 1. Request Body when a human approves or rejects an action
class ActionResolveRequest(BaseModel):
    resolved_by: str = Field(
        ...,
        example="alice@company.com",
        description="Username or email of the engineer reviewing this action"
    )
    comment: Optional[str] = Field(
        None,
        example="Patch verified and tested locally",
        description="Optional justification or feedback"
    )


# 2. Standard Response Body for an action
class ActionResponse(BaseModel):
    id: int
    finding_id: Optional[int] = None
    action_type: str
    payload: Optional[str] = None
    status: str
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# 3. Rich Schema for pending actions (includes finding context like file and line)
class PendingActionDetailResponse(BaseModel):
    id: int
    finding_id: Optional[int] = None
    action_type: str
    payload: Optional[str] = None
    status: str
    created_at: datetime.datetime
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    finding_title: Optional[str] = None
    severity: Optional[str] = None

    class Config:
        from_attributes = True