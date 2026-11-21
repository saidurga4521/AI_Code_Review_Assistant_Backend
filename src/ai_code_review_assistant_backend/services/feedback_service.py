from typing import Optional,Dict,Any
from sqlalchemy.orm import Session

from ai_code_review_assistant_backend.db.models import (
  DeveloperFeedback,
  PRReview,
  ReviewFinding,
  Repository
)

def record_finding_feedback(finding_id :int,is_useful:bool,db:Session,reason:Optional[str]=None,comment:Optional[str]=None)->DeveloperFeedback:
  """
  Records Developer finding feedback on a specific ReviewFinding
  """
  finding=db.query(ReviewFinding).filter(ReviewFinding.id == finding_id).first()
  if not finding:
    raise ValueError(f"ReviewFinding with ID {finding_id} not found.")

  feedback =DeveloperFeedback(
    finding_id=finding_id,
    is_useful=is_useful,
    reason=reason,
    comment=comment
  )
  db.add(feedback)
  db.commit()
  db.refresh(feedback)
  return feedback

def get_repository_feedback_stats(repo_id:int,db:Session)->Dict[str,Any]:
  """
  Calculates aggregated accuracy and developer satisfaction metrics for a repo:
     - Total feedback items
     - Useful count vs False Positive count
     - Precision rate (%)=(Useful/Total)*100
  """
  repo=db.query(Repository).filter(Repository.id == repo_id).first()
  if not repo:
    raise ValueError(f"Repository with ID {repo_id} not found.")

  feedbacks=(
    db.query(DeveloperFeedback)
    .join(ReviewFinding,DeveloperFeedback)
  )

  