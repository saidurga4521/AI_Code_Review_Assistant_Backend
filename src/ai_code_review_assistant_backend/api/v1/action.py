from typing import List
from fastapi import APIRouter,HTTPException,status,Depends
from sqlalchemy.orm import Session

from ai_code_review_assistant_backend.schemas.action import PendingActionDetailResponse,ActionResponse,ActionResolveRequest
from ai_code_review_assistant_backend.db.session import get_db
from ai_code_review_assistant_backend.services.approval_service import get_pending_actions,resolve_write_action
from ai_code_review_assistant_backend.db.models import WriteAction

router=APIRouter(
  prefix='/actions',
  tags=['Human-in-the-Loop-Actions']
)

#1.GET /actions/pending - List all the actions awating for human review
@router.get('/pending',response_model=List[PendingActionDetailResponse])
def list_pending_actions(db:Session = Depends(get_db)):
  """
  List all staged write actions currently awaiting for human review
  Includes the target file_path,line number,finding title and severity.
  """
  return get_pending_actions(db=db)

#2.POST /actions/{action_id}/approve - Approve the staged action
@router.post('/{action_id}/approve',response_model=ActionResponse)
def approve_action(action_id:int,request:ActionResolveRequest,db:Session=Depends(get_db)):
  """
  Approved a staged code change
  Records who approved it (resolved_by) amd the approval timestamp.
  """
  try:
    updated_action=resolve_write_action(
      action_id=action_id,
      decision='APPROVED',
      resolved_by=request.resolved_by,
      db=db,
      comment=request.comment
    )
    return updated_action
  except Exception as e:
     error_msg = str(e)
     if "not found" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

# 3.POST /actions/{action_id}/reject - Reject a staged action
@router.post("/{action_id}/reject", response_model=ActionResponse)
def reject_action(
    action_id: int,
    request: ActionResolveRequest,
    db: Session = Depends(get_db)
):
    """
    Reject a staged code change.
    Prevents the patch from ever being applied.
    """
    try:
        updated_action = resolve_write_action(
            action_id=action_id,
            decision="REJECTED",
            resolved_by=request.resolved_by,
            db=db,
            comment=request.comment
        )
        return updated_action
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

 #4.GET /action/{action_id} - View single action details
@router.get('/{action_id}',response_model=ActionResponse)
def get_action_detail(action_id:int,db:Session =Depends(get_db)):
   """
   Retreive the current status and details of a specific write action
   """

   action=db.query(WriteAction).filter(WriteAction.id == action_id).first()
   if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WriteAction with ID {action_id} not found."
        )
   return action


  