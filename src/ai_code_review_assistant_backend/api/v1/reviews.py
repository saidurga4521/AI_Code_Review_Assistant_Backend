from typing  import List,Any
from fastapi import APIRouter,Depends,status,HTTPException
from sqlalchemy.orm import Session

from ai_code_review_assistant_backend.schemas.review import ReviewDetailResponse,ReviewCreateRequest,ReviewSummaryResponse
from ai_code_review_assistant_backend.db.session import get_db
from ai_code_review_assistant_backend.db.models import Repository,PRReview
from ai_code_review_assistant_backend.services.review_service import review_pull_request

router=APIRouter(tags=['PR Reviews'])
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
  repo=db.query(Repository).filter(Repository.id == repo_id).first()
  if not repo:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Repository with ID {repo_id} not found"

    )

  try:
    review_result=review_pull_request(
      repo_id=repo_id,
      diff_text=request.diff_text,
      db=db,
      pr_number=request.pr_number,
      commit_sha=request.commit_sha
    )
  except Exception as e:
      raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing PR review: {str(e)}"
      )

  # fetch the newly created record with its findings populated
  review_record=db.query(PRReview).filter(PRReview.id == review_result['review_id']).first()
  return review_record

#2.GET /repositories/{repo_id}/reviews - List all the past reviews for a repo
@router.get(
   '/repositories/{repo_id}',
   response_model=List[ReviewSummaryResponse]
)
def list_repository_reviews(repo_id:int,db:Session=Depends(get_db)):
   """
   List all past pull requests reviews conducted for this repo
   """

   repo = db.query(Repository).filter(Repository.id == repo_id).first()
   if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository with ID {repo_id} not found"
        )

   results=db.query(PRReview).filter(PRReview.repo_id == repo_id).order_by(PRReview.created_at.desc()).all()
   return results

#3.GET /reviews/{review_id} -Get single review with all findings
@router.get('/reviews/{review_id}',response_model=ReviewDetailResponse)
def get_review_detail(review_id:int,db:Session=Depends(get_db)):
   """
   Retrieve full details of specific review,including all flagged findings
   """

   review=db.query(PRReview).filter(PRReview.id == review_id).first()
   if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID {review_id} not found"
        )
   return review
   