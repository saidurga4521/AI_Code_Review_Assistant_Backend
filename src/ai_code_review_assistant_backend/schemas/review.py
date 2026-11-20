import datetime
from typing import Optional,List
from pydantic import Field,BaseModel

#1.Request body for triggering a PR Review
class ReviewCreateRequest(BaseModel):
  diff_text:str=Field(
    ...,
    description='The git diff to analyze',
    example="diff --git a/src/main.py b/src/main.py\n..."
  ),
  pr_number:Optional[int]=Field(None,example=42,description='Pull request Number')
  commit_sha:Optional[str]=Field(None,example='a1b2c3d4',description='Commit SHA')

#2.Schema for single finding 
class FindingResponse(BaseModel):
    id: int
    review_id: int
    file_path: str
    line_number: int
    severity: str
    category: str
    title: str
    description: str
    suggested_diff: Optional[str] = None
    evidence_snippet: Optional[str] = None
    created_at: datetime.datetime
    class Config:
        from_attributes = True

#3.Schema for a staged WriteAction(Human-in-the-loop)
class WriteActionResponse(BaseModel):
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

#4.Summary schema for listing PR reviews

class ReviewSummaryResponse(BaseModel):
    id:int
    repo_id: int
    pr_number: Optional[int] = None
    commit_sha: Optional[str] = None
    summary: str
    risk_level: str
    created_at: datetime.datetime
    class Config:
        from_attributes = True   

#5.Detailed Schema for a single PR Review including its findings
class ReviewDetailResponse(BaseModel):
    id: int
    repo_id: int
    pr_number: Optional[int] = None
    commit_sha: Optional[str] = None
    summary: str
    risk_level: str
    created_at: datetime.datetime
    findings: List[FindingResponse] = []
    class Config:
        from_attributes = True



