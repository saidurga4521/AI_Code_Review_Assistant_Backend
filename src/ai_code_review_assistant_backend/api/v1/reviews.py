from typing  import List,Any
from fastapi import APIRouter,Depends,status,HTTPException
from sqlalchemy.orm import Session

from ai_code_review_assistant_backend.schemas.review import ReviewDetailResponse,ReviewCreateRequest
from ai_code_review_assistant_backend.db.session import get_db

router=APIRouter(tages=['PR Reviews'])
#1.POST /repositories/{repo_id}/review -Trigger a code review

@router.post(
  '/repositories/{repo_id}/review',
  response_model=ReviewDetailResponse,
  status_code=status.HTTP_201_CREATED
)
def trigger_pull_request_review(repo_id:int,request:ReviewCreateRequest,db:Session=Depends(get_db)):
  """
  Submit a Git Diff to be audited by AI Review Assistant
  Evalutes BUG_RISK,SECURITY,MISSING_TESTS and Architecture
  Saves findings
  """
  repo=db.query