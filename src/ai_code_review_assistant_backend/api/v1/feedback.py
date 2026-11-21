from typing import List
from fastapi import APIRouter,HTTPException,status,Depends
from sqlalchemy.orm import Session

from ai_code_review_assistant_backend.db.session import get_db
from ai_code_review_assistant_backend.db.models import DeveloperFeedback,ReviewFinding
from ai_code_review_assistant_backend.services.feedback_service import record_finding_feedback,get_repository_feedback_stats
from ai_code_review_assistant_backend.schemas.feedback import FeedbackResponse,FeedbackCreateRequest,FeedbackStatsResponse

router=APIRouter(
  tags=['Developer Feedback']
)

#1.Submit feedback on a finding
@router.post('/findings/{finding_id}/feedback',response_model=FeedbackResponse,status_code=status.HTTP_201_CREATED)
def submit_finding_feedback(finding_id:int,request:FeedbackCreateRequest,db:Session=Depends(get_db)):
  """
  Submit developer feedback on a specific finding
  """

  try:
    feedback=record_finding_feedback(
      finding_id=finding_id,
      is_useful=request.is_useful,
      db=db,
      reason=request.reason,
      comment=request.comment
    )

    return feedback
  except Exception as e:
    raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

#2.List all feedback for a specific finding
@router.get('/findings/{finding_id}/feedback',response_model=List[FeedbackResponse])
def get_finding_feedback(finding_id:int,db:Session=Depends(get_db)):
  """
  List all developer feedback for a specific finding
  """
  finding=db.query(ReviewFinding).filter(ReviewFinding.id == finding_id).first()
  if not finding:
    raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ReviewFinding with ID {finding_id} not found."
        )

  feedback_results=db.query(DeveloperFeedback).filter(DeveloperFeedback.finding_id == finding.id).all()
  return feedback_results


#3.Get Feedback stats of repo
@router.get('/repositories/{repo_id}/feedback_stats',response_model=FeedbackStatsResponse)
def get_repo_feedback_stats(repo_id:int,db:Session=Depends(get_db)):
  """
  Get Feedback stats for each repo
  """

  try:
    stats=get_repository_feedback_stats(
      repo_id=repo_id,
      db=db
    )
    return stats
  except Exception as e:
     raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

