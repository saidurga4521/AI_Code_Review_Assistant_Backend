#hmac ->hash based message authentication code 
#hashlib ->hashlib provides hashing algorithms
#urllib->It is used for fetch the http requests
import hmac
import hashlib
import json
import urllib.request
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import APIRouter,Request,HTTPException,status,Depends,Header

from ai_code_review_assistant_backend.db.session import get_db
from ai_code_review_assistant_backend.config import settings
from ai_code_review_assistant_backend.db.models import Repository
from ai_code_review_assistant_backend.services.review_service import review_pull_request

router=APIRouter(
  prefix='/webhooks',
  tags=['Github Webhooks']
)

def verify_github_signature(payload_bytes:bytes,signature_header:Optional[str],secret:Optional[str])->bool:
  """
  Verifies that the request came from Github using HMAC-SHA256.
  """
  if not secret:
    # In Local development without a configured secret,allow testing
    return True
  if not signature_header or not signature_header.startswith('sha256='):
    return False

  expected_signature='sha256='+hmac.new(
    key=secret.encode('utf-8'),
    msg=payload_bytes,
    digestmod=hashlib.sha256
  ).hexdigest() # convert the result in hexadecimal string

  return hmac.compare_digest(expected_signature,signature_header)


@router.post('/github')
async def github_webhook_handler(
  request:Request,
  x_hub_signature_256:Optional[str]=Header(None,alias='X-Hub-Signature-256'),
  x_github_event:Optional[str]=Header(None,alias='X-GitHub-Event'),
  db:Session=Depends(get_db)
):
  """
  Webhook receiver for Github events
  """

  #1.Read the raw request body
  raw_body=await request.body()

  if not verify_github_signature(raw_body,x_hub_signature_256,settings.GITHUB_WEBHOOK_SECRET):
    raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing GitHub webhook signature (X-Hub-Signature-256)."
        )

  #2.Handle Github handshake 'ping' event
  if x_github_event == 'ping':
    return {
            "status": "ok",
            "message": "GitHub Webhook handshake successful!"
        }

  #3.Only process 'pull_request' and 'push' events
  if x_github_event not in ('pull_request','push'):
    return {
      'status':'ignored',
      'message':f"Event {x_github_event} received but not processes.Listening only for pull_request and push"
    }

  #4.Parse JSON payload
  try:
    payload=json.loads(raw_body.decode('utf-8'))
  except json.JSONDecodeError:
    raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload."
        )
  repo_data=payload.get('repository',{})
  repo_full_name=repo_data.get('full_name') or repo_data.get('name')
  clone_url =repo_data.get('clone_url')

  #case-A:Pull Request Event
  if x_github_event == 'pull_request':
    action=payload.get('action')
    if action not in ('opened','synchronize','reopened'):
      return {
          "status": "ignored",
          "message": f"PR action '{action}' does not require an automated review."
      }
    pr_data=payload.get('pull_request',{})
    pr_number=pr_data.get('number')
    commit_sha=pr_data.get('head',{}).get('sha')
    diff_url=pr_data.get('diff_url')

  #case-B:Handling the push events
  else:
    if payload.get('deleted'):
      return {
        'status':"ignored",
        'message':'Branch deletion push ignored'
      }

    pr_number=None
    commit_sha=payload.get('after')
    compare_url=payload.get('compare')
    diff_url=f"{compare_url}.diff" if compare_url else None


  # find repository in our database
  repo = None
  # Priority 1: Match by unique Git clone_url (if provided)
  if clone_url:
    repo = db.query(Repository).filter(Repository.clone_url == clone_url).first()
  # Priority 2: Match by full name ("owner/repo") or short name
  if not repo and repo_full_name:
    repo = db.query(Repository).filter(
      (Repository.name == repo_full_name) | (Repository.name == repo_data.get("name"))
    ).first()

  if not repo:
    raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository '{repo_full_name}' has not been registered in the database."
            )

  #6.Fetch or extract git diff
  diff_text=payload.get('diff_text')
  if not diff_text and diff_url:
    try:
      req=urllib.request.Request(
        diff_url,
        headers={'User-Agent':'AI-Code-Review-Assistant/1.0'}
      )
      with urllib.request.urlopen(req,timeout=10) as response:
        diff_text=response.read().decode('utf-8',errors='replace')
    except Exception as e:
           raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch diff from GitHub ({diff_url}): {str(e)}"
            )

  if not diff_text:
    return {
      "status": "skipped",
      "message": "No diff content found to review."
    }

  #7.Execute automated AI Review
  review_result=review_pull_request(
    repo_id=repo.id,
    diff_text=diff_text,
    db=db,
    pr_number=pr_number,
    commit_sha=commit_sha
  )

  return {
    "status": "reviewed",
    "repository": repo.name,
    "pr_number": pr_number,
    "commit_sha": commit_sha,
    "review_id": review_result["review_id"],
    "risk_level": review_result["risk_level"],
    "summary": review_result["summary"],
    "findings_count": review_result["findings_count"]
  }

  




