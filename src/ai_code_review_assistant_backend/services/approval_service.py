import datetime
from typing import List,Dict,Any,Optional
from sqlalchemy.orm import Session
from ai_code_review_assistant_backend.db.models import WriteAction,ReviewFinding



def get_pending_actions(db:Session)->List[Dict[str,Any]]:
  """
  Fetch all staged actions awaiting for human review
  """
  pending =(
    db.query(WriteAction,ReviewFinding)
    .outerjoin(ReviewFinding,WriteAction.finding_id == ReviewFinding.id)
    .filter(WriteAction.status == 'PENDING_APPROVAL')
    .order_by(WriteAction.created_at.desc())
    .all()
  )

  results=[]
  for action,finding in pending:
    results.append({
      "id": action.id,
            "finding_id": action.finding_id,
            "action_type": action.action_type,
            "payload": action.payload,
            "status": action.status,
            "created_at": action.created_at,
            "file_path": finding.file_path if finding else None,
            "line_number": finding.line_number if finding else None,
            "finding_title": finding.title if finding else None,
            "severity": finding.severity if finding else None,
    })

  return results

def resolve_write_action(action_id:int,decision:str,resolved_by:str,db:Session,comment:Optional[str]=None)->WriteAction:
  """
  It resolves a staged writeAction from PENDING_APPROVAL to APPROVED OR REJECTED.
  makesure that already resolved actions cannot be modified
  """ 

  if decision not in ('APPROVED','REJECTED'):
    raise ValueError(f"Invalid decision '{decision}'. Must be 'APPROVED' or 'REJECTED'.")

  action=db.query(WriteAction).filter(WriteAction.id == action_id).first()

  if not action:
    raise ValueError(f"WriteAction with ID {action_id} not found.")

  if action.status !='PENDING_APPROVAL':
    raise ValueError(
            f"Action {action_id} has already been resolved with status '{action.status}' by {action.resolved_by}."
        )

  #Apply resolution
  action.status =decision
  action.resolved_by =resolved_by
  action.resolved_at =datetime.datetime.now()

  db.commit()
  db.refresh(action)
  return action

